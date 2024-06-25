import argparse
import translatable as tr


def main():
    parser = argparse.ArgumentParser(prog="translatable")
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="sub-command"
    )

    count_parser = subparsers.add_parser("count", help="count characters")
    count_parser.add_argument(
        "-p",
        "--pdf",
        type=str,
        help="input PDF file.",
        required=True,
    )

    api_usage_parser = subparsers.add_parser("api_usage", help="print DeepL API usage")
    api_usage_parser.add_argument(
        "--auth-key",
        type=str,
        help="DeepL API key ( DEEPL_AUTH_KEY environ can also be specified ).",
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

    translate_parser = subparsers.add_parser("translate", help="translate text")
    translate_parser.add_argument(
        "-j",
        "--json",
        type=str,
        help="input layout JSON file.",
        required=True,
    )
    translate_parser.add_argument(
        "--local",
        help="use local translation model",
        action="store_true",
    )
    translate_parser.add_argument(
        "--auth-key",
        type=str,
        help="DeepL API key ( DEEPL_AUTH_KEY environ can also be specified ).",
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

    all_parser = subparsers.add_parser("all", help="parse, translate, then merge")
    all_parser.add_argument(
        "-p",
        "--pdf",
        type=str,
        help="input PDF file.",
        required=True,
    )
    all_parser.add_argument(
        "--local",
        help="use local translation model",
        action="store_true",
    )
    all_parser.add_argument(
        "--auth-key",
        type=str,
        help="DeepL API key ( DEEPL_AUTH_KEY environ can also be specified ).",
    )
    all_parser.add_argument(
        "--keep-auxiliary",
        action="store_true",
        help="keep auxiliary files",
    )

    args = parser.parse_args()

    if args.command == "count":
        tr.main_character_count(args.pdf)
    elif args.command == "api_usage":
        tr.main_api_usage(args.auth_key)
    elif args.command == "parse":
        tr.parse_pdf(args.pdf)
    elif args.command == "to_deepl":
        tr.to_deepl_format(args.json)
    elif args.command == "from_deepl":
        tr.from_deepl_format(args.text, args.json)
    elif args.command == "translate":
        tr.main_translate_text(args.json, args.local, args.auth_key)
    elif args.command == "merge":
        tr.main_merge_pdf(args.pdf, args.json)
    elif args.command == "all":
        tr.parse_translate_merge(
            args.pdf,
            local=args.local,
            auth_key=args.auth_key,
            keep_auxiliary=args.keep_auxiliary,
        )


if __name__ == "__main__":
    main()
