import os
import sys
import re
import layoutparser as lp
import json
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, KeepInFrame
from reportlab.platypus.flowables import TopPadder
from transformers import pipeline
import textwrap
from tqdm import tqdm
import torch
import deepl

# constants
DPI = 72
default_font_name = "HeiseiKakuGo-W5"
pdfmetrics.registerFont(UnicodeCIDFont(default_font_name))


def get_deepl_auth_key(auth_key=None):
    if auth_key is not None:
        return auth_key
    return os.getenv("DEEPL_AUTH_KEY")


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


def save_layout_json(layouts, json_path):
    with open(json_path, "w") as f:
        json.dump([l.to_dict() for l in layouts], f, indent=2)


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


def translate_text(layouts, local=False, auth_key=None):
    if local:
        return translate_text_by_local_model(layouts)
    else:
        return translate_text_by_deepl_api(layouts, auth_key)


def translate_text_by_local_model(layouts):
    device = 0 if torch.cuda.is_available() else -1
    translator = pipeline(
        "translation",
        model="facebook/nllb-200-distilled-600M",
        src_lang="eng_Latn",
        tgt_lang="jpn_Jpan",
        device=device,
    )

    for layout in tqdm(layouts, desc="Page", file=sys.stderr):
        for block in tqdm(
            layout, desc="Paragraph in Page", leave=False, file=sys.stderr
        ):
            ja_text = translator(textwrap.wrap(block.text, 1000), max_length=1000)
            block.text = "".join(t["translation_text"] for t in ja_text)

    return layouts


def main_character_count(input_pdf):
    layouts = extract_paragrah_layouts(input_pdf)
    blocks = [block for layout in layouts for block in layout]
    print(sum(len(b.text) for b in blocks))


def main_api_usage(auth_key=None):
    translator = deepl.Translator(get_deepl_auth_key(auth_key))
    print_deepl_api_usage(translator)


def print_deepl_api_usage(translator):
    usage = translator.get_usage()
    if usage.any_limit_reached:
        print("Translation limit reached.", file=sys.stderr)
    if usage.character.valid:
        print(
            f"Character usage: {usage.character.count} of {usage.character.limit}",
            file=sys.stderr,
        )


def translate_text_by_deepl_api(layouts, auth_key=None):
    translator = deepl.Translator(get_deepl_auth_key(auth_key))
    blocks = [block for layout in layouts for block in layout]
    result = translator.translate_text(
        [b.text for b in blocks], target_lang="JA", formality="more"
    )
    for block, r in zip(blocks, result):
        block.text = r.text
    return layouts


def main_translate_text(input_json, local=False, auth_key=None):
    layouts = load_layout_json(input_json)
    layouts = translate_text(layouts, local, auth_key)
    print(json.dumps([l.to_dict() for l in layouts], indent=2))


def prepare_fonts():
    fonts_dir = Path("fonts")
    if not fonts_dir.exists():
        return []

    fonts = []
    for fonts_ttf in fonts_dir.glob("*.ttf"):
        pdfmetrics.registerFont(TTFont(fonts_ttf.stem, fonts_ttf))
        fonts.append(fonts_ttf.stem)

    return fonts


def merge_pdf(input_pdf, layouts):
    fonts = prepare_fonts()
    if len(fonts) > 0:
        font_name = fonts[0]
    else:
        font_name = default_font_name

    mask_stream = BytesIO()
    mask_canvas = Canvas(mask_stream, bottomup=1)
    mask_canvas.setFont(font_name, 20)
    default_style = ParagraphStyle(
        name="Normal",
        fontName=font_name,
        fontSize=20,
        leading=20,
        firstLineIndent=20,
    )

    for layout in layouts:
        mask_canvas.setPageSize((layout.page_data["width"], layout.page_data["height"]))
        mask_canvas.setFillColorRGB(1, 1, 1)
        for block_idx, block in enumerate(layout):
            block = block.pad(5, 5, 0, 0)
            mask_canvas.rect(
                block.coordinates[0],
                layout.page_data["height"] - block.coordinates[3],
                block.width,
                block.height,
                fill=1,
                stroke=0,
            )

            paragraph = Paragraph(block.text, default_style)
            frame = Frame(
                block.coordinates[0],
                layout.page_data["height"] - block.coordinates[3],
                block.width,
                block.height,
                leftPadding=0,
                rightPadding=0,
                topPadding=0,
                bottomPadding=0,
            )
            frame.add(
                KeepInFrame(
                    block.width * 1.5,
                    block.height * 1.5,
                    [paragraph],
                ),
                mask_canvas,
            )

        mask_canvas.showPage()

    mask_canvas.save()
    mask_stream.seek(0)
    mask_pdf = PdfReader(mask_stream)

    src_pdf = PdfReader(input_pdf)
    src_pdf2 = PdfReader(input_pdf)
    ja_pdf = PdfWriter()
    al_pdf = PdfWriter()

    # merge
    for pdf_page, orig_page, mask_page in zip(
        src_pdf.pages, src_pdf2.pages, mask_pdf.pages
    ):
        al_pdf.add_page(orig_page)
        pdf_page.merge_page(mask_page)
        al_pdf.add_page(pdf_page)
        ja_pdf.add_page(pdf_page)

    input_pdf = Path(input_pdf)
    ja_pdf.write(input_pdf.with_name(f"{input_pdf.stem}_ja.pdf"))
    al_pdf.write(input_pdf.with_name(f"{input_pdf.stem}_al.pdf"))

    al_pdf.insert_blank_page(
        layouts[0].page_data["width"],
        layouts[0].page_data["height"],
    )
    al_pdf.write(input_pdf.with_name(f"{input_pdf.stem}_pr.pdf"))


def main_merge_pdf(input_pdf, input_json):
    merge_pdf(input_pdf, load_layout_json(input_json))


def parse_translate_merge(
    input_pdf,
    local=False,
    auth_key=None,
    keep_auxiliary=False,
):
    input_path = Path(input_pdf)
    layouts = extract_paragrah_layouts(input_pdf)
    if keep_auxiliary:
        save_layout_json(
            layouts,
            input_path.with_name(f"{input_path.stem}_layout_en.json"),
        )
    layouts = translate_text(layouts, local, auth_key)
    if keep_auxiliary:
        save_layout_json(
            layouts,
            input_path.with_name(f"{input_path.stem}_layout_ja.json"),
        )
    merge_pdf(input_pdf, layouts)
