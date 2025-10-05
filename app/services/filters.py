from typing import Dict, List, Any, Set
import pandas as pd

class FilterEngine:
    def __init__(self, studies_df: pd.DataFrame, id_col: str, global_token_studies):
        self.studies_df = studies_df
        self.id_col = id_col
        self.global_token_studies = global_token_studies
        self.last_stats: Dict[str,int] = {}

    @staticmethod
    def _normalize_token(t: str) -> str:
        return ''.join(c.lower() for c in t.strip() if c.isalnum() or c in ('-','_')).strip()

    def _tokens_from_text(self, q: str):
        if not q: return []
        import re
        toks = re.split(r'\W+', q.lower())
        return [self._normalize_token(tok) for tok in toks if len(tok) > 2]

    def filter_ids(self, filters: Dict[str, List[str]] | Dict[str, Any]) -> Set[str]:
        all_ids = set(self.studies_df[self.id_col].unique())
        working = all_ids.copy()
        self.last_stats = {'initial': len(working)}

        # organism
        orgs = [o for o in (filters.get('organism') or []) if o is not None]
        if orgs:
            target = {str(o).strip().lower() for o in orgs if str(o).strip()}
            candidate_cols = [c for c in ['organism_label','Organism','Organism Label','organism'] if c in self.studies_df.columns]
            collected_ids = set()
            for col in candidate_cols:
                tmp = self.studies_df[[col, self.id_col]].copy()
                tmp['__norm'] = tmp[col].astype(str).str.strip().str.lower()
                match_ids = set(tmp[tmp['__norm'].isin(target)][self.id_col])
                collected_ids |= match_ids
            if candidate_cols:
                working &= collected_ids if collected_ids else set()
            self.last_stats['after_organism'] = len(working)
            if not working:
                # debug: valores distintos disponibles
                if candidate_cols:
                    distinct_vals = []
                    for col in candidate_cols:
                        vals = list(self.studies_df[col].dropna().unique())[:40]
                        distinct_vals.extend([f"{col}::"+str(v) for v in vals])
                    self.last_stats['organism_distinct_sample'] = distinct_vals[:60]
                return working

        # project_type
        ptypes = [p for p in (filters.get('project_type') or []) if p is not None]
        if ptypes:
            targetp = {str(p).strip().lower() for p in ptypes if str(p).strip()}
            candidate_cols_pt = [c for c in ['project_label','Project Type','project_type','Project'] if c in self.studies_df.columns]
            collected_ids_pt = set()
            for col in candidate_cols_pt:
                tmp = self.studies_df[[col, self.id_col]].copy()
                tmp['__norm'] = tmp[col].astype(str).str.strip().str.lower()
                match_ids = set(tmp[tmp['__norm'].isin(targetp)][self.id_col])
                collected_ids_pt |= match_ids
            if candidate_cols_pt:
                working &= collected_ids_pt if collected_ids_pt else set()
            self.last_stats['after_project_type'] = len(working)
            if not working:
                if candidate_cols_pt:
                    distinct_vals = []
                    for col in candidate_cols_pt:
                        vals = list(self.studies_df[col].dropna().unique())[:40]
                        distinct_vals.extend([f"{col}::"+str(v) for v in vals])
                    self.last_stats['project_type_distinct_sample'] = distinct_vals[:60]
                return working

        # keywords (AND)
        sel_kws = filters.get('keywords') or []
        for kw in sel_kws:
            k = self._normalize_token(kw)
            if not k: continue
            matches = self.global_token_studies.get(k, set())
            if not matches:
                return set()
            working &= matches
            if not working: return working
        if sel_kws:
            self.last_stats['after_keywords'] = len(working)

        # free text q (configurable and/or + min match) con fallback inteligentes
        q_text = filters.get('q') or filters.get('query') or ''
        if q_text:
            original_working = working.copy()
            q_mode = (filters.get('q_mode') or 'and').lower()  # 'and' | 'or'
            terms = self._tokens_from_text(q_text)
            # Filtrar tokens que no aparezcan nunca para no matar la query entera
            existing_terms = [t for t in terms if self.global_token_studies.get(t)]
            missing_terms = [t for t in terms if t not in existing_terms]
            if missing_terms:
                self.last_stats['ignored_tokens'] = missing_terms
            # Si no queda ningún término utilizable, aplicar fallback frase directa
            executed_phrase_fallback = False
            if not existing_terms:
                phrase_ids = self._phrase_match_ids(q_text)
                working &= phrase_ids if phrase_ids else set()
                executed_phrase_fallback = True
            else:
                if q_mode == 'or':
                    term_sets = [self.global_token_studies.get(t, set()) for t in existing_terms]
                    min_match = filters.get('q_min_match') or 1
                    from collections import Counter
                    counter = Counter()
                    for tset in term_sets:
                        for sid in tset:
                            counter[sid] += 1
                    valid = {sid for sid, c in counter.items() if c >= min_match}
                    working &= valid
                else:  # AND estricto con fallback
                    for term in existing_terms:
                        matches = self.global_token_studies.get(term, set())
                        if not matches:
                            continue
                        working &= matches
                        if not working:
                            break
                    # Fallback automático: si AND devolvió vacío, intentar OR con min_match dinámico
                    if not working:
                        term_sets = [self.global_token_studies.get(t, set()) for t in existing_terms]
                        from collections import Counter
                        counter = Counter()
                        for tset in term_sets:
                            for sid in tset:
                                counter[sid] += 1
                        # min_match = ceil(50% de los términos) pero al menos 1
                        import math
                        min_match_auto = max(1, math.ceil(0.5 * len(existing_terms)))
                        fallback_valid = {sid for sid, c in counter.items() if c >= min_match_auto}
                        if fallback_valid:
                            working = original_working & fallback_valid
                            self.last_stats['fallback_or_min_match'] = min_match_auto
                        # Segundo fallback: búsqueda de frase parcial (subcadena en título/descr)
                        if not working:
                            phrase_ids = self._phrase_match_ids(q_text)
                            if phrase_ids:
                                working = original_working & phrase_ids
                                executed_phrase_fallback = True
            # Si después de todo seguimos vacíos, quizá usar similitud fuzzy en títulos
            if q_text and not working:
                fuzzy_ids = self._fuzzy_title_match_ids(q_text, top_k=25, threshold=0.72)
                if fuzzy_ids:
                    working = fuzzy_ids
                    self.last_stats['fuzzy_fallback'] = True
            self.last_stats['after_q'] = len(working)
            if executed_phrase_fallback:
                self.last_stats['phrase_fallback'] = True

        self.last_stats['final'] = len(working)
        return working

    # --- Métodos auxiliares de fallback ---
    def _phrase_match_ids(self, phrase: str) -> Set[str]:
        phrase_norm = phrase.lower().strip()
        if len(phrase_norm) < 4:
            return set()
        cols = [c for c in ['Study Title','Study Description'] if c in self.studies_df.columns]
        if not cols:
            return set()
        matched = set()
        for _, r in self.studies_df[[self.id_col] + cols].iterrows():
            for c in cols:
                val = str(r.get(c,'')).lower()
                if phrase_norm in val:
                    matched.add(r[self.id_col])
                    break
        return matched

    def _fuzzy_title_match_ids(self, text: str, top_k: int = 15, threshold: float = 0.7) -> Set[str]:
        # Implementación ligera con difflib (sin dependencias extra). Si no supera threshold no devuelve nada.
        import difflib
        candidate_pairs = []
        base = text.lower().strip()
        if len(base) < 4:
            return set()
        if 'Study Title' not in self.studies_df.columns:
            return set()
        for _, r in self.studies_df[['Study Title', self.id_col]].iterrows():
            title = str(r['Study Title']).lower()
            ratio = difflib.SequenceMatcher(None, base, title).ratio()
            if ratio >= threshold:
                candidate_pairs.append((ratio, r[self.id_col]))
        candidate_pairs.sort(reverse=True, key=lambda x: x[0])
        top = candidate_pairs[:top_k]
        return {cid for _, cid in top}
