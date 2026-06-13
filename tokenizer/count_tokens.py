import argparse

import tiktoken
from pypdf import PdfReader


# Approximate input (prompt) price in USD per 1,000,000 tokens.
# Update these as provider pricing changes.
INPUT_PRICE_PER_MILLION = {
    "gpt-3.5-turbo": 0.50,
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "gpt-4-turbo": 10.00,
    "gpt-4": 30.00,
}


def count_tokens(pdf_path: str, model: str = "gpt-3.5-turbo", show_cost: bool = False) -> None:
    reader = PdfReader(pdf_path)

    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)

    print(f"Total tokens: {len(tokens)}")
    print(f"Total words: {len(text.split())}")

    if show_cost:
        price = INPUT_PRICE_PER_MILLION.get(model)
        if price is None:
            print(f"Estimated cost: no pricing on file for model '{model}'")
        else:
            cost = len(tokens) / 1_000_000 * price
            print(f"Estimated input cost ({model} @ ${price:.2f}/1M): ${cost:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Count the number of tokens in a PDF using tiktoken."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "-m",
        "--model",
        default="gpt-3.5-turbo",
        help="Model name used to pick the tiktoken encoding (default: gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--cost",
        action="store_true",
        help="Also print the estimated input (prompt) cost for the chosen model",
    )
    args = parser.parse_args()
    count_tokens(args.pdf_path, args.model, args.cost)


if __name__ == "__main__":
    main()
