from typing import Dict, Any, List
import math
import re

# Simplified local heuristic functions (can be swapped with real LLM integrations)

def tokenize(text: str) -> List[str]:
    return [t for t in re.split(r'\W+', text.lower()) if t]

STOP = set(['the','and','for','with','this','that','from','into','between','sobre','para','como','del','las','los'])

def mmr_summary(sentences: List[str], target=160) -> str:
    if not sentences:
        return ''
    # simple truncation fallback
    out = []
    total = 0
    for s in sentences:
        words = s.split()
        if total + len(words) > target:
            break
        out.append(s)
        total += len(words)
        if total >= target:
            break
    return ' '.join(out)


def build_sentences(df) -> List[str]:
    sents = []
    for _, r in df.head(60).iterrows():
        desc = (r.get('Study Description','') or '')
        if desc:
            parts = re.split(r'(?<=[.!?])\s+', desc)
            for p in parts:
                p = p.strip()
                if 40 < len(p) < 400:
                    sents.append(p)
    return sents

def title_heuristic(filters: Dict[str, List[str]]) -> str:
    org = ','.join(filters.get('organism', [])[:2]) or 'Estudios'
    proj = ','.join(filters.get('project_type', [])[:2])
    parts = [org]
    if proj:
        parts.append(proj)
    return ' - '.join(parts)


def generate_title_and_description(ranked_df, filters) -> Dict[str, Any]:
    title = title_heuristic(filters)
    sentences = build_sentences(ranked_df)
    desc = mmr_summary(sentences)
    return {
        'title': title,
        'description': desc,
        'meta': {
            'mode': 'heuristico',
            'fallback_chain': [],
            'final_source': 'heuristic',
            'llm_used': False
        }
    }
