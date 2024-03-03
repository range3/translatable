import argparse
import sys
import cv2
import layoutparser as lp

def extract_text(input_pdf, output_txt):
    pdf_pages, _ = lp.load_pdf(input_pdf, load_images=True, dpi=72)
    pass


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
        # if sys.stdout.isatty():
        #     print("Error: Please redirect output to a file.", file=sys.stderr)
        #     sys.exit(1)
        extract_text(args.extract, sys.stdout)

    elif args.replace and len(args.replace) == 2:
        input_pdf, input_txt = args.replace
        output_pdf = sys.stdout if sys.stdout.isatty() else sys.stderr
        print("Error: Please redirect output to a file.", file=output_pdf)
        sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
