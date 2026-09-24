# NamePlate

Rename files and directories by transforming their basename

- Author [Tuncay D.](https://github.com/thingsiplay)
- Source: [Github](https://github.com/thingsiplay/nameplate)
- License [MIT](LICENSE)

## What is NamePlate?

A commandline tool written in Python to change filenames in bulk. Affects only
basename without touching parent directories. Therefore files cannot be moved
to other directories. By default the file extension after last dot is protected
as well. This command is meant to be supplementary to `mv` on Linux.

```bash
name --append "_v2" -- *.py

name --glob --replace " (*" -- *.sfc
```

### Features

- ignore file extension by default (can be changed)
- fixed strings by default, supports glob pattern and regular expressions
- append, prepend and replace operations
- simple case transform to lower, UPPER, Title or Capitalize

## Installation

Program is written in Python 3.14 on Linux. No other Python module is required,
but no other environment is tested either. Manual installation: download
script, rename script, make it executable, put it into a directory that
is in your $PATH.

```bash
git clone https://github.com/thingsiplay/nameplate
cd nameplate
mv name.py name
# The path below is just a suggestion. This depends on your system.
install --verbose -t ~/.local/bin/ name
```

## Examples

Below examples use options -n (--dry-run) and -v (--verbose), plus a set of
fixed filenames for safe demonstration. Use option -h (--help) to list all
available options.

```bash
# Preview files without applying changes (useful to test glob patterns).
$ name -nv -- *[hH]*
History.dat
find.sh
```

```bash
# A single dash "-" instructs to read filenames from stdin.
$ echo 'File1.html\nFile2.css' | name -nv -- - notes.txt
File1.html
File2.css
notes.txt
```

```bash
# Add any text to the end of all filenames.
$ name -nv --append _v2 -- notes.txt
renamed: 'notes.txt' -> 'notes_v2.txt'
```

```bash
# Add output from arbitrary shell commands (here current date) to all files.
$ name -nv --append "-$(date --iso-8601)" -- notes.txt
renamed: 'notes.txt' -> 'notes-2026-09-23.txt'
```

```bash
# Convert to uppercase, then add ".bak" after extension on all files.
$ name -nv --with-extension -c upper -a .bak -- ../files/nearest.png
renamed: '../files/nearest.png' -> '../files/NEAREST.PNG.bak'
```

```bash
# Make sure to add "scanlines-" only if its not already there.
$ name -nv --prepend-missing scanlines- -- scanlines-fract.slangp Modern.slangp
unchanged: 'scanlines-fract.slangp' -> 'scanlines-fract.slangp'
renamed: 'Modern.slangp' -> 'scanlines-Modern.slangp'
```

```bash
# Replace Roman numerals in their correct order. (naive and incomplete example)
$ name -nv -r" III/ 3" -r" II/ 2" -r" IV/ 4" -r" I/ 1" -- "Dragon Quest I & II.png"
renamed: 'Dragon Quest I & II.png' -> 'Dragon Quest 1 & 2.png'
```

```bash
# With glob: Remove everything after and including " (".
$ name -nv -G --replace " (*" -- "Final Fantasy III (USA) (Rev 1).png"
renamed: 'Final Fantasy III (USA) (Rev 1).png' -> 'Final Fantasy III.png'
```

```bash
# With regex: Add space before uppercase letters, but not after an underscore.
$ name -nv -E --replace-all '(\B(?<!_)[A-Z])/ \1' -- "ActRaiser_ReDone v1.0.png"
renamed: 'ActRaiser_ReDone v1.0.png' -> 'Act Raiser_Re Done v1.0.png'
```
