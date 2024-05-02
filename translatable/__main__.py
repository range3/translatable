import argparse
import translatable as tr

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
    translate_parser.add_argument(
        "-j",
        "--json",
        type=str,
        help="input layout JSON file.",
        required=True,
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

    all_parser = subparsers.add_parser(
        "all", help="parse, translate, and merge"
    )
    all_parser.add_argument(
        "-p",
        "--pdf",
        type=str,
        help="input PDF file.",
        required=True,
    )

    args = parser.parse_args()

    if args.command == "parse":
        tr.parse_pdf(args.pdf)
    elif args.command == "to_deepl":
        tr.to_deepl_format(args.json)
    elif args.command == "from_deepl":
        tr.from_deepl_format(args.text, args.json)
    elif args.command == "translate":
        tr.main_translate_text(args.json)
    elif args.command == "merge":
        tr.merge_pdf(args.pdf, args.json)
    elif args.command == "all":
        tr.parse_translate_merge(args.pdf)


if __name__ == "__main__":
    main()
