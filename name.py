#!/usr/bin/env python

from __future__ import annotations
import sys
import os
import argparse
import re
import fnmatch
import textwrap
from pathlib import Path
from typing import Any, Sequence, Union
from dataclasses import dataclass
from enum import StrEnum


# Metadata
__app_version__ = "0.2"
__app_name__ = "NamePlate"
__app_cmd__ = "name"
__app_author__ = "Tuncay D."
__app_url__ = "https://github.com/thingsiplay/nameplate"
__app_year__ = "2026"
__app_license__ = "MIT License"


def eprint(*args: str, **kwargs: Any) -> None:
    print(*args, file=sys.stderr, **kwargs)


def strerror(error: BaseException, default: str | None = None) -> str:
    err_str = getattr(error, "strerror", None)
    if err_str:
        return err_str
    elif default is not None:
        return default
    else:
        return str(error)


class ActionType(StrEnum):
    APPEND = "append"
    PREPEND = "prepend"
    REPLACED = "replace"
    CASE = "case"


class Status(StrEnum):
    RENAMED = "renamed"
    SKIPPED = "skipped"
    FAILED = "failed"
    UNCHANGED = "unchanged"


class CaseModeStylized(StrEnum):
    LOWER = "lower"
    UPPER = "UPPER"
    TITLE = "Title"
    CAPITALIZE = "Capitalize"


class CaseMode(StrEnum):
    LOWER = CaseModeStylized.LOWER.lower()
    UPPER = CaseModeStylized.UPPER.lower()
    TITLE = CaseModeStylized.TITLE.lower()
    CAPITALIZE = CaseModeStylized.CAPITALIZE.lower()


class FontStyle(StrEnum):
    CLEAR = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    URL = "\033[4m"
    BLINK = "\033[5m"
    BLINK2 = "\033[6m"
    SELECTED = "\033[7m"


class FontBackgroundColor(StrEnum):
    BLACK = "\33[40m"
    RED = "\33[41m"
    GREEN = "\33[42m"
    YELLOW = "\33[43m"
    BLUE = "\33[44m"
    VIOLET = "\33[45m"
    BEIGE = "\33[46m"
    WHITE = "\33[47m"
    GREY = "\33[100m"
    RED2 = "\33[101m"
    GREEN2 = "\33[102m"
    YELLOW2 = "\33[103m"
    BLUE2 = "\33[104m"
    VIOLET2 = "\33[105m"
    BEIGE2 = "\33[106m"
    WHITE2 = "\33[107m"


class FontColor(StrEnum):
    BLACK = "\33[30m"
    RED = "\33[31m"
    GREEN = "\33[32m"
    YELLOW = "\33[33m"
    BLUE = "\33[34m"
    VIOLET = "\33[35m"
    BEIGE = "\33[36m"
    WHITE = "\33[37m"
    GREY = "\33[90m"
    RED2 = "\33[91m"
    GREEN2 = "\33[92m"
    YELLOW2 = "\33[93m"
    BLUE2 = "\33[94m"
    VIOLET2 = "\33[95m"
    BEIGE2 = "\33[96m"
    WHITE2 = "\33[97m"


def term_supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


@dataclass
class FilenameOperation:
    action_type: ActionType | None
    value: str | CaseMode
    replace: str | None
    apply_all: bool
    if_missing: bool


