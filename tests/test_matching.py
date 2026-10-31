import argparse
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from ecommerce_demo.matching import compare, normalise, positive_rate, read_products


class MatchingTests(unittest.TestCase):
    def test_bilingual_normalisation(self):
        self.assertEqual(normalise('跑步 短裤 蓝色'), normalise('running shorts blue'))

    def test_fixture_matching_ambiguity_and_missing_candidates(self):
        data = read_products(Path(__file__).parents[1] / 'examples/products.csv')
        matched, ambiguous, missing = compare(data, Decimal('0.9'))
        self.assertEqual(matched['status'], 'MATCH')
        self.assertEqual(matched['candidate_price_cny'], '99.00')
        self.assertEqual(matched['price_gap_pct'], '-1.00')
        self.assertEqual(ambiguous['status'], 'REVIEW')
        self.assertEqual(ambiguous['price_gap_pct'], '')
        self.assertEqual(missing['status'], 'NO_CANDIDATE')

    def test_invalid_rates(self):
        for value in ('NaN', 'Infinity', '0', '-1', 'abc'):
            with self.subTest(value=value), self.assertRaises(argparse.ArgumentTypeError):
                positive_rate(value)

    def test_rejects_bad_inputs(self):
        header = 'id,market,category,size,name,price,currency\n'
        for rows in ('a,CN,shorts,M,demo,NaN,CNY\n', 'a,CN,shorts,M,demo,-1,CNY\n',
                     'a,CN,shorts,M,demo,10,USD\n', 'a,CN,shorts,M,,10,CNY\n',
                     'a,CN,shorts,M,demo,10,CNY\na,CN,shorts,M,demo,20,CNY\n'):
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'bad.csv'
                path.write_text(header + rows, encoding='utf-8')
                with self.assertRaises(ValueError):
                    read_products(path)


if __name__ == '__main__':
    unittest.main()
