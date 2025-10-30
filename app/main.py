from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Any, Dict
import pandas as pd
import os, json, glob, re, pathlib
from datetime import datetime, timezone
from .services.pipeline import PayloadBuilder

app = FastAPI(title="NASA Studies API", version="0.1.0")

# CORS (frontend domains pueden añadirse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

############################################################
# CARGA / PREPROCESAMIENTO DESDE ODR (replicar notebook)
############################################################
ID_COL = 'Study Identifier'

ORGANISM_LABELS = {
    # Map extendido: incluye variaciones de nombres de carpeta para producir etiquetas legibles
    'Human_(Homo_sapiens)': 'Human',
    'human_homo_sapiens': 'Human (Homo sapiens)',
    'Rodent': 'Rodent',
    'rodent': 'Rodent',
    'Plant': 'Plant',
    'plant': 'Plant',
    'Microbiota': 'Microbiota',
    'microbiota': 'Microbiota',
    'Bacteria': 'Bacteria',
    'bacteria': 'Bacteria',
    'Fungus': 'Fungus',
    'fungus': 'Fungus',
    'Algae': 'Algae',
    'algae': 'Algae',
    'Fish': 'Fish',
    'fish': 'Fish',
    'Snail': 'Snail',
    'snail': 'Snail',
    'Squid': 'Squid',
    'squid': 'Squid',
    'Squirrel': 'Squirrel',
    'squirrel': 'Squirrel',
    'Fruit_fly': 'Fruit Fly',
    'fruit_fly': 'Fruit Fly',
    'Worm': 'Worm',
    'worm': 'Worm',
    'Cellular_organisms': 'Cellular Organisms',
    'cellular_organisms': 'Cellular Organisms'
}

PROJECT_TYPE_MAP = {
    'ground': 'Ground',
    'Ground': 'Ground',
    'Ground Study': 'Ground',
    'high_altitude': 'High Altitude',
    'High_Altitude': 'High Altitude',
    'space_flight': 'Spaceflight',
    'spaceflight': 'Spaceflight',
    'Spaceflight Study': 'Spaceflight',
    'Space Flight': 'Spaceflight',
    'pmc': 'pmc',
    'PMC': 'pmc'
}

ODR_DIR = pathlib.Path(__file__).resolve().parent.parent / 'odr'

def _epoch_to_date(val) -> datetime | None:
    if val is None or val == '':
        return None
    try:
        # valores en segundos (ej 1721088000.0) -> fecha UTC
        f = float(val)
        if f > 10_000_000:  # heurística epoch
            return datetime.fromtimestamp(f, tz=timezone.utc)
    except Exception:
        pass
    # Intentar parseo de strings tipo 'YYYY-MM-DD' o 'MM/DD/YYYY'
    s = str(val).strip()
    for fmt in ('%Y-%m-%d','%m/%d/%Y','%m/%d/%y','%m/%d/%Y %H:%M:%S'):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None