# This class is called at invoke time for options to manipulate filenames.
# The purpose is to preserve the order of user invoked options. The attribute
# "filename_ops" can later be read and used in a loop.
class BaseFilenameAction(argparse.Action):
    def __init__(
        self,
        action_type: ActionType | None,
        apply_all: bool,
        if_missing: bool,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.action_type = action_type
        self.apply_all = apply_all
        self.if_missing = if_missing
        super().__init__(*args, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Union[str, Sequence[Any], None],
        option_string: str | None = None,
    ) -> None:
        if not hasattr(namespace, "filename_ops"):
            namespace.filename_ops = []

        if isinstance(values, (list, tuple)):
            if len(values) == 0:
                raise argparse.ArgumentTypeError("No value provided")
            value = values[0]
        elif isinstance(values, str):
            value = values
        elif values is None:
            raise argparse.ArgumentTypeError(f"No value provided for {option_string}")
        else:
            value = str(values)

        match self.action_type:
            case ActionType.REPLACED:
                try:
                    value, replace = value.rsplit("/", 1)
                except ValueError:
                    replace = ""
            case ActionType.CASE:
                value = CaseMode(value)
                replace = None
            case _:
                replace = None

        if not value:
            raise ValueError("search pattern or add text must be not empty")

        op = FilenameOperation(
            action_type=self.action_type,
            value=value,
            replace=replace,
            apply_all=self.apply_all,
            if_missing=self.if_missing,
        )
        namespace.filename_ops.append(op)


def case(source: str, mode: CaseMode) -> str:
    match mode:
        case CaseMode.LOWER:
            return source.lower()
        case CaseMode.UPPER:
            return source.upper()
        case CaseMode.TITLE:
            return source.title()
        case CaseMode.CAPITALIZE:
            return source.capitalize()
        case _:
            return source


# Replace matching pattern part with replace text in source text.
# By default only first match is replaced.
# Ignore case or turn regex support for pattern.
def replace(
    source: str,
    pattern: str,
    replace: str,
    apply_all: bool,
    extended_regexp: bool,
    glob: bool,
    ignore_case: bool,
) -> str:
    use_regex_engine = extended_regexp or glob or ignore_case
    if not use_regex_engine:
        count = -1 if apply_all else 1
        return source.replace(pattern, replace, count=count)

    flags = re.NOFLAG
    if ignore_case:
        flags |= re.IGNORECASE

    if glob:
        pattern = fnmatch.translate(pattern)
        # There is an issue with anchors. For some reason the pattern
        # doesn't work with the anchor "\z" that is automatically added
        # by fnmatch. Stripping them away seems to work.
        if pattern.startswith("^"):
            pattern = pattern[1:]
        if pattern.startswith(r"\a"):
            pattern = pattern[2:]
        if pattern.endswith("$"):
            pattern = pattern[:-1]
        if pattern.endswith(r"\z"):
            pattern = pattern[:-2]
    elif not extended_regexp:
        pattern = re.escape(pattern)

    count = 0 if apply_all else 1
    return re.sub(pattern, replace, source, count=count, flags=flags)


def print_status(
    source: Path,
    target: Path,
    quiet: bool,
    verbose: bool,
    status: Status | None = None,
    reason: str | None = None,
) -> None:

    # default: FAILED, RENAMED, SKIPPED
    # FAILED = always
    # RENAMED = hide when quiet
    # SKIPPED = hide when quiet, but force show with verbose
    # UNCHANGED = show when verbose, but force hide with quiet
    should_print = False
    if status == Status.FAILED:
        should_print = True
    elif status == Status.RENAMED:
        if not quiet:
            should_print = True
    elif status == Status.SKIPPED:
        if verbose:
            should_print = True
        elif not quiet:
            should_print = True
    elif status == Status.UNCHANGED:
        if verbose and not quiet:
            should_print = True

    if not should_print:
        return

    q = "'"
    sep = "->"
    message = f"{q}{source.as_posix()}{q} {sep} {q}{target.as_posix()}{q}"
    if status:
        message = f"{status}: {message}"
    if reason:
        message = f"{message} ({reason})"
    print(message)


def stdin_lines() -> list[str]:
    lines: list[str] = []
    for line in sys.stdin.readlines():
        if line:
            lines.extend(line.split("\n"))
    return [line for line in lines if not line == ""]


def argument_parser(args: list[str] | None = None) -> argparse.ArgumentParser:

    clear = ""
    # Header
    h = ""
    # Comment
    c = ""
    if term_supports_color():
        clear = FontStyle.CLEAR
        h = FontStyle.BOLD
        c = FontStyle.ITALIC
    p = f"{__app_cmd__}"

    class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def __init__(self, *args: Any, **kwargs: Any):
            kwargs.setdefault("max_help_position", 30)
            super().__init__(*args, **kwargs)

    epilog = textwrap.dedent(f"""
        {h}Default behavior{clear}
        * File extension including dot is ignored and preserved, unless -x or -X.
        * Existing files and directories cannot be overwritten, unless --force.
        * Use -- to separate options from filenames that start with hyphen.
        * Use single dash "-" to read newline separated list of files from stdin.

        {h}PATTERN/REPLACEMENT syntax{clear}
        * Both parts are delimited by "/".
        * If REPLACEMENT is empty "" or the delimiter is omitted, then matches will
            be deleted from filename.
        * With regex enabled (-E), use \\1, \\2 etc. in REPLACEMENT to insert
            captured groups by "()".
        * PATTERN that match everything, or result in empty parts will be ignored.
  
        {h}Status messages{clear}
        Default output: renamed, skipped, failed
        * renamed: Changes applied successfully. Hidden by --quiet.
        * unchanged: No change needed. Show with --verbose; unless --quiet.
        * skipped: Change spotted but not applied. Hidden by --quiet; unless --verbose.
        * failed: Operation error. Always shown.

        {h}Examples{clear}
        Below examples use options -n (--dry-run) and -v (--verbose), plus a set of
        fixed filenames for safe demonstration.

          {c}# Preview files without applying changes (useful to test glob patterns).{clear}
          {p} -nv -- *[hH]*

          {c}# A single dash "-" instructs to read filenames from stdin.{clear}
          echo 'File1.html\\nFile2.css' | {p} -nv -- - notes.txt

          {c}# Add any text to the end of all filenames.{clear}
          {p} -nv --append _v2 -- notes.txt

          {c}# Add output from arbitrary shell commands (here current date) to all files.{clear}
          {p} -nv --append "-$(date --iso-8601)" -- notes.txt

          {c}# Convert to uppercase, then add ".bak" after extension on all files.{clear}
          {p} -nv --with-extension -c upper -a .bak -- ../files/nearest.png

          {c}# Make sure to add "scanlines-" only if its not already there.{clear}
          {p} -nv --prepend-missing scanlines- -- scanlines-fract.slangp Modern.slangp

          {c}# Replace Roman numerals in their correct order. (naive and incomplete example){clear}
          {p} -nv -r" III/ 3" -r" II/ 2" -r" IV/ 4" -r" I/ 1" -- "Dragon Quest I & II.png"

          {c}# With glob: Remove everything after and including " (".{clear}
          {p} -nv -G --replace " (*" -- "Final Fantasy III (USA) (Rev 1).png"

          {c}# With regex: Add space before uppercase letters, but not after an underscore.{clear}
          {p} -nv -E --replace-all '(\\B(?<!_)[A-Z])/ \\1' -- "ActRaiser_ReDone v1.0.png"

        Copyright © {__app_year__} {__app_author__} ({__app_license__})
        {__app_url__} 
    """)

    parser = argparse.ArgumentParser(
        formatter_class=CustomHelpFormatter,
        description=(
            f"{__app_name__}: Rename files and directories by transforming their basename"
        ),
        epilog=(epilog),
    )

    parser.add_argument(
        "files",
        default=[],
        nargs="*",
        type=Path,
        help=('files or folders to process, use "-" to read from stdin'),
    )

    parser.add_argument(
        "--version", default=False, action="store_true", help="print version and exit"
    )

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help=("overwrite existing target files and directories"),
    )

    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        default=False,
        help=("simulate operations without modifying the filesystem"),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help=("also show files with no changes"),
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help=("suppress renamed and skipped status messages"),
    )

    scope_group = parser.add_argument_group("scope")

    extension_mode_group = scope_group.add_mutually_exclusive_group()

    extension_mode_group.add_argument(
        "-x",
        "--with-extension",
        action="store_true",
        default=False,
        help="modify entire filename plus extension",
    )

    extension_mode_group.add_argument(
        "-X",
        "--extension-only",
        action="store_true",
        default=False,
        help="modify file extension only (including last dot)",
    )

    action_group = parser.add_argument_group("action (applied in the order given)")

    action_group.add_argument(
        "-a",
        "--append",
        action=BaseFilenameAction,
        action_type=ActionType.APPEND,
        apply_all=False,
        if_missing=False,
        nargs=1,
        default=None,
        metavar="TEXT",
        help=("append TEXT to end of name"),
    )

    action_group.add_argument(
        "-A",
        "--append-missing",
        action=BaseFilenameAction,
        action_type=ActionType.APPEND,
        apply_all=False,
        if_missing=True,
        nargs=1,
        default=None,
        metavar="TEXT",
        help=("append TEXT only if not already present"),
    )

    action_group.add_argument(
        "-p",
        "--prepend",
        action=BaseFilenameAction,
        action_type=ActionType.PREPEND,
        apply_all=False,
        if_missing=False,
        nargs=1,
        default=None,
        metavar="TEXT",
        help=("prepend TEXT to start of name"),
    )

    action_group.add_argument(
        "-P",
        "--prepend-missing",
        action=BaseFilenameAction,
        action_type=ActionType.PREPEND,
        apply_all=False,
        if_missing=True,
        nargs=1,
        default=None,
        metavar="TEXT",
        help=("prepend TEXT only if not already present"),
    )

    action_group.add_argument(
        "-r",
        "--replace",
        action=BaseFilenameAction,
        action_type=ActionType.REPLACED,
        apply_all=False,
        if_missing=False,
        nargs=1,
        default=None,
        metavar="PATTERN/REPLACEMENT",
        help=("replace first PATTERN match with REPLACEMENT"),
    )

    action_group.add_argument(
        "-R",
        "--replace-all",
        action=BaseFilenameAction,
        action_type=ActionType.REPLACED,
        apply_all=True,
        if_missing=False,
        nargs=1,
        default=None,
        metavar="PATTERN/REPLACEMENT",
        help=("replace all PATTERN matches with REPLACEMENT"),
    )

    action_group.add_argument(
        "-c",
        "--case",
        action=BaseFilenameAction,
        action_type=ActionType.CASE,
        apply_all=True,
        if_missing=False,
        nargs=1,
        choices=list(CaseMode),
        default=None,
        metavar="MODE",
        help=(f"transform case to: {', '.join(list(CaseModeStylized))}"),
    )

    matching_group = parser.add_argument_group("matching")

    pattern_mode_group = matching_group.add_mutually_exclusive_group()

    pattern_mode_group.add_argument(
        "-E",
        "--extended-regexp",
        action="store_true",
        default=False,
        help=("enable regular expressions for PATTERN"),
    )

    pattern_mode_group.add_argument(
        "-G",
        "--glob",
        action="store_true",
        default=False,
        help=("enable shell like wildcard globbing for PATTERN"),
    )

    matching_group.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        default=False,
        help=("enable case insensitive comparison for PATTERN"),
    )

    return parser


