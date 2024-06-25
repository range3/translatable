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
```console
docker-compose up --build
docker-compose run --rm cli -h
```

# Usage
```console
# use DeepL API
export DEEPL_AUTH_KEY=YOUR_DEEPL_AUTH_KEY
docker-compose run -v $(pwd)/dir:/app/dir --rm cli all -p dir/english.pdf

# use local translation model
docker-compose run -v $(pwd)/dir:/app/dir --rm cli all -p dir/english.pdf --local

# Copy and paste the extracted English text into DeepL
docker-compose run -v $(pwd)/dir:/app/dir --rm cli parse -p dir/english.pdf > dir/en.json
docker-compose run -v $(pwd)/dir:/app/dir --rm cli to_deepl -j dir/en.json > dir/en.txt
docker-compose run -v $(pwd)/dir:/app/dir --rm cli from_deepl -t dir/ja.txt -j dir/en.json > dir/ja.json
docker-compose run -v $(pwd)/dir:/app/dir --rm cli merge -p dir/english.pdf -j dir/ja.json


# count characters of the given PDF
docker-compose run -v $(pwd)/dir:/app/dir --rm cli count -p dir/english.pdf

# show DeepL api usage
docker-compose run --rm cli api_usage # --auth-key or DEEPL_AUTH_KEY env is required
```

# install (dev)
```console
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install "layoutparser[layoutmodels]" torchvision wheel numpy cython pillow==9.5.0 pypdf reportlab transformers sentencepiece sacremoses deepl
pip install --no-build-isolation 'git+https://github.com/facebookresearch/detectron2.git@v0.6#egg=detectron2'
```
