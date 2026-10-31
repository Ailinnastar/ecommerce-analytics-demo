"""Product collection parsing and candidate scoring extracted from the original retail matcher.

Only reusable text-scoring code is retained; no spreadsheets or original row schema.
"""
from __future__ import annotations
import re
from typing import Dict, List, Optional
from rapidfuzz import fuzz

INCH_RE = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\"")

SYNONYMS: Dict[str, List[str]] = {
    # garment cores
    "pants": ["pant", "trousers", "jogger", "joggers", "legging", "leggings", "cargo", "culotte", "wide-leg", "flare", "straight"],
    "jogger": ["joggers", "pants"],
    "shorts": ["short", "bike short", "biker short", "running short"],
    "skirt": ["skort", "tennis skirt", "court skirt"],
    "hoodie": ["zip hoodie", "pullover", "sweatshirt"],
    "sweatshirt": ["pullover", "crewneck"],
    "t-shirt": ["tee", "t shirt", "top"],
    "tank": ["vest", "bra-top", "crop tank"],
    "vest": ["gilet"],
    "jacket": ["zip jacket", "hooded jacket", "anorak", "windbreaker", "parka"],
    "dress": ["one-piece"],

    # fits & rises
    "high-rise": ["high rise", "super-high-rise", "super high rise"],
    "mid-rise": ["mid rise"],
    "low-rise": ["low rise"],

    # fabrics / techs
    "nulu": ["nulu™"],
    "rib": ["ribbed", "rib-knit"],
    "waffle": ["waffle-knit", "waffle knit"],
    "luon": ["luon™"],
    "everlux": ["everlux™"],
    "luxtreme": ["luxtreme™"],
    "rulu": ["rulu™"],

    # sports tags
    "running": ["run"],
    "tennis": ["court"],
}

CN_TO_EN_HINTS: Dict[str, str] = {
    # Additive translator for common CN tokens
    "女士": "women",
    "男士": "men",
    "高腰": "high-rise",
    "中腰": "mid-rise",
    "低腰": "low-rise",
    "喇叭": "flare",
    "阔腿": "wide-leg",
    "直筒": "straight",
    "短裤": "shorts",
    "长裤": "pants",
    "裙": "skirt",
    "连衣裙": "dress",
    "工字": "racerback",
    "背心": "tank",
    "夹克": "jacket",
    "连帽": "hooded",
    "连帽衫": "hoodie",
    "卫衣": "sweatshirt",
    "半拉链": "half-zip",
    "拉链": "zip",
    "烟囱领": "funnel-neck",
    "华夫格": "waffle",
    "罗纹": "rib",
    "防晒": "uv-protective",
    "拒水": "water-repellent",
    "防风": "windproof",
    "口袋": "pocket",
    "马甲": "vest",
    "羽绒": "down",
    "跑步": "running",
    "网球": "tennis",
    "瑜伽": "yoga",
    "亚洲版型": "asian fit",
    "常规版型": "regular fit",
}

STRONG_KEYWORDS = {
    "scuba", "define", "wunder puff", "wunder", "wunder train", "wunder under", "wundermost",
    "groove", "align", "swiftly", "fast & free", "fast and free", "energy",
    "like a cloud", "all yours", "softstreme", "ribbed nulu", "everywhere", "everywhere belt bag",
    "down for it all", "flow y", "swift", "becalm", "base pace", "speed up",
    "hotty hot", "wunder train", "invigorate", "metal vent tech", "license to train",
    "jersey training", "ebb to street", "city essentials", "dance studio", "quilty pleasures",
    "pace breaker", "big cozy", "hold tight", "glow up", "restfeel", "on my level",
    "swift speed", "sculpt", "daydrift", "enlite", "featherweight", "invisiwear",
    "underease", "love", "perfectly oversized",
}

