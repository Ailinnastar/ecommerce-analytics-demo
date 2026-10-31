"""Run with python -m ecommerce_demo --help."""

import argparse
import csv
from pathlib import Path

from .matching import compare, positive_rate, read_products


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--rate', type=positive_rate, required=True,
                        help='Explicit HKD-to-CNY rate; sample data is synthetic')
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error('input and output must be different files')
    try:
        rows = compare(read_products(args.input), args.rate)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ['source_id', 'candidate_id', 'score', 'status', 'candidate_price_cny', 'price_gap_pct']
    with args.output.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Wrote {len(rows)} review rows to {args.output}')


if __name__ == '__main__':
    main()