def main(args: list[str] | None = None) -> int:
    app_arguments: argparse.Namespace

    if not args and not sys.argv[1:]:
        eprint("Error: No files and options provided. Use --help to show description.")
        argument_parser().print_usage(sys.stderr)
        return 1

    app_arguments = argument_parser(args).parse_args()

    if app_arguments.version:
        print(f"{__app_name__} v{__app_version__}")
        return 0

    # Remove single dash "-" and combine input_files from arguments and stdin
    # when necessary.
    input_files: list[Path] = []
    single_dash_found: bool = False
    for file in app_arguments.files:
        if not single_dash_found and file == Path("-"):
            single_dash_found = True
            # Only attempt reading from stdin, if its connected through pipes.
            if not sys.stdin.isatty():
                input_files.extend([Path(line) for line in stdin_lines()])
        else:
            input_files.append(file)

    # Apply all changes and create a new list of processd_files.
    #
    # processed_files accumulats [original_source, updated_target] paths as a
    # pair for each file from input.
    processed_files: list[tuple[Path, Path]] = []
    operations: list[Any] = getattr(app_arguments, "filename_ops", [])
    changes_to_apply: str | None = None
    for original_source in input_files:
        updated_target = original_source

        for op in operations:
            if app_arguments.extension_only:
                old_part = updated_target.suffix
                update_func = updated_target.with_suffix
                # Edge case if user does not provide a leading dot. It would
                # fail to append, if there is no dot at end of filename, so we
                # need to add one ourselves.
                if not old_part.startswith(".") and not op.value.startswith("."):
                    old_part += "."
            elif app_arguments.with_extension:
                old_part = updated_target.name
                update_func = updated_target.with_name
            else:
                old_part = updated_target.stem
                update_func = updated_target.with_stem

            changes_to_apply = None
            match op.action_type:
                case ActionType.APPEND:
                    if not op.if_missing or (not old_part.endswith(op.value)):
                        changes_to_apply = old_part + op.value
                case ActionType.PREPEND:
                    if not op.if_missing or (not old_part.startswith(op.value)):
                        changes_to_apply = op.value + old_part
                case ActionType.REPLACED:
                    changes_to_apply = replace(
                        source=old_part,
                        pattern=op.value,
                        replace=op.replace or "",
                        apply_all=op.apply_all,
                        extended_regexp=app_arguments.extended_regexp,
                        glob=app_arguments.glob,
                        ignore_case=app_arguments.ignore_case,
                    )
                case ActionType.CASE:
                    changes_to_apply = case(source=old_part, mode=op.value)
                case _:
                    raise ValueError(f"Unknown action type: {op.action_type}")

            if changes_to_apply:
                updated_target = update_func(changes_to_apply)

        processed_files.append((original_source, updated_target))

    # Execute rename command on filesystem and determine what status messages to
    # print.
    quiet = app_arguments.quiet
    verbose = app_arguments.verbose
    status: Status = Status.UNCHANGED
    for source, target in processed_files:
        if operations:
            if source == target:
                if app_arguments.verbose:
                    status = Status.UNCHANGED
                    reason = None
                    print_status(source, target, quiet, verbose, status, reason)
                continue
            elif not app_arguments.force and target.exists():
                status = Status.SKIPPED
                reason = "target exists; use -f to overwrite"
                print_status(source, target, quiet, verbose, status, reason)
            else:
                status = Status.RENAMED
                reason = None

                try:
                    if not app_arguments.dry_run:
                        # Note on how Pythons Path.replace(target) operates:
                        # Existing files and empty directory as target will be
                        # replaced. Relative paths are interpreted as working
                        # directory, not from original source.
                        after_renamed = source.replace(target)
                        target = after_renamed
                except NotADirectoryError:
                    status = Status.FAILED
                    reason = "type mismatch; target is a file"
                except IsADirectoryError:
                    status = Status.FAILED
                    reason = "type mismatch; target is a directory"
                except PermissionError as error:
                    status = Status.FAILED
                    reason = strerror(error, default="permission denied")
                except OSError as error:
                    status = Status.FAILED
                    if not source.exists():
                        reason = "source file does not exist"
                    elif target.is_dir() and list(target.iterdir()):
                        reason = "cannot rename to non-empty target directory"
                    else:
                        reason = strerror(error)

                print_status(source, target, quiet, verbose, status, reason)

        elif app_arguments.verbose:
            print(source.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
