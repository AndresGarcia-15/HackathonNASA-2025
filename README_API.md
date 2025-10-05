# NASA Studies API

Arquitectura de la API basada en FastAPI para exponer el pipeline de filtrado, ranking y generación heurística de título/descripción.

## Endpoints

- `GET /health` -> Estado y número de estudios cargados.
- `GET /facets` -> Facetas básicas (`organism`, `project_type`).
- `GET /studies` -> Payload completo filtrado y paginado.
  - Query params:
    - `organism=...&organism=...`
    - `project_type=...`
    - `keywords=...`
    - `q=texto libre`
    - `page` (default 1)
    - `page_size` (default 20, máx 200)
    - `mode=heuristico` (futuro: auto, remoto, local)
- `GET /studies/{study_id}` -> Detalle completo de un estudio.

## Ejemplo de llamada
```
/studies?organism=Plant&project_type=High%20Altitude&keywords=growth&q=root%20development&page=1&page_size=15
```

## Estructura del payload `/studies`
```
{
  "filters": {...},
  "generated": {"title": str, "description": str, "meta": {...}},
  "counts": {"total_studies": int, "important": int, "less_relevant": int},
  "articles": {"important": [...], "less_relevant": [...], "page_items": [...]},
  "topics": {"emerging": [...], "frequent_subset": [...], "by_topic_index": {...}},
  "debug": {...},
  "data": {"studies_full": [ { todos los campos originales + rank_score } ], "total_full": int },
  "exported_at": ISO8601
}
```

## Diseño Interno

- `app/services/filters.py` -> Motor de filtrado (organism, project_type, keywords, q).
- `app/services/ranking.py` -> Cálculo heurístico de `rank_score`.
- `app/services/generation.py` -> Heurísticas de título y resumen (extensible a LLM).
- `app/services/pipeline.py` -> Ensambla todo y construye el payload final.
- `app/models/payload.py` -> Esquemas Pydantic (para validación futura si se desea aplicar en responses).

## Extensiones Futuras
- Integrar LLM remoto/local en `generation.py` con caché.
- Añadir endpoint `/summarize` para resúmenes de un subconjunto.
- Añadir ordenamiento configurable (e.g. `sort=recency`).
- Cache estratificada para filtros populares.
- Modo compacto: `?compact=true` que omita `studies_full`.

## Ejecución Local
```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Notas de Rendimiento
- Pre-cómputo de índice invertido simple (`global_token_studies`) en memoria.
- Sin estado mutable: escalable horizontalmente con un warm-up inicial.
- Para conjuntos grandes: considerar serializar índice a disco (parquet / pickle) y mapearlo en arranque.

## Seguridad / Producción
- Limitar orígenes CORS en producción.
- Añadir rate limiting (e.g. slowapi) si hay exposición pública.
- Validar tamaños de `q` y número de `keywords` (actualmente sin límites estrictos).

## Licencia
Uso interno hackathon / demo.
