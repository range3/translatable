import layoutparser as lp
from pathlib import Path
import pdf2image
import numpy as np
import matplotlib.pyplot as plt


input_pdf = Path("fast24-IONIA.pdf")
DPI=72

pdf_pages, _ = lp.load_pdf(input_pdf, load_images=True, dpi=DPI)


model = lp.Detectron2LayoutModel('lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
                                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                                label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"})

# def pdf_to_image(file_path, page_num):
#     return np.asarray(pdf2image.convert_from_path(file_path, dpi = DPI)[page_num])

pdf_images = np.asarray(pdf2image.convert_from_path(input_pdf, dpi=DPI))

# for images in pdf_images:
#   plt.imshow(images)
#   plt.show()

pdf_layout = model.detect(pdf_images[1])

paragraph_blocks = [b for b in pdf_layout if b.type=='Text']
paragraph_blocks = sorted(paragraph_blocks, key=lambda x: (x.block.y_1, x.block.x_1))

def is_inside(paragraph_block, text_block):
    # Set allowable_error_pixel based on paragraph_block's width
    allowable_error_pixel = 10 if paragraph_block.width > 300 else 3

    # Check if text_block is inside paragraph_block with the allowable error margin
    return (
        text_block.block.x_1 >= paragraph_block.block.x_1 - allowable_error_pixel and
        text_block.block.y_1 >= paragraph_block.block.y_1 - allowable_error_pixel and
        text_block.block.x_2 <= paragraph_block.block.x_2 + allowable_error_pixel and
        text_block.block.y_2 <= paragraph_block.block.y_2 + allowable_error_pixel
    )

def text_blocks_to_words(text_blocks, coalesce_threshold=1):
    if len(text_blocks) == 0:
        return []
    words = [text_blocks[0].text]
    prev_x_2 = text_blocks[0].block.x_2
    for block in text_blocks[1:]:
        gap_x = block.block.x_1 - prev_x_2
        if gap_x > coalesce_threshold:
            words.append(block.text)
        else:
            words[-1] += block.text
        prev_x_2 = block.block.x_2
    return words

" ".join(text_blocks_to_words(inner_text_blocks))

pdf_images = np.asarray(pdf2image.convert_from_path(input_pdf, dpi=DPI))

for page_idx, pdf_page in enumerate(pdf_pages):
    print(page_idx)
    text_blocks = pdf_page.get_homogeneous_blocks()
    pdf_layout = model.detect(pdf_images[page_idx])
    paragraph_blocks = [b for b in pdf_layout if b.type=='Text']
    paragraph_blocks = sorted(paragraph_blocks, key=lambda x: (x.block.x_1//100, x.block.y_1//10))

    for paragraph_block in paragraph_blocks:
      inner_text_blocks = list(filter(lambda x: is_inside(paragraph_block, x), text_blocks))
      words_in_paragraph = text_blocks_to_words(inner_text_blocks)
      if len(words_in_paragraph) > 10:
        print(" ".join(words_in_paragraph))
        print("-"*30)

# sort by y_1 and x_1
paragraph_blocks = sorted(paragraph_blocks, key=lambda x: (x.block.y_1, x.block.x_1))
paragraph_blocks

class Rectangle:
    def __init__(self, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
        self.x_1 = top_left_x
        self.y_1 = top_left_y
        self.x_2 = bottom_right_x
        self.y_2 = bottom_right_y
    
    def width(self):
        return self.x_2 - self.x_1
    
    def height(self):
        return self.y_2 - self.y_1
    
    def scale(self, scale_x, scale_y):
        self.x_1 *= scale_x
        self.y_1 *= scale_y
        self.x_2 *= scale_x
        self.y_2 *= scale_y

    def __repr__(self):
        return f"Rectangle([{self.x_1}, {self.y_1}, {self.x_2}, {self.y_2}])"

# prepare the font
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
font_name = 'BIZUDGothic'
font_ttf = 'fonts/BIZUDGothic-Regular.ttf'
pdfmetrics.registerFont(TTFont(font_name, font_ttf))

import re
# replace paragraph_blocks with the translated text and generate a new pdf
input_text = Path("ionia-ja.txt")

re_split_paragraphs = re.compile(r'\n-+\n')

input_paragraphs = re_split_paragraphs.split(input_text.read_text())

def calc_fontsize(paragraph_width, paragraph_height, translated_text):
    return int(np.sqrt((paragraph_width) * (paragraph_height) / len(translated_text)))

from pypdf import PdfReader, PdfWriter
from io import BytesIO
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus.frames import Frame
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, KeepInFrame

src_pdf = PdfReader(input_pdf.open("rb"))
dst_pdf = PdfWriter()

def get_pdf_page_shape(pdf_page):
    return (pdf_page.mediabox[2], pdf_page.mediabox[3])

paragraph_idx = 0
for page_idx, pdf_page in enumerate(pdf_pages):
    pdf_image = pdf_images[page_idx]
    width, height = get_pdf_page_shape(src_pdf.pages[page_idx]) 
    pdf_page_rect = Rectangle(0, 0, width, height)
    pdf_image_rect = Rectangle(0, 0, pdf_image.shape[1], pdf_image.shape[0])

    mask_stream = BytesIO()
    mask_canvas = Canvas(mask_stream, pagesize=(pdf_page_rect.width(), pdf_page_rect.height()), bottomup=1)
    mask_canvas.setFillColorRGB(1, 1, 1)

    text_stream = BytesIO()
    text_canvas = Canvas(text_stream, pagesize=(pdf_page_rect.width(), pdf_page_rect.height()), bottomup=1)

    # print(pdf_page_rect)
    # print(pdf_image_rect)
    text_blocks = pdf_page.get_homogeneous_blocks()
    page_layout = model.detect(pdf_image)
    paragraph_blocks = [b for b in page_layout if b.type=='Text']
    paragraph_blocks = sorted(paragraph_blocks, key=lambda x: (x.block.x_1//100, x.block.y_1//10))
    for paragraph_block in paragraph_blocks:
        inner_text_blocks = list(filter(lambda x: is_inside(paragraph_block, x), text_blocks))
        words_in_paragraph = text_blocks_to_words(inner_text_blocks)
        if len(words_in_paragraph) <= 10:
            continue
        # print(words_in_paragraph)
        paragraph_rect = Rectangle(paragraph_block.block.x_1, paragraph_block.block.y_1, paragraph_block.block.x_2, paragraph_block.block.y_2)
        paragraph_rect.scale(
            pdf_page_rect.width()/pdf_image_rect.width(),
            pdf_page_rect.height()/pdf_image_rect.height())
        
        bottomup_y = pdf_page_rect.height() - paragraph_rect.y_2
        mask_canvas.rect(paragraph_rect.x_1, bottomup_y, paragraph_rect.width(), paragraph_rect.height(), fill=1, stroke=1)

        # テキストフレームの追加
        frame = Frame(paragraph_rect.x_1, bottomup_y, paragraph_rect.width(), paragraph_rect.height(),
                    showBoundary=1, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        # テキスト実態の追加
        fontsize = calc_fontsize(paragraph_rect.width(), paragraph_rect.height(), input_paragraphs[paragraph_idx])
        style = ParagraphStyle(name='Normal', fontName=font_name, fontSize=fontsize, leading=fontsize)
        paragraph = Paragraph(input_paragraphs[paragraph_idx], style)
        paragraph_idx += 1
        story = [paragraph]
        story_inframe = KeepInFrame(paragraph_rect.width() * 1.5, paragraph_rect.height() * 1.5, story)
        # frame.addFromList([story_inframe], text_canvas)
        frame.addFromList([story_inframe], mask_canvas)


    mask_canvas.save()
    mask_stream.seek(0)
    mask_pdf = PdfReader(mask_stream)

    # text_canvas.save()
    # text_stream.seek(0)
    # text_pdf = PdfReader(text_stream)
    try:
        src_pdf.pages[page_idx].merge_page(mask_pdf.pages[0])
        # src_pdf.pages[page_idx].merge_page(text_pdf.pages[0])
    except Exception as e:
        print("error: %s" % e)

    dst_pdf.add_page(src_pdf.pages[page_idx])

dst_pdf_name = input_pdf.with_name(f"{input_pdf.stem}_en.pdf")
with Path(dst_pdf_name).open("wb") as f:
    dst_pdf.write(f)
