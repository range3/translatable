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
```bash
# GPU (docker --gpus) が使用可能の場合
# GPU (docker --gpus) if available
docker compose up gpu -d

# CPUのみの場合
# CPU only
docker compose up cpu -d
```

# Usage
初回実行時に機械学習モデルのダウンロードが行われ、コンテナ内にキャッシュされます。  
The machine learning model is downloaded and cached in the container at the first run.

```bash
# show help
docker compose exec gpu python3 -m translatable -h

# show DeepL api usage
docker compose exec gpu api_usage

# translate English PDF using DeepL API
docker compose exec gpu all -p dir/english.pdf

# translate English PDF using local translation model
docker compose exec gpu all -p dir/english.pdf --local

# Copy and paste the extracted English text into DeepL
docker compose exec gpu parse -p dir/english.pdf > dir/en.json
docker compose exec gpu to_deepl -j dir/en.json > dir/en.txt
docker compose exec gpu from_deepl -t dir/ja.txt -j dir/en.json > dir/ja.json
docker compose exec gpu merge -p dir/english.pdf -j dir/ja.json

# count characters of the given PDF
docker compose exec gpu count -p dir/english.pdf

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
