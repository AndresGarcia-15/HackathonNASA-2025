# NASA Studies API

API FastAPI que expone filtrado, ranking y generación de campos derivados (título alterno, resumen compacto, términos emergentes) "a partir de contexto".

## Endpoints

- `GET /health` -> Estado y número de estudios cargados.
- `GET /facets` -> Facetas básicas (`organism`, `project_type`).
- `GET /studies` -> Payload filtrado y paginado.
  - Query params:
    - `organism=...&organism=...`
    - `project_type=...`
    - `keywords=...`
    - `q=texto libre`
    - `page` (default 1)
    - `page_size` (default 20, máx 200)
    - `mode=heuristico` (futuro: auto, remoto, local)
- `GET /studies/{study_id}` -> Detalle enriquecido.

## Ejemplo de llamada
```
/studies?organism=Plant&project_type=High%20Altitude&keywords=growth&q=root%20development&page=1&page_size=15
```

## Parámetros (GET /studies)
| Param | Tipo | Repetible | Descripción |
|-------|------|-----------|-------------|
| organism | str | sí | Uno o más organismos |
| project_type | str | no | Tipo de proyecto |
| keywords | str | sí | Palabras sueltas para filtrar |
| q | str | no | Búsqueda textual libre |
| page | int | no | Página (1 por defecto) |
| page_size | int | no | Tamaño página (<=200) |
| compact | bool | no | Si true reduce campos voluminosos |

## Cuerpo (POST /studies/search)
```json
{
  "organism": ["Plant"],
  "project_type": "High Altitude",
  "keywords": ["growth"],
  "q": "root development",
  "page": 1,
  "page_size": 15,
  "compact": false
}
```

## Estructura del payload `/studies`
```jsonc
{
  "filters": {"organism": ["Plant"], "project_type": "High Altitude", "q": "root development"},
  "generated": {"title": "Root growth under reduced gravity", "description": "Resumen compacto...", "meta": {"stage": "partial_match"}},
  "counts": {"total_studies": 124, "important": 8, "less_relevant": 32},
  "articles": {
    "important": [{"id": "STUDY123", "rank_score": 0.92, "study_title": "..."}],
    "less_relevant": [{"id": "STUDY045", "rank_score": 0.41}],
    "page_items": [{"id": "STUDY123"}, {"id": "STUDY045"}]
  },
  "topics": {"emerging": ["photomorphogenesis"], "frequent_subset": ["gravity", "root"], "by_topic_index": {}},
  "debug": {"stage": "partial", "cache_hit": false},
  "data": {"studies_full": [{"id": "STUDY123", "rank_score": 0.92, "study_description": "..."}], "total_full": 124},
  "exported_at": "2025-10-05T04:32:10Z"
}
```

## Búsqueda Escalonada
1. Coincidencia completa de todos los términos.
2. Coincidencia parcial mínima.
3. Coincidencia de frase.
4. Coincidencia aproximada.
El campo `debug.stage` indica la etapa aplicada.

## Diseño Interno

- `app/services/filters.py` -> Motor de filtrado (organism, project_type, keywords, q).
- `app/services/ranking.py` -> Cálculo heurístico de `rank_score`.
- `app/services/generation.py` -> Generación contextual (extensible a LLM externo).
- `app/services/pipeline.py` -> Ensambla todo y construye el payload final.
- `app/models/payload.py` -> Esquemas Pydantic (para validación futura si se desea aplicar en responses).

## Extensiones Futuras
- Integrar LLM remoto/local en `generation.py` con caché.
- Endpoint `/summarize`.
- Ordenamiento configurable (`sort=recency`).
- Cache estratificada para filtros populares.
- Modo compacto ya soportado: omite campos largos.

## Ejecución Local
```
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Notas de Rendimiento
- Índice ligero en memoria (`global_token_studies`).
- Escalable horizontalmente (estado reconstruible en arranque /reload).
- Para grandes volúmenes: serializar índice (parquet/pickle).

## Seguridad / Producción
- Limitar orígenes CORS.
- Proteger `/reload` (API key / token).
- Rate limiting (slowapi / proxy).
- Validar longitud de `q` y nº de `keywords`.

## Licencia
Uso interno hackathon / demo.
