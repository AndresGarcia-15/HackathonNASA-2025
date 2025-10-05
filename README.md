<div align="center">

# Plataforma de Estudios y Literatura Bioespacial
**Catálogo y API unificada para explorar estudios (ODR) y artículos científicos (literatura PMC).**

</div>

## Índice Rápido
- [Visión General](#visión-general)
- [Quickstart API](#quickstart-api)
- [Endpoints](#endpoints-principales)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Campos Generados](#campos-generados)
- [Caching y Rendimiento](#caching-y-rendimiento)
- [Roadmap](#roadmap)
- [Documentación Extendida](#documentación-extendida)
- [Análisis NLP Exploratorio (Fase Original)](#análisis-nlp-exploratorio-fase-original)

## Visión General
El backend unifica múltiples archivos JSON de estudios por organismo y tipo de proyecto junto con un archivo de artículos científicos. Proporciona filtrado, búsqueda escalonada y generación de campos derivados a partir del propio contenido (títulos alternos, resúmenes compactos y términos emergentes) sin depender de un modelo externo en esta fase.

## Quickstart API
```powershell
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```
Visita: http://localhost:8000/docs

Ejemplo rápido:
```
GET /studies?organism=Plant&project_type=High%20Altitude&q=photosynthesis
```

## Endpoints Principales
| Método | Ruta | Uso |
|--------|------|-----|
| GET | /health | Estado rápido (conteos) |
| GET | /facets | Facetas (organism, project_type) |
| GET | /studies | Listado + filtros y paginación |
| POST | /studies/search | Búsqueda vía body JSON (similar a GET) |
| GET | /studies/{id} | Detalle enriquecido |
| POST | /reload | Recarga datos en memoria |

Documentación detallada: `README_API.md`.

## Estructura del Proyecto
```
app/
  main.py
  services/ (pipeline, filtros, ranking, generación)
odr/ (datasets versionados necesarios)
results/ (exportaciones derivadas)
scripts/ (utilidades, PDF docs)
docs/DEPLOYMENT.md
BACKEND_DOCUMENTACION.md
README_API.md
```

## Campos Generados
| Campo | Descripción | Motivo |
|-------|-------------|--------|
| título_alterno | Variante breve / aclaratoria | Facilita lectura rápida |
| resumen_compacto | Síntesis del contenido relevante | Orientación inicial |
| términos_emergentes | Tokens distintivos del subconjunto filtrado | Navegación temática |
| destacados | Subconjunto priorizado | Priorización visual |

## Caching y Rendimiento
- Cache in-memory por combinación de filtros / página.
- Búsqueda escalonada evita listas vacías (coincidencia total → parcial → frase → aproximada).
- Recarga manual con `/reload` (proteger en producción).

## Roadmap
1. Autenticación para `/reload`.
2. Ponderación avanzada con citaciones y recencia.
3. Filtro de rango de fechas y citaciones mínimas.
4. Resaltado de términos en fragmentos.
5. Persistencia opcional de índice.

## Documentación Extendida
- Referencia rápida de API: `README_API.md`
- Documento técnico completo: `BACKEND_DOCUMENTACION.md`
- Despliegue y contenedores: `docs/DEPLOYMENT.md`

## Análisis NLP Exploratorio (Fase Original)
La sección siguiente preserva el contenido de la fase inicial de exploración NLP sobre documentos, mantenida por valor histórico y para reproducir experimentos de tokenización, lematización y análisis de frecuencias.

### Pipeline de Procesamiento (Histórico)
1. Carga de datos.
2. Exploración de estructura.
3. Limpieza (URLs, números, puntuación, normalización).
4. Tokenización.
5. Filtrado de stopwords.
6. Lematización (spaCy).
7. Frecuencias y ranking.
8. Visualizaciones (barras, nubes, bigramas).
9. Exportación multi-formato.

### Características (Histórico)
- Trazabilidad con `doc_id` y `accession`.
- Procesamiento bilingüe (EN/ES).
- Visualizaciones estáticas e interactivas.
- Exportación a Excel/CSV/JSON.

### Tecnologías (Histórico)
- Datos: pandas, numpy.
- NLP: nltk, spacy.
- Visualización: matplotlib, seaborn, plotly, wordcloud.

### Instalación NLP (Opcional)
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

### Uso Notebook
Abrir `procesamiento.ipynb` y ejecutar secuencialmente.

### Salidas Típicas
```
documentos_metadata.*
lemmas_expandido.*
frecuencias_lemmas.*
bigramas_frecuentes.*
documentos_procesados.json
```

### Personalización NLP
```python
custom_stopwords = {"ejemplo1", "ejemplo2"}
stopwords_combined = stopwords_combined.union(custom_stopwords)
```

### Problemas Frecuentes
Modelo spaCy faltante → instalar. Stopwords NLTK faltantes → descargar. Memoria → procesar en lotes.

---
## Licencia
Ver archivo `LICENSE` (MIT) salvo indicación distinta.

## Autoría
Proyecto para competencia / exploración bioespacial 2025.

---
¿Buscas el detalle completo? Lee `BACKEND_DOCUMENTACION.md`.
