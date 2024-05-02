# install
```console
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install layoutparser torchvision wheel numpy cython pillow==9.5.0
pip install --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git@v0.6#egg=detectron2'
pip install "layoutparser[layoutmodels]"
pip instal pypdf
pip install reportlab
pip install transformers
pip install sentencepiece
pip install sacremoses
```


# Usage
```console
(.venv) $ python -m translatable -h
usage: __main__.py [-h] {parse,to_deepl,from_deepl,translate,merge,all} ...

Translatable

positional arguments:
  {parse,to_deepl,from_deepl,translate,merge,all}
                        sub-command
    parse               parse PDF file, extract layout and text as JSON
    to_deepl            convert JSON to DeepL-compatible format
    from_deepl          convert DeepL-compatible format to JSON
    translate           translate text locally without DeepL
    merge               merge translated text back to PDF
    all                 parse, translate, and merge

options:
  -h, --help            show this help message and exit



# all in one using machine translation model locally
(.venv) $ python -m translatable all -p sample/english.pdf

# step by step
# 1. parse
(.venv) $ python -m translatable parse -p sample/english.pdf > en.json

# 2. translate (local model)
(.venv) $ python -m translatable translate -j en.json > ja.json

# 2. to_deepl (using DeepL)
(.venv) $ python -m translatable to_deepl -j en.json > en.txt

# 3. from_deepl
(.venv) $ python -m translatable from_deepl -t ja.txt -j en.json > ja.json

# 4. merge
python -m translatable merge -p sample/english.pdf -j ja.json
```
