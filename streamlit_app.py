import os
import time
import requests
import streamlit as st
from typing import List, Dict, Any
import pandas as pd

# Configuración inicial Streamlit
st.set_page_config(page_title="NASA Studies Search Demo", layout="wide")

st.title("🔎 NASA Studies / PMC Demo Search")

# --------------------------------------------------
# Config sección de conexión
# --------------------------------------------------
def get_default_api_base():
    # Permite sobrescribir vía variable de entorno API_BASE
    return os.environ.get("API_BASE", "http://localhost:8000")

api_base = st.sidebar.text_input("API Base URL", value=get_default_api_base(), help="Incluye protocolo. Ej: http://localhost:8000 o https://<ngrok>.ngrok-free.app")

# Endpoint
search_endpoint = f"{api_base.rstrip('/')}/studies/search"
facets_endpoint = f"{api_base.rstrip('/')}/facets"
health_endpoint = f"{api_base.rstrip('/')}/health"
study_detail_base = f"{api_base.rstrip('/')}/studies"  # /studies/{id}

# --------------------------------------------------
# Utilidades de caché
# --------------------------------------------------
@st.cache_data(ttl=60)
def fetch_facets() -> Dict[str, Any]:
    try:
        r = requests.get(facets_endpoint, timeout=10)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {"organism": [], "project_type": []}

@st.cache_data(ttl=30)
def fetch_health() -> Dict[str, Any]:
    try:
        r = requests.get(health_endpoint, timeout=5)
        if r.ok:
            return r.json()
    except Exception:
        pass
    return {}

# --------------------------------------------------
# Sidebar filtros
# --------------------------------------------------
health = fetch_health()
with st.sidebar.expander("Health API", expanded=False):
    if health:
        st.json(health)
    else:
        st.warning("No se pudo obtener /health")

facets = fetch_facets()
organisms = facets.get('organism', [])
project_types = facets.get('project_type', [])

st.sidebar.markdown("### Filtros")
sel_organisms = st.sidebar.multiselect("Organism", options=organisms)
sel_projects = st.sidebar.multiselect("Project Type", options=project_types)
keywords_input = st.sidebar.text_input("Keywords (separar por coma)")
keywords_list = [k.strip() for k in keywords_input.split(',') if k.strip()]

