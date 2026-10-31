# E-commerce Product Matching Demo

A standalone portfolio demonstration of product-name normalisation, cross-market matching, confidence-based review, and currency-adjusted price comparison.

**Provenance:** `lululemon_matching.py` retains the reusable collection parsing and fuzzy-scoring functions from Ailinna's original retail product matcher. The original Excel workflow, work datasets, row-layout assumptions, and client deliverables are excluded. `ecommerce_demo/` is a separate demonstration created for public portfolio use in October 2026. All included example products, prices, and exchange rates are synthetic.

## Run

Python 3.10+. The synthetic CLI uses the standard library. Install RapidFuzz to run the extracted original scorer and all tests:

```bash
python -m pip install -r requirements.txt
python -m ecommerce_demo --input examples/products.csv --output output/matches.csv --rate 0.9
python -m unittest discover -s tests -v
```

The sample converts synthetic HKD prices to CNY at an explicitly supplied demonstration rate. It is not a live exchange-rate feed.

## Workflow

The following workflow describes the **new synthetic demonstration**. The original scorer is an independent importable module using RapidFuzz, collection names, and garment hints; its scores are heuristics rather than calibrated probabilities. Similar fit names and nearby lengths can represent distinct SKUs and must be reviewed by a person. No live crawler is included: the local scraper found alongside the matcher targets Alo Yoga rather than Lululemon.

1. Validate the CSV schema, markets, identifiers, and non-negative prices.
2. Normalise text with Unicode NFKC and a small, documented bilingual synonym map.
3. Restrict candidate matches to the same category and size in the other market.
4. Rank names with Python's `difflib.SequenceMatcher`. Flag tied or weak candidates for review.
5. Export source IDs, matched IDs, scores, status, and currency-adjusted price gaps.

Matching is a review aid, not a guarantee of product equivalence. Packaging, materials, model variants, taxes, and shipping can invalidate price comparisons. This small demo does not recreate production multilingual entity resolution, live scraping, or Power BI dashboards.

## Layout

- `ecommerce_demo/`: reusable matching and CLI code
- `lululemon_matching.py`: extracted original collection parser and scoring functions
- `examples/products.csv`: entirely synthetic inputs
- `tests/`: validation, matching, ambiguity, and price-conversion checks
- `.github/workflows/checks.yml`: automated tests

## Data contract

Input columns: `id,market,category,size,name,price,currency`. Supported market/currency pairs are `CN/CNY` and `HK/HKD`. Prices must be finite, non-negative decimals. IDs must be unique. The CLI requires a finite positive HKD-to-CNY rate. Blank optional outputs indicate that no safe match or percentage comparison was available.
