import unittest

from lululemon_matching import extract_product_collection, score_candidate


class OriginalMatchingTests(unittest.TestCase):
    def test_empty_names_are_not_matches(self):
        self.assertEqual(score_candidate('', 'Align leggings', ''), 0)

    def test_collection_and_exact_match(self):
        self.assertIsNotNone(extract_product_collection('Align High-Rise Pant'))
        self.assertEqual(score_candidate('Align High-Rise Pant', 'Align High-Rise Pant', ''), 100)

    def test_mismatched_collection_reduces_score(self):
        collection = extract_product_collection('Align High-Rise Pant')
        correct = score_candidate('Align High-Rise Pant', 'Align High-Rise Pant', '', collection)
        wrong = score_candidate('Align High-Rise Pant', 'Scuba High-Rise Pant', '', collection)
        self.assertGreater(correct, wrong)


if __name__ == '__main__':
    unittest.main()
