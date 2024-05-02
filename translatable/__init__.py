import re
import layoutparser as lp
import json
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, KeepInFrame
from reportlab.platypus.flowables import TopPadder

# constants
DPI = 72
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))


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
    mask_stream = BytesIO()
    mask_canvas = Canvas(mask_stream, bottomup=1)
    default_style = ParagraphStyle(
        name="Normal",
        fontName="HeiseiKakuGo-W5",
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
    pr_pdf = PdfWriter()

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