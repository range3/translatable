# install
```console
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install layoutparser torchvision wheel numpy cython pillow==9.5.0
pip install --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git@v0.6#egg=detectron2'
pip install "layoutparser[layoutmodels]"
```