PRODUCT_COLLECTIONS = [
    "down for it all",
    "metal vent tech",
    "perfectly oversized",
    "everywhere belt bag",  # "Everywhere" collection may also appear as "Everywhere Belt Bag"
    "license to train",
    "jersey training",
    "like a cloud",
    "ebb to street",
    "city essentials",
    "dance studio",
    "quilty pleasures",
    "wunder puff",
    "wunder train",
    "wunder under",
    "fast & free",
    "swiftly tech",
    "pace breaker",
    "all yours",
    "big cozy",
    "flow y",
    "speed up",
    "hotty hot",
    "base pace",
    "hold tight",
    "glow up",
    "restfeel",
    "on my level",
    "swift speed",
    "everywhere",
    "wunder",
    "align",
    "energy",
    "scuba",
    "define",
    "groove",
    "becalm",
    "swiftly",
    "invigorate",
    "sculpt",
    "daydrift",
    "enlite",
    "featherweight",
    "invisiwear",
    "underease",
    "wundermost",
    "love",
]

def extract_product_collection(name: str) -> Optional[str]:
    """
    Extract the product collection/line name from a product name.
    Returns None if no collection is found.
    Collections are checked in order (longest first) to handle multi-word collections.

    Handles edge cases:
    - Brand prefixes (e.g., "lululemon Align")
    - Trademark symbols (e.g., "Align™")
    - Case variations
    - "&" vs "and" variations (e.g., "Fast & Free" matches both "Fast & Free" and "Fast and Free")
    - Hyphens vs spaces (e.g., "fast-and-free" matches "Fast & Free")
    """
    if not isinstance(name, str) or not name:
        return None

    # Clean the name: remove brand prefixes, normalize whitespace
    name_lower = name.lower().strip()

    # Remove common brand prefixes
    name_lower = re.sub(r"^lululemon\s+", "", name_lower)
    name_lower = re.sub(r"\s+", " ", name_lower)  # Normalize whitespace

    # Normalize "&" to "and" for matching (both variants should match)
    # This handles "Fast & Free" vs "Fast and Free"
    name_normalized = re.sub(r"\s*&\s*", " and ", name_lower)

    # Check each collection (longest first to handle multi-word collections)
    for collection in PRODUCT_COLLECTIONS:
        # Create normalized collection pattern (handle "&" vs "and")
        collection_normalized = collection.lower()
        collection_pattern = re.sub(r"\s*&\s*", " and ", collection_normalized)

        # Match collection name as whole word/phrase
        # Handle hyphens and spaces in collection names flexibly
        # e.g., "fast and free", "like a cloud", "wunder puff"
        # Convert spaces to flexible pattern that matches spaces or hyphens
        escaped = re.escape(collection_pattern)
        # Replace escaped spaces with pattern that matches space or hyphen
        pattern = escaped.replace(r"\ ", r"[\s\-]+")
        # Ensure word boundaries at start/end (but allow hyphens)
        pattern = r"(?:^|[^\w])" + pattern + r"(?:[^\w]|$)"
        # Match against normalized name
        if re.search(pattern, name_normalized):
            # Return the original collection name (with "&" if it has it)
            return collection

    return None

def _contains_any(text: str, *terms: str) -> bool:
    low = text.lower()
    return any(t in low for t in terms if t)

def _get_inches(text: str) -> List[float]:
    vals: List[float] = []
    for m in INCH_RE.finditer(text):
        try:
            vals.append(float(m.group(1)))
        except Exception:
            pass
    return vals

