"""Transparent heuristic field suggestions, never automatic business truth."""

import re

import pandas as pd

from .config import DETECTION_MARGIN, DETECTION_THRESHOLD
from .contracts import ColumnCandidate

SYNONYMS = {
    "date": {"date", "time", "timestamp", "period", "month", "day", "invoice date"},
    "sales": {"sales", "sale", "revenue", "turnover", "net sales", "sales amount"},
    "purchases": {"purchases", "purchase", "cost", "procurement", "expenses", "purchase amount"},
}


def detect_columns(table: pd.DataFrame) -> dict[str, list[ColumnCandidate]]:
    results = {}
    for role, words in SYNONYMS.items():
        candidates = []
        for column in table:
            name = re.sub(r"[_\W]+", " ", str(column).lower()).strip()
            sample = table[column].dropna().head(200)
            lexical = any(w == name or w in name.split() for w in words)
            evidence = []
            if role == "date":
                # Numeric identifiers and amounts are deliberately not parsed as epoch dates.
                looks_date = sample.astype(str).str.contains(r"[-/:]|[A-Za-z]", regex=True)
                if pd.api.types.is_datetime64_any_dtype(sample):
                    coverage = 1.0
                elif len(sample) and looks_date.mean() > 0.7:
                    coverage = float(
                        pd.to_datetime(sample, format="mixed", errors="coerce").notna().mean()
                    )
                else:
                    coverage = 0.0
            else:
                cleaned = sample.astype(str).str.replace(r"[$€£₹, ]", "", regex=True)
                coverage = (
                    float(pd.to_numeric(cleaned, errors="coerce").notna().mean())
                    if len(sample)
                    else 0.0
                )
            score = min(1.0, (0.6 if lexical else 0.0) + 0.4 * coverage)
            if lexical:
                evidence.append("Name matches configured terminology")
            evidence.append(f"{'Date' if role == 'date' else 'Numeric'} coverage: {coverage:.0%}")
            if role != "date" and not lexical:
                evidence.append("Numeric evidence alone does not establish business meaning")
            candidates.append(ColumnCandidate(str(column), role, round(score, 3), evidence))
        candidates.sort(key=lambda c: (-c.confidence, c.column_name))
        for candidate in candidates:
            candidate.alternatives = [c.column_name for c in candidates if c is not candidate][:3]
        results[role] = candidates
    return results


def requires_confirmation(candidates: list[ColumnCandidate]) -> bool:
    return (
        not candidates
        or candidates[0].confidence < DETECTION_THRESHOLD
        or (
            len(candidates) > 1
            and candidates[0].confidence - candidates[1].confidence < DETECTION_MARGIN
        )
    )
