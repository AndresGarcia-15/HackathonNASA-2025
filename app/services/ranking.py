from typing import List, Dict, Any
import pandas as pd
import math

# Ranking heurístico similar al notebook

def rank_subset(subset: pd.DataFrame, id_col: str) -> pd.DataFrame:
    if subset.empty:
        return subset.assign(rank_score=0.0)
    df = subset.copy()
    # Score basado en longitud de título, diversidad de tokens y recencia (si hay release_date)
    import re
    def diversity(text: str) -> float:
        if not text: return 0.0
        toks = re.split(r'\W+', text.lower())
        toks = [t for t in toks if len(t)>3]
        return len(set(toks)) / max(1, len(toks))

    title_scores = df['Study Title'].fillna('').map(lambda t: min(len(t)/120, 1.0))
    desc_scores = df['Study Description'].fillna('').map(lambda d: min(len(d)/800,1.0))
    diversity_scores = df['Study Title'].fillna('').map(diversity)

    recency = None
    if 'release_date' in df.columns:
        try:
            rd = pd.to_datetime(df['release_date'], errors='coerce')
            span_days = (rd.max() - rd.min()).days if rd.notna().any() else 0
            if span_days > 0:
                recency = (rd - rd.min()).dt.days / span_days
            else:
                recency = pd.Series(0, index=df.index)
        except Exception:
            recency = pd.Series(0, index=df.index)
    else:
        recency = pd.Series(0, index=df.index)

    df['rank_score'] = (
        0.35*title_scores +
        0.25*desc_scores +
        0.25*diversity_scores +
        0.15*recency.fillna(0)
    )
    df = df.sort_values('rank_score', ascending=False)
    return df
