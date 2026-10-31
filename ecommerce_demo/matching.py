"""Transparent matching rules for synthetic product data."""

import argparse
import csv
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from pathlib import Path


@dataclass(frozen=True)
class Product:
    id: str
    market: str
    category: str
    size: str
    name: str
    price: Decimal
    currency: str


def positive_rate(value):
    try:
        rate = Decimal(value)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError('rate must be a decimal') from error
    if not rate.is_finite() or rate <= 0:
        raise argparse.ArgumentTypeError('rate must be finite and positive')
    return rate


def normalise(value):
    text = unicodedata.normalize('NFKC', value).casefold()
    for source, target in {'跑步': ' running ', '短裤': ' shorts ', '蓝色': ' blue ', '黑色': ' black '}.items():
        text = text.replace(source, target)
    return ' '.join(re.findall(r'\w+', text))


def read_products(path: Path):
    products = []
    ids = set()
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        required = set(Product.__dataclass_fields__)
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Missing required product columns')
        for number, row in enumerate(reader, start=2):
            if any(not isinstance(row.get(key), str) or not row[key].strip() for key in required):
                raise ValueError(f'Row {number}: required values cannot be blank')
            values = {key: row[key].strip() for key in required}
            if values['id'] in ids:
                raise ValueError(f'Row {number}: duplicate product ID')
            if {'CN': 'CNY', 'HK': 'HKD'}.get(values['market']) != values['currency']:
                raise ValueError(f'Row {number}: unsupported market/currency pair')
            try:
                values['price'] = Decimal(values['price'])
            except InvalidOperation as error:
                raise ValueError(f'Row {number}: invalid price') from error
            if not values['price'].is_finite() or values['price'] < 0:
                raise ValueError(f'Row {number}: price must be finite and non-negative')
            products.append(Product(**values))
            ids.add(values['id'])
    return products


def compare(products, rate):
    if not rate.is_finite() or rate <= 0:
        raise ValueError('rate must be finite and positive')
    results = []
    for source in (item for item in products if item.market == 'CN'):
        candidates = [item for item in products if item.market == 'HK'
                      and normalise(item.category) == normalise(source.category)
                      and normalise(item.size) == normalise(source.size)]
        ranked = sorted(((SequenceMatcher(None, normalise(source.name), normalise(item.name)).ratio(), item)
                         for item in candidates), key=lambda pair: (-pair[0], pair[1].id))
        result = dict(source_id=source.id, candidate_id='', score='', status='NO_CANDIDATE',
                      candidate_price_cny='', price_gap_pct='')
        if ranked:
            score, candidate = ranked[0]
            ambiguous = len(ranked) > 1 and score - ranked[1][0] < 0.05
            status = 'MATCH' if score >= 0.85 and not ambiguous else 'REVIEW'
            result.update(candidate_id=candidate.id, score=f'{score:.3f}', status=status)
            if status == 'MATCH':
                converted = candidate.price * rate
                result['candidate_price_cny'] = str(converted.quantize(Decimal('0.01')))
                if source.price:
                    gap = (converted / source.price - 1) * 100
                    result['price_gap_pct'] = str(gap.quantize(Decimal('0.01')))
        results.append(result)
    return results
