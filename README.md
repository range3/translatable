# translatable
This tool translates English papers into Japanese while preserving the layout.
You can choose from the following three methods of translation.
- Using DeepL API (need API key, 500K characters/month free for now)
- Copy and paste the extracted English text into DeepL
- Use a local translation model

英語論文をレイアウトを保ったまま日本語に翻訳するツールです。
翻訳は以下の３通りの方法から選べます。
- DeepL APIを使う (APIキーが必要、現在は月間50万文字まで無料)
- DeepLに抽出した英語テキストをコピペする
- ローカルで翻訳モデルを使う

# install
Set the `.env` file to DeepL API key. Please refer to `.env.example`.  
`.env`ファイルにDeepL APIキーを設定してください。`.env.example`を参考にしてください。

```bash
# GPU (docker --gpus) if available
docker compose up gpu -d

# CPU only
docker compose up cpu -d
```

# Usage
Place the PDF file you wish to translate in the `./data` directory. This directory is bound to the `/app/data` directory in the container.  
The machine learning model is downloaded and cached in the container at the first run.  

`./data`ディレクトリに翻訳したいPDFファイルを置いてください。
このディレクトリはコンテナ内の`/app/data`ディレクトリにバインドされています。  
初回実行時に機械学習モデルのダウンロードが行われ、コンテナ内にキャッシュされます。  

```bash
cd /path/to/translatable

# set alias for easy use
alias translatable="docker compose exec gpu python3 -m translatable"

# show help
translatable -h

# show DeepL api usage
translatable api_usage

# translate English PDF using DeepL API
translatable all -p data/english.pdf

# translate English PDF using local translation model
translatable all -p data/english.pdf --local

# Copy and paste the extracted English text into DeepL
translatable parse -p data/english.pdf > data/en.json
translatable to_deepl -j data/en.json > data/en.txt
translatable from_deepl -t data/ja.txt -j data/en.json > data/ja.json
translatable merge -p data/english.pdf -j data/ja.json

# count characters of the given PDF
translatable count -p data/english.pdf

# stop the container
docker compose stop
```

# install (dev)
```console
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install "layoutparser[layoutmodels]" torchvision wheel numpy cython pillow==9.5.0 pypdf reportlab transformers sentencepiece sacremoses deepl
pip install --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git@v0.6#egg=detectron2'
```