q_mode = st.sidebar.selectbox("Modo Query (q_mode)", options=["and", "or"], index=0)
q_min_match = st.sidebar.number_input("q_min_match (opcional)", min_value=0, step=1, value=0)
page_size = st.sidebar.slider("Page Size", 5, 100, 20, step=5)
show_compact = st.sidebar.checkbox("Compact (sin full records)", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("Limpiar caché de datos"):
    fetch_facets.clear()
    fetch_health.clear()
    st.toast("Caché limpiada", icon="✅")

# --------------------------------------------------
# Entrada de búsqueda en vivo
# --------------------------------------------------
q = st.text_input("Busqueda libre (q)", value="", placeholder="Escribe para buscar en título y descripción...")

# Debounce manual: usar un pequeño delay antes de disparar la llamada si el usuario sigue escribiendo
# Aquí simplificado: cada cambio de q dispara.

# --------------------------------------------------
# Función para consultar API
# --------------------------------------------------
@st.cache_data(show_spinner=False, ttl=15)
def run_search(payload: Dict[str, Any]):
    t0 = time.time()
    try:
        r = requests.post(search_endpoint, json=payload, timeout=30)
        latency = time.time() - t0
        if r.ok:
            return r.json(), latency, None
        return None, latency, f"HTTP {r.status_code}"
    except Exception as e:
        return None, 0.0, str(e)

# Construcción del payload
filters_payload = {
    "organism": sel_organisms,
    "project_type": sel_projects,
    "keywords": keywords_list,
    "q": q or None,
    "q_mode": q_mode,
    "q_min_match": (int(q_min_match) if q_min_match > 0 else None),
    "page": 1,
    "page_size": page_size,
    "mode": "heuristico",
    "emerging_topics_n": 5,
    "compact": show_compact
}

# Trigger de búsqueda (auto al cambiar q / filtros)
with st.spinner("Buscando..."):
    data, latency, error = run_search(filters_payload)

col_header = st.container()
with col_header:
    left, mid, right = st.columns([1,1,1])
    with left:
        st.metric("Query Latency (s)", f"{latency:.2f}")
    with mid:
        total = data.get('counts', {}).get('total_studies') if data else 0
        st.metric("Resultados", total)
    with right:
        if data:
            cache_hit = data.get('debug', {}).get('cache_hit')
            st.metric("Cache Hit", "Sí" if cache_hit else "No")

if error:
    st.error(f"Error en búsqueda: {error}")
elif not data:
    st.warning("Sin datos devueltos.")
else:
    # --------------------------------------------------
    # Resumen heurístico
    # --------------------------------------------------
    gen = data.get('generated', {}) or {}
    heur_title = gen.get('title') or 'Título heurístico no disponible'
    heur_desc = gen.get('description') or ''
    st.markdown("## 🧠 Resumen heurístico")
    st.markdown(f"**{heur_title}**")
    if heur_desc:
        short = heur_desc[:350]
        if len(heur_desc) > 350:
            st.write(short + '...')
            with st.expander("Ver descripción completa generada"):
                st.write(heur_desc)
        else:
            st.write(heur_desc)
    else:
        st.caption("(No se generó descripción heurística)")

    # Suggested keywords
    sug = []
    if not show_compact:
        sug = data.get('data', {}).get('suggested_keywords', [])
    else:
        fs = data.get('topics', {}).get('frequent_subset', [])
        sug = [d.get('token') for d in fs]
    with st.expander("Suggested Keywords", expanded=False):
        if sug:
            st.write(', '.join(sug))
        else:
            st.write("No disponibles.")

    # Emerging topics
    with st.expander("Emerging Topics", expanded=False):
        em = data.get('topics', {}).get('emerging', [])
        if em:
            for t in em:
                st.markdown(f"**{t['topic']}** (subset {t['subset_occurrences']} / global {t['global_occurrences']})")
        else:
            st.write("N/A")

    # Important articles
    st.markdown("### ⭐ Top (important)")
    important = data.get('articles', {}).get('important', [])
    if not important:
        st.write("Sin resultados.")
    else:
        for idx, art in enumerate(important):
            with st.container():
                st.markdown(f"**{art['title']}**  ")
                meta_line = f"ID: `{art['id']}` | Score: {art['rank_score']:.3f} | {art.get('organism')} | {art.get('project_type')}"
                if art.get('release_date'):
                    meta_line += f" | Fecha: {str(art['release_date'])[:10]}"
                if art.get('DOI'):
                    meta_line += f" | DOI: {art['DOI']}"
                st.caption(meta_line)
                if art.get('url'):
                    st.write(f"[Link]({art['url']})")
                # Botón para seleccionar detalle
                if st.button("Ver detalle", key=f"detail_btn_imp_{art['id']}_{idx}"):
                    st.session_state['selected_study_id'] = art['id']
                st.divider()

    # Página de resultados
    st.markdown("### 📄 Página de resultados")
    page_items = data.get('articles', {}).get('page_items', [])
    if page_items:
        table_rows = []
        for art in page_items:
            table_rows.append({
                'id': art['id'],
                'title': art['title'],
                'score': round(art['rank_score'],3),
                'organism': art.get('organism'),
                'project_type': art.get('project_type'),
                'date': (str(art.get('release_date'))[:10] if art.get('release_date') else None),
                'DOI': art.get('DOI')
            })
        st.dataframe(pd.DataFrame(table_rows))
        # Selector de detalle basado en page_items
        ids_available = [r['id'] for r in page_items]
        st.markdown("#### Detalle de un estudio")
        default_id = st.session_state.get('selected_study_id') if 'selected_study_id' in st.session_state else None
        default_index = 0
        if default_id and default_id in ids_available:
            default_index = ids_available.index(default_id) + 1
        sel_id = st.selectbox("Selecciona un ID para ver el detalle", options=["(ninguno)"] + ids_available, index=default_index)
        if sel_id != "(ninguno)":
            st.session_state['selected_study_id'] = sel_id
    else:
        st.info("No hay page_items en esta página.")

    # Vista detallada usando endpoint individual
    def fetch_study_detail(study_id: str, base: str):
        if not study_id:
            return None, "Sin ID"
        url = f"{base.rstrip('/')}/{study_id}"
        try:
            r = requests.get(url, timeout=20)
            if r.ok:
                return r.json(), None
            return None, f"HTTP {r.status_code}"
        except Exception as e:
            return None, str(e)

    detail_id = st.session_state.get('selected_study_id')
    if detail_id:
        st.markdown("---")
        st.markdown(f"## 🔍 Detalle del estudio `{detail_id}`")
        detail_data, detail_err = fetch_study_detail(detail_id, study_detail_base)
        if detail_err:
            st.error(f"No se pudo obtener detalle: {detail_err}")
        elif not detail_data:
            st.warning("Respuesta vacía del endpoint de detalle.")
        else:
            title_field = detail_data.get('Study Title') or detail_data.get('study_title')
            project_label = detail_data.get('project_label') or detail_data.get('project_type')
            organism_label = detail_data.get('organism_label') or detail_data.get('organism')
            if title_field:
                st.markdown(f"### {title_field}")

            # Layout de metadatos en columnas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**Organism**")
                st.write(organism_label or '—')
                st.markdown("**Project Type**")
                st.write(project_label or '—')
                st.markdown("**Release Date**")
                rd = detail_data.get('release_date')
                st.write(str(rd)[:10] if rd else '—')
            with col2:
                if project_label != 'pmc':
                    st.markdown("**Flight Program**")
                    st.write(detail_data.get('Flight Program') or detail_data.get('flight_program') or '—')
                    st.markdown("**Mission**")
                    st.write(detail_data.get('Mission') or detail_data.get('mission_name') or '—')
                    st.markdown("**Assay Type**")
                    st.write(detail_data.get('Study Assay Technology Type') or detail_data.get('assay_type') or '—')
                else:
                    st.markdown("**PMID**")
                    st.write(detail_data.get('pmid') or '—')
                    st.markdown("**PMC**")
                    st.write(detail_data.get('pmc') or '—')
                    st.markdown("**Cited By**")
                    st.write(detail_data.get('cited_by') if detail_data.get('cited_by') is not None else '—')
            with col3:
                if project_label != 'pmc':
                    st.markdown("**Assay Platform**")
                    st.write(detail_data.get('Study Assay Technology Platform') or detail_data.get('assay_platform') or '—')
                    # Reemplazar Factors (muchos null) por Accession / Identifiers si existen
                    acc = detail_data.get('Accession') or detail_data.get('accession')
                    ident = detail_data.get('Identifiers') or detail_data.get('identifiers')
                    st.markdown("**Accession / Identifiers**")
                    st.write(acc or ident or '—')
                    st.markdown("**DOI**")
                    st.write(detail_data.get('DOI') or detail_data.get('doi') or '—')
                else:
                    st.markdown("**DOI**")
                    st.write(detail_data.get('DOI') or detail_data.get('doi') or '—')
                    st.markdown("**Figura IDs**")
                    figs = detail_data.get('fig_ids')
                    if figs:
                        st.write(', '.join(figs) if isinstance(figs, list) else figs)
                    else:
                        st.write('—')
                    st.markdown("**URL**")
                    st.write(detail_data.get('url') or '—')

            # Identificadores
            id_cols = []
            for label, key in [('Accession','Accession'), ('PMID','pmid'), ('PMC','pmc'), ('ID Interno', 'Study Identifier')]:
                val = detail_data.get(key)
                if val:
                    id_cols.append(f"**{label}:** {val}")
            if id_cols:
                st.markdown(' | '.join(id_cols))

            # Enlaces
            if detail_data.get('url'):
                st.markdown(f"[Enlace principal]({detail_data['url']})")

            # Para PMC: mostrar Abstract y Conclusions por separado si existen
            if project_label == 'pmc':
                abstract_raw = detail_data.get('abstract_raw') or detail_data.get('abstract')
                conclusions_raw = detail_data.get('conclusions_raw') or detail_data.get('conclusions')
                if abstract_raw:
                    with st.expander("📄 Abstract"):
                        st.write(abstract_raw)
                if conclusions_raw:
                    with st.expander("🔚 Conclusions"):
                        st.write(conclusions_raw)

            # Descripción combinada (genérica) si existe
            desc_field = detail_data.get('Study Description') or detail_data.get('study_description')
            if desc_field:
                with st.expander("🧾 Descripción completa (combinada)"):
                    st.write(desc_field)

            # Extra PMC ya se mostraron arriba; para ODR se puede añadir factores si existieran
            if project_label != 'pmc':
                factors = detail_data.get('Study Factor Name') or detail_data.get('factors')
                if factors:
                    st.markdown(f"**Factors:** {factors}")

            # Rank score si está presente
            if 'rank_score' in detail_data:
                st.caption(f"Rank Score: {detail_data['rank_score']}")

            # JSON completo
            with st.expander("🧪 JSON completo"):
                st.json(detail_data)

    # Full records opcional
    if not show_compact:
        with st.expander("Full Records (studies_full)", expanded=False):
            fr = data.get('data', {}).get('studies_full', [])
            if fr:
                max_show = min(50, len(fr))
                st.write(f"Mostrando {max_show} de {len(fr)} registros")
                st.dataframe(pd.DataFrame(fr[:max_show]))
            else:
                st.write("Vacío o modo compacto.")

st.markdown("---")
st.caption("Demo Streamlit conectada a FastAPI NASA Studies. Ajusta filtros en el sidebar para refrescar.")
