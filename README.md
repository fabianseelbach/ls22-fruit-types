# LS 22 Best Fruit Types

[![Binary](https://github.com/fabianseelbach/ls22-fruit-types/actions/workflows/binary.yml/badge.svg)](https://github.com/fabianseelbach/ls22-fruit-types/actions/workflows/binary.yml)
[![Documentation Status](https://readthedocs.org/projects/ls22-fruit-types/badge/?version=latest)](https://ls22-fruit-types.readthedocs.io/?badge=latest)


Full Documentation is [here](https://ls22-fruit-types.readthedocs.io).

## Install

### Pythonic Way
You'll need at least Python 3.10.

#### MacOS/Linux

```shell
git clone https://github.com/fabianseelbach/ls22-fruit-types.git
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

#### Windows
```shell
git clone https://github.com/fabianseelbach/ls22-fruit-types.git
python -m venv env
./env/bin/activate
pip install -r requirements.txt
```

## Usage

You can set the Difficulty of your Savegame. At the moment only `normal` is supported.

### Mod-Map

Just use the ZIP-File of your Mod Map.
If you want a specific Language to be used, give it Short-Name as `--lang`.

```
get_fruittypes zip [-h] [--output OUTPUT] [--difficulty {normal}] --zip-file
                   ZIP_FP [--lang LANG]
```

### Single XML-Files

You'll have to get the `maps_fillTypes.xml` and `maps_fruitTypes.xml` from your Mod-Map.
Those typically are in the `maps`-Folder.

If you need translations, get the translation-XML-File also from your Mod-Map. 

```
get_fruittypes xml [-h] [--output OUTPUT] [--difficulty {normal}]
                   --fruit-types FRUIT_FP --fill-types FILL_FP
                   [--translation TRANSLATION_FP]
```

