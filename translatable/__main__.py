import argparse
import re
import layoutparser as lp
import json

# constants
DPI = 72


def load_model():
    return lp.Detectron2LayoutModel(
        "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
        extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.7],
        label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    )


def coalesce_nearby_textblock(layout: lp.Layout, threshold=0.8):
    blocks = [layout[0]]
    for block in layout[1:]:
        if 0 < block.coordinates[0] - blocks[-1].coordinates[2] < threshold:
            blocks[-1] = blocks[-1].union(block)
            blocks[-1].text += block.text
        else:
            blocks.append(block)
    return lp.Layout(blocks)


def extract_paragrah_layouts(pdf_path, dpi=DPI, model=load_model()):
    pdf_layouts, pdf_images = lp.load_pdf(pdf_path, load_images=True, dpi=DPI)

    paragraph_layouts = []
    for page_layout, page_image in zip(pdf_layouts, pdf_images):
        model_layout = model.detect(page_image)
        model_layout = lp.Layout(
            [b for b in model_layout if b.type in ["Text", "List"]]
        )

        blocks = []
        for block in model_layout:
            word_blocks = page_layout.filter_by(block, center=True)
            word_blocks = coalesce_nearby_textblock(word_blocks)
            block.text = " ".join(word_blocks.get_texts())
            blocks.append(block)

        width = page_image.width
        blocks = sorted(
            blocks, key=lambda x: (x.coordinates[0] // (width / 4), x.coordinates[1])
        )

        paragraph_layouts.append(lp.Layout(blocks, page_data=page_layout.page_data))

    return paragraph_layouts

def from_list_of_dict(lod):
    return [
        lp.Layout(
            [lp.TextBlock.from_dict(b) for b in d["blocks"]], page_data=d["page_data"]
        )
        for d in lod
    ]

def load_layout_json(json_path):
    with open(json_path) as f:
        return from_list_of_dict(json.load(f))

def parse_pdf(input_pdf):
    layouts = extract_paragrah_layouts(input_pdf)
    print(json.dumps([l.to_dict() for l in layouts], indent=2))


def to_deepl_format(input_json):
    with open(input_json) as f:
        json_data = json.load(f)

    for page in json_data:
        for block in page["blocks"]:
            print(block["text"])
        print("-" * 30)


def from_deepl_format(input_text, input_json):
    with open(input_text) as f:
        text = f.read()
    page_text = re.split(r"-{8,}\r?\n", text)
    page_text = [re.split(r"\r?\n", t.strip()) for t in page_text]

    layouts = load_layout_json(input_json)

    for layout, paragraphs in zip(layouts, page_text):
        for block, paragraph in zip(layout, paragraphs):
            block.text = paragraph

    print(json.dumps([l.to_dict() for l in layouts], indent=2))

def merge_pdf(input_pdf, input_json):
    layouts = load_layout_json(input_json)


def main():
    parser = argparse.ArgumentParser(description="Translatable")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="sub-command"
    )

    parse_parser = subparsers.add_parser(
        "parse", help="parse PDF file, extract layout and text as JSON"
    )
    parse_parser.add_argument(
        "-p",
        "--pdf",
        type=str,
        help="input PDF file.",
        required=True,
    )

    to_deepl_parser = subparsers.add_parser(
        "to_deepl", help="convert JSON to DeepL-compatible format"
    )
    to_deepl_parser.add_argument(
        "-j",
        "--json",
        type=str,
        help="input layout JSON file.",
        required=True,
    )

    from_deepl_parser = subparsers.add_parser(
        "from_deepl", help="convert DeepL-compatible format to JSON"
    )
    from_deepl_parser.add_argument(
        "-j",
        "--json",
        type=str,
        help="input layout JSON file.",
        required=True,
    )
    from_deepl_parser.add_argument(
        "-t",
        "--text",
        type=str,
        help="input text file.",
        required=True,
    )

    translate_parser = subparsers.add_parser(
        "translate", help="translate text locally without DeepL"
    )
    merge_parser = subparsers.add_parser(
        "merge", help="merge translated text back to PDF"
    )
    merge_parser.add_argument(
        "-j",
        "--json",
        type=str,
        help="input translated layout JSON file.",
        required=True,
    )
    merge_parser.add_argument(
        "-p",
        "--pdf",
        type=str,
        help="input PDF file.",
        required=True,
    )

    args = parser.parse_args()

    if args.command == "parse":
        parse_pdf(args.pdf)
    elif args.command == "to_deepl":
        to_deepl_format(args.json)
    elif args.command == "from_deepl":
        from_deepl_format(args.text, args.json)
    elif args.command == "translate":
        print("翻訳処理を実行")
    elif args.command == "merge":
        merge_pdf(args.pdf, args.json)


if __name__ == "__main__":
    main()