def compute_domain_boosts(cn_text: str, hk_name: str) -> int:
    """Small positive boosts for domain knowledge matches."""
    score = 0
    low_cn = cn_text.lower()
    low_hk = hk_name.lower()

    # Asian Fit ↔ Regular Fit reconciliation
    cn_asian = ("亚洲版型" in cn_text) or ("asian fit" in low_cn)
    cn_regular = ("常规版型" in cn_text) or ("regular fit" in low_cn)
    hk_asian = _contains_any(low_hk, "asian fit", "asia fit")
    hk_regular = _contains_any(low_hk, "regular fit")

    if (cn_asian and hk_regular) or (cn_regular and hk_asian):
        score += 6  # treat as same model across regions

    # Sport tags
    if ("网球" in cn_text and _contains_any(low_hk, "tennis", "court")) or \
       ("跑步" in cn_text and _contains_any(low_hk, "run", "running")):
        score += 5

    # Rise hints
    if ("高腰" in cn_text and _contains_any(low_hk, "high-rise", "high rise")) or \
       ("中腰" in cn_text and _contains_any(low_hk, "mid-rise", "mid rise")) or \
       ("低腰" in cn_text and _contains_any(low_hk, "low-rise", "low rise")):
        score += 3

    # Length proximity (e.g., 23" vs 25")
    cn_inches = _get_inches(cn_text)
    hk_inches = _get_inches(hk_name)
    if cn_inches and hk_inches:
        if set(cn_inches) & set(hk_inches):
            score += 3
        else:
            # if the difference is small, still help a bit
            if any(abs(a - b) <= 2.0 for a in cn_inches for b in hk_inches):
                score += 2

    # Family keywords
    for kw in STRONG_KEYWORDS:
        if kw in low_hk:
            score += 2

    return min(12, score)  # cap boost

def score_candidate(target_phrase: str, candidate_name: str, cn_text: str, cn_collection: Optional[str] = None) -> int:
    """
    Improved scoring that considers word order, not just token sets.
    Uses multiple fuzzy matching methods and combines them.

    Args:
        target_phrase: The target product name to match against
        candidate_name: The candidate HK product name
        cn_text: Full CN text for domain boost computation
        cn_collection: CN product collection (if known) for collection matching boost
    """
    # Clean inputs
    target = target_phrase.strip().lower()
    candidate = candidate_name.strip().lower()

    if not target or not candidate:
        return 0

    # CRITICAL: Check for collection mismatch - heavily penalize
    collection_penalty = 0
    if cn_collection:
        hk_collection = extract_product_collection(candidate_name)
        if hk_collection and hk_collection != cn_collection:
            # Heavily penalize collection mismatches (should be filtered out before scoring, but safety net)
            collection_penalty = -50

    # 1. WRatio (weighted ratio) - best overall, considers order, length, character similarity
    # This is usually the most reliable
    w_ratio = fuzz.WRatio(target, candidate)

    # 2. Token sort ratio - sorts tokens alphabetically but maintains token-level order
    # Better than token_set_ratio because it considers order within the sorted tokens
    token_sort = fuzz.token_sort_ratio(target, candidate)

    # 3. Partial ratio - checks if one string is contained in another
    # Useful for cases like "Scuba Mid-Rise Wide-Leg Pant" vs "Scuba Wide-Leg Pant"
    partial = fuzz.partial_ratio(target, candidate)

    # 4. Token set ratio (original) - but lower weight since it ignores order
    token_set = fuzz.token_set_ratio(target, candidate)

    # 5. Ratio - simple character-level Levenshtein distance
    simple_ratio = fuzz.ratio(target, candidate)

    # Combine scores with weights favoring order-aware methods
    # WRatio and token_sort get highest weight
    combined = (
        w_ratio * 0.35 +           # Best overall, considers order
        token_sort * 0.25 +        # Order-aware token matching
        partial * 0.20 +           # Substring matching
        simple_ratio * 0.10 +      # Character-level similarity
        token_set * 0.10           # Fallback for set-based matching
    )

    # Add collection match boost (if collections match, give bonus)
    collection_boost = 0
    if cn_collection:
        hk_collection = extract_product_collection(candidate_name)
        if hk_collection == cn_collection:
            collection_boost = 8  # Significant boost for matching collection

    # Add domain boosts
    s = combined + \
        compute_domain_boosts(cn_text, candidate_name) + \
        collection_boost + collection_penalty

    return max(0, min(100, int(s)))