def load_raw_odr_hits() -> pd.DataFrame:
    """Recorre odr/<organism_subdir>/*.json, extrae hits.hits[].['_source'] añadiendo organism_label y project_label.
    Replica la lógica fundamental del notebook (conversión mínima de fechas y normalizaciones).
    """
    rows: list[dict] = []
    if not ODR_DIR.exists():
        return pd.DataFrame(columns=[ID_COL])
    for org_dir in sorted([d for d in ODR_DIR.iterdir() if d.is_dir()]):
        org_key = org_dir.name  # ej 'plant', 'rodent'
        for json_path in org_dir.glob('*.json'):
            fname = json_path.stem  # ej 'space_flight'
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                hits = (data.get('hits') or {}).get('hits') or []
                for h in hits:
                    src = h.get('_source') or {}
                    r = dict(src)
                    sid = r.get(ID_COL) or r.get('Accession') or r.get('Authoritative Source URL')
                    if sid:
                        # limpiar posible sufijo '/'
                        sid = str(sid).strip().rstrip('/')
                        r[ID_COL] = sid
                    # organism label
                    key_norm = org_key.replace('-', '_')
                    org_label = ORGANISM_LABELS.get(key_norm)
                    if not org_label:
                        org_label = ORGANISM_LABELS.get(key_norm.lower()) or key_norm.replace('_', ' ').title()
                    r['organism_label'] = org_label
                    # project label desde filename si no existe mapeo interno
                    proj_label = PROJECT_TYPE_MAP.get(fname, PROJECT_TYPE_MAP.get(fname.replace('-', '_'), fname.title()))
                    # Si el _source tiene 'Project Type' preferirlo para deducir
                    pt_field = r.get('Project Type') or r.get('Project_Type')
                    if pt_field:
                        # Normalizaciones similares
                        v = str(pt_field).strip()
                        proj_label = PROJECT_TYPE_MAP.get(v, PROJECT_TYPE_MAP.get(v.replace(' ', '_'), v))
                    r['project_label'] = proj_label
                    # Título / Descripción
                    if 'Study Title' not in r:
                        r['Study Title'] = r.get('Study Publication Title')
                    # release_date a partir de 'Study Public Release Date'
                    rel_raw = r.get('Study Public Release Date') or r.get('release_date')
                    dt_val = _epoch_to_date(rel_raw)
                    r['release_date'] = dt_val.isoformat() if dt_val else None
                    rows.append(r)
            except Exception:
                continue
    if not rows:
        return pd.DataFrame(columns=[ID_COL])
    df = pd.DataFrame(rows)
    # Quitar duplicados exactos por (ID, organism_label, project_label)
    keep_cols = list(dict.fromkeys([c for c in df.columns]))
    df = df[keep_cols]
    if all(c in df.columns for c in [ID_COL,'organism_label','project_label']):
        df = df.drop_duplicates(subset=[ID_COL,'organism_label','project_label'])
    return df

