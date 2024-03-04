import argparse
import sys
import layoutparser as lp
import numpy as np
import pdf2image

# constants
DPI = 72


def is_inside(paragraph_block, text_block):
    # Set allowable_error_pixel based on paragraph_block's width
    allowable_error_pixel = 10 if paragraph_block.width > 300 else 3

    # Check if text_block is inside paragraph_block with the allowable error margin
    return (
        text_block.block.x_1 >= paragraph_block.block.x_1 - allowable_error_pixel
        and text_block.block.y_1 >= paragraph_block.block.y_1 - allowable_error_pixel
        and text_block.block.x_2 <= paragraph_block.block.x_2 + allowable_error_pixel
        and text_block.block.y_2 <= paragraph_block.block.y_2 + allowable_error_pixel
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


def extract_text(input_pdf):
    pdf_pages, _ = lp.load_pdf(input_pdf, load_images=True, dpi=DPI)
    model = lp.Detectron2LayoutModel(
        "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
        extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
        label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
    )
    pdf_images = np.asarray(pdf2image.convert_from_path(input_pdf, dpi=DPI))

    for page_idx, pdf_page in enumerate(pdf_pages):
        text_blocks = pdf_page.get_homogeneous_blocks()
        pdf_layout = model.detect(pdf_images[page_idx])
        paragraph_blocks = [b for b in pdf_layout if b.type == "Text"]
        paragraph_blocks = sorted(
            paragraph_blocks, key=lambda x: (x.block.x_1 // 100, x.block.y_1 // 10)
        )

        for paragraph_block in paragraph_blocks:
            inner_text_blocks = list(
                filter(lambda x: is_inside(paragraph_block, x), text_blocks)
            )
            words_in_paragraph = text_blocks_to_words(inner_text_blocks)
            if len(words_in_paragraph) > 10:
                print(" ".join(words_in_paragraph))
                print("-" * 30)


def replace_text(input_pdf, input_txt, output_pdf):
    pass


def main():
    parser = argparse.ArgumentParser(
        description="Translatable - A tool for extracting and replacing text in PDFs."
    )
    parser.add_argument(
        "--extract", help="Extract text from a PDF file.", type=str, metavar="input.pdf"
    )
    parser.add_argument(
        "--replace",
        nargs=2,
        help="Replace text in a PDF file using a text file.",
        metavar=("input.pdf", "input.txt"),
    )

    args = parser.parse_args()

    if args.extract:
        extract_text(args.extract)

    elif args.replace and len(args.replace) == 2:
        input_pdf, input_txt = args.replace
        output_pdf = sys.stdout if sys.stdout.isatty() else sys.stderr
        print("Error: Please redirect output to a file.", file=output_pdf)
        sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