def load_pmc_articles() -> pd.DataFrame:
    """Carga artículos de literatura (PMC) desde el nuevo archivo articulos_actualizado.json.
    Fallback: si no existe, intenta articles_with_citations.json (versión anterior).
    En el nuevo archivo existen campos 'doi' y 'date'. Se mapean a 'DOI' y 'release_date'.
    """
    pmc_path = ODR_DIR / 'articulos_actualizado.json'
    legacy_path = ODR_DIR / 'articles_with_citations.json'
    if not pmc_path.exists() and legacy_path.exists():
        pmc_path = legacy_path
    if not pmc_path.exists():
        return pd.DataFrame(columns=[ID_COL])
    try:
        with open(pmc_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        rows = []
        for art in data:
            pmc_id = art.get('pmc') or art.get('pmcid') or art.get('pmid')
            if not pmc_id:
                continue
            pmc_id = str(pmc_id).strip()
            title = art.get('title')
            abstract = art.get('abstract') or ''
            conclusions = art.get('conclusions') or ''
            descr_parts = [p for p in [abstract, conclusions] if p]
            # Mantener Study Description combinada (compatibilidad) pero además campos separados
            description = '\n\n'.join(descr_parts) if descr_parts else None
            pmid = art.get('pmid')
            url = None
            if art.get('pmc'):
                url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{art['pmc']}/"
            elif pmid:
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            # DOI y fecha (nuevos campos en articulos_actualizado.json)
            doi = art.get('doi') or art.get('DOI')
            date_raw = art.get('date') or art.get('release_date')
            # Parse de fecha simple (YYYY-MM-DD) + fallback a _epoch_to_date
            rdate_iso = None
            if date_raw:
                try:
                    # Intentar directamente formato ISO corto
                    from datetime import datetime
                    rdate_iso = datetime.strptime(date_raw[:10], '%Y-%m-%d').replace(tzinfo=timezone.utc).isoformat()
                except Exception:
                    dtp = _epoch_to_date(date_raw)
                    if dtp:
                        rdate_iso = dtp.isoformat()
            row = {
                ID_COL: pmc_id,
                'Study Title': title,
                'Study Description': description,
                'abstract_raw': abstract or None,
                'conclusions_raw': conclusions or None,
                'organism_label': 'Literature',  # evita asignar erróneamente un organismo biológico
                'project_label': 'pmc',
                'release_date': rdate_iso,
                'pmid': pmid,
                'pmc': art.get('pmc'),
                'cited_by': art.get('cited_by'),
                'fig_ids': art.get('fig_ids'),
                'url': url,
                'DOI': doi
            }
            rows.append(row)
        if not rows:
            return pd.DataFrame(columns=[ID_COL])
        df = pd.DataFrame(rows)
        # Quitar duplicados por identificador
        df = df.drop_duplicates(subset=[ID_COL])
        return df
    except Exception:
        return pd.DataFrame(columns=[ID_COL])

def build_studies_view(df: pd.DataFrame) -> pd.DataFrame:
    """Vista agregada por (Study Identifier, organism_label, project_label).
    El notebook unifica campos; aquí tomamos first no nulos para título/descr/fecha."""
    if df.empty:
        return pd.DataFrame(columns=[ID_COL,'organism_label','project_label','Study Title','Study Description','release_date'])
    # Garantizar columnas clave
    for col in ['organism_label','project_label','Study Title','Study Description','release_date','DOI','url']:
        if col not in df.columns:
            df[col] = None
    grp_cols = [ID_COL,'organism_label','project_label']
    def _first(series):
        for v in series:
            if pd.notna(v) and v not in ('', 'None'):
                return v
        return None
    view = df.groupby(grp_cols, dropna=False).agg({
        'Study Title': _first,
        'Study Description': _first,
        'release_date': _first,
        'DOI': _first,
        'url': _first
    }).reset_index()
    # Parse fecha a datetime
    try:
        view['release_date'] = pd.to_datetime(view['release_date'], errors='coerce')
    except Exception:
        pass
    return view

def load_studies_dataframe() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (view_df, raw_full_df)."""
    raw_df = load_raw_odr_hits()
    pmc_df = load_pmc_articles()
    if not pmc_df.empty:
        common_cols = list(dict.fromkeys(list(raw_df.columns) + list(pmc_df.columns)))
        raw_df = raw_df.reindex(columns=common_cols)
        pmc_df = pmc_df.reindex(columns=common_cols)
        raw_df = pd.concat([raw_df, pmc_df], ignore_index=True)
    view = build_studies_view(raw_df)
    return view, raw_df

_df, _raw_full_df = load_studies_dataframe()
pipeline = PayloadBuilder(_df, id_col=ID_COL)

@app.get('/health')
async def health():
    return {
        'status': 'ok',
        'studies_loaded': int(len(_df)),
        'columns': list(_df.columns),
        'source': 'odr_raw_json',
        'organisms': int(_df['organism_label'].nunique()) if 'organism_label' in _df else 0,
        'projects': int(_df['project_label'].nunique()) if 'project_label' in _df else 0,
        'features': {
            'spell_checking': True,
            'smart_q_mode': True,
            'query_expansion': True
        }
    }

@app.get('/spell-check')
async def spell_check_query(q: str):
    """
    Endpoint para probar corrección ortográfica sin hacer búsqueda completa.
    
    Ejemplo: /spell-check?q=bacterios%20in%20micrograviti
    """
    if not q or not q.strip():
        return {
            'error': 'Query parameter "q" is required',
            'example': '/spell-check?q=bacterios%20in%20micrograviti'
        }
    
    # Usar el spell checker del pipeline
    spell_checker = pipeline.filter_engine.spell_checker
    result = spell_checker.check_query(q)
    
    return {
        'query': q,
        'analysis': result,
        'suggestions_detail': [
            {
                'original': corr['original'],
                'suggestions': corr['suggestions']
            }
            for corr in result.get('corrections', [])
        ]
    }

@app.get('/facets')
async def facets():
    # Facets siempre sobre el dataset global en memoria
    orgs = sorted([o for o in _df['organism_label'].dropna().unique()]) if 'organism_label' in _df else []
    projs = sorted([p for p in _df['project_label'].dropna().unique()]) if 'project_label' in _df else []
    return {
        'organism': orgs,
        'project_type': projs,
        'counts': {
            'organism': {o: int(_df[_df['organism_label']==o][ID_COL].nunique()) for o in orgs},
            'project_type': {p: int(_df[_df['project_label']==p][ID_COL].nunique()) for p in projs}
        }
    }

@app.get('/studies')
async def get_studies(
    organism: Optional[List[str]] = Query(default=None),
    project_type: Optional[List[str]] = Query(default=None),
    keywords: Optional[List[str]] = Query(default=None),
    q: Optional[str] = None,
    q_mode: str = 'and',
    q_min_match: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    mode: str = 'heuristico',
    emerging_topics_n: int = 5,
    compact: bool = False
):
    filters: Dict[str,Any] = {
        'organism': organism or [],
        'project_type': project_type or [],
        'keywords': keywords or [],
        'q': q,
        'q_mode': q_mode,
        'q_min_match': q_min_match
    }
    payload = pipeline.build_payload(filters, page=page, page_size=page_size, mode=mode, emerging_topics_n=emerging_topics_n, compact=compact)
    return payload

@app.post('/studies/search')
async def post_studies_search(body: Dict[str,Any]):
    organism = body.get('organism') or []
    project_type = body.get('project_type') or []
    keywords = body.get('keywords') or []
    q = body.get('q')
    q_mode = body.get('q_mode','and')
    q_min_match = body.get('q_min_match')
    page = int(body.get('page',1))
    page_size = int(body.get('page_size',20))
    mode = body.get('mode','heuristico')
    emerging_topics_n = int(body.get('emerging_topics_n',5))
    compact = bool(body.get('compact', False))
    filters: Dict[str,Any] = {
        'organism': organism,
        'project_type': project_type,
        'keywords': keywords,
        'q': q,
        'q_mode': q_mode,
        'q_min_match': q_min_match
    }
    return pipeline.build_payload(filters, page=page, page_size=page_size, mode=mode, emerging_topics_n=emerging_topics_n, compact=compact)

@app.post('/reload')
async def reload_dataset():
    global _df, _raw_full_df, pipeline
    _df, _raw_full_df = load_studies_dataframe()
    pipeline = PayloadBuilder(_df, id_col=ID_COL)
    return {
        'reloaded': True,
        'studies_loaded': int(len(_df)),
        'organisms': int(_df['organism_label'].nunique()) if 'organism_label' in _df else 0,
        'raw_columns': len(_raw_full_df.columns)
    }

@app.get('/studies/{study_id}')
async def get_study_detail(study_id: str):
    # Fila agregada
    agg_row = _df[_df[ID_COL]==study_id]
    if agg_row.empty:
        return {'error': 'not_found'}
    # Fila(s) crudas (puede haber varias combinaciones). Tomamos la primera con más campos no nulos.
    raw_candidates = _raw_full_df[_raw_full_df[ID_COL]==study_id]
    raw_row = None
    if not raw_candidates.empty:
        # Heurística: escoger la fila con mayor número de valores no nulos
        raw_row = raw_candidates.iloc[raw_candidates.notna().sum(axis=1).argmax()]
    agg = agg_row.iloc[0]
    out: Dict[str, Any] = {}

    def _is_missing(v: Any) -> bool:
        """Detección segura de 'missing' evitando ambigüedad con arrays/listas.
        Considera None, NaN/NaT, strings vacíos o 'None'."""
        if v is None:
            return True
        # Evitar aplicar pd.isna a listas/dicts/tuplas/sets o ndarrays que devuelven arrays booleanos
        if isinstance(v, (list, dict, tuple, set)):
            return False
        try:
            import pandas as _pd
            if _pd.isna(v):  # scalars solamente
                return True
        except Exception:
            pass
        if isinstance(v, str) and v.strip() in ('', 'None', 'nan', 'NaN'):
            return True
        return False

    def _normalize(v: Any) -> Any:
        # Convertir timestamps a ISO, listas se dejan igual
        from datetime import datetime as _dt
        if isinstance(v, (pd.Timestamp, _dt)):
            if pd.isna(v):
                return None
            return v.tz_localize('UTC').isoformat() if isinstance(v, pd.Timestamp) and v.tzinfo is None else v.isoformat()
        return v

    # Copiar columnas agregadas con normalización
    for c in agg_row.columns:
        val = agg[c]
        val = _normalize(val)
        out[c] = None if _is_missing(val) else val

    # Mezclar columnas crudas adicionales (no sobrescribir si ya hay valor válido)
    if raw_row is not None:
        for c in raw_row.index:
            existing = out.get(c)
            if _is_missing(existing):
                val = raw_row[c]
                val = _normalize(val)
                out[c] = None if _is_missing(val) else val
    # Alias útiles para frontend
    out['study_id'] = out.get(ID_COL)
    # Normalizar organism label final
    if out.get('organism_label') is None and out.get('organism'):
        ok = str(out['organism'])
        out['organism_label'] = ORGANISM_LABELS.get(ok.lower(), ok)
    return out

# Nota: Para LLM remoto/local se añadirían endpoints /generate o /summarize, encapsulando claves API y caching.
