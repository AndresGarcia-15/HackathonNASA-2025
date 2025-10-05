# Procesamiento NLP - Documentos de Biología Espacial NASA

## 📝 Descripción

Este proyecto realiza un análisis exhaustivo de Procesamiento de Lenguaje Natural (NLP) sobre documentos científicos de la NASA relacionados con biología espacial. El objetivo es identificar tópicos relevantes, frecuencias de términos y patrones en la investigación espacial.

## 🎯 Objetivo

Competición NASA - Análisis de documentos científicos para identificar tendencias y tópicos principales en investigación de biología espacial.

## 🔄 Pipeline de Procesamiento

1. **Carga de Datos**: Importación de archivos JSON con estudios de la NASA
2. **Exploración**: Análisis de la estructura y campos disponibles
3. **Limpieza**: 
   - Eliminación de URLs, menciones, números
   - Normalización de texto
   - Eliminación de puntuación
4. **Tokenización**: Separación del texto en palabras individuales
5. **Filtrado**: Eliminación de stopwords (español e inglés)
6. **Lematización**: Reducción de palabras a su forma base usando spaCy
7. **Análisis de Frecuencias**: Conteo y ranking de términos
8. **Visualización**:
   - Gráficos de barras (top 30 palabras)
   - Nubes de palabras (WordCloud)
   - Análisis de bigramas
9. **Exportación**: Guardado en múltiples formatos (Excel, CSV, JSON)

## 📊 Características Principales

- ✅ **Trazabilidad Completa**: Todos los datos mantienen conexión con `doc_id` y `accession`
- ✅ **Procesamiento Bilingüe**: Soporta inglés y español
- ✅ **Múltiples Visualizaciones**: Gráficos estáticos e interactivos
- ✅ **Exportación Múltiple**: Excel, CSV y JSON para diferentes usos
- ✅ **Listo para Web**: Formato JSON estructurado para aplicaciones web

## 🛠️ Tecnologías Utilizadas

### Librerías de Python

- **Procesamiento de Datos**: `pandas`, `numpy`
- **NLP**: `nltk`, `spacy`
- **Visualización**: `matplotlib`, `seaborn`, `plotly`, `wordcloud`
- **Manejo de Archivos**: `openpyxl`, `xlsxwriter`

### Modelos

- **spaCy**: `en_core_web_sm` (modelo de inglés)
- **NLTK**: Stopwords en inglés y español

## 🚀 Instalación

### Opción 1: Instalación Automática (Recomendada)

```powershell
# Ejecutar el script de instalación
.\setup.ps1
```

### Opción 2: Instalación Manual

```powershell
# Instalar dependencias
pip install -r requirements.txt

# Descargar modelo de spaCy
python -m spacy download en_core_web_sm

# Descargar recursos NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

## 📖 Uso

1. **Preparar los datos**: Coloca tu archivo JSON en el directorio del proyecto

2. **Ejecutar el notebook**: Abre `procesamiento.ipynb` en Jupyter/VS Code

3. **Ejecutar celda por celda**: Sigue el flujo del notebook

4. **Revisar resultados**: Los archivos se generarán automáticamente

## 📁 Estructura de Archivos de Salida

```
documentos_metadata.xlsx/.csv       # Metadatos de documentos procesados
lemmas_expandido.xlsx/.csv          # DataFrame expandido (un lemma por fila)
frecuencias_lemmas.xlsx/.csv        # Conteo de frecuencias de palabras
bigramas_frecuentes.xlsx/.csv       # Pares de palabras más comunes
documentos_procesados.json          # Datos completos en formato JSON
```

## 🔍 Formato de Datos

### DataFrame Principal (documentos_metadata)

| Campo | Descripción |
|-------|-------------|
| `doc_id` | ID único del documento |
| `accession` | Código de acceso del estudio |
| `study_identifier` | Identificador del estudio |
| `study_title` | Título del estudio |
| `study_description` | Descripción completa |
| `managing_center` | Centro NASA responsable |
| `project_type` | Tipo de proyecto |
| `num_tokens` | Cantidad de tokens |
| `num_lemmas` | Cantidad de lemmas |

### DataFrame Expandido (lemmas_expandido)

| Campo | Descripción |
|-------|-------------|
| `doc_id` | ID del documento origen |
| `accession` | Código de acceso |
| `lemma` | Palabra lematizada |

## 📈 Visualizaciones Incluidas

1. **Gráfico de Barras Horizontal**: Top 30 palabras más frecuentes
2. **Gráfico Interactivo (Plotly)**: Exploración dinámica de frecuencias
3. **WordCloud Clásica**: Nube de palabras estilo científico
4. **WordCloud Espacial**: Tema oscuro tipo espacio
5. **Gráfico de Bigramas**: Pares de palabras más comunes

## 🌐 Demo de Búsqueda (FastAPI + Streamlit)

Se incluye una demo ligera en `streamlit_app.py` que consume el endpoint POST `/studies/search` de la API FastAPI.

### Ejecutar API
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Ejecutar Streamlit
```powershell
streamlit run streamlit_app.py
```

Luego abre el navegador (la terminal mostrará la URL local, típicamente http://localhost:8501) y ajusta filtros en el sidebar. Puedes cambiar la base de la API (por ejemplo un túnel ngrok) en el campo "API Base URL".

Características:
- Búsqueda reactiva por `q` y filtros (`organism`, `project_type`, `keywords`).
- Vista de artículos importantes, página de resultados y suggested keywords.
- Modo compacto para reducir payload (`compact=true`).

Para exponer la demo fuera de tu red local puedes usar ngrok:
```powershell
ngrok http 8501
```

Si quieres proteger endpoints sensibles, añade una verificación de API key en FastAPI antes de exponer públicamente.

## 💡 Próximos Pasos

Después de completar este procesamiento base, puedes:

1. **Aplicar filtros específicos** según los tópicos identificados
2. **Realizar análisis de tópicos** (LDA, NMF)
3. **Clustering de documentos** similares
4. **Análisis temporal** si hay fechas disponibles
5. **Integrar con otros datasets** JSON

## 🔧 Personalización

### Agregar Stopwords Personalizadas

```python
custom_stopwords = {'palabra1', 'palabra2', 'palabra3'}
stopwords_combined = stopwords_combined.union(custom_stopwords)
```

### Cambiar Longitud Mínima de Tokens

```python
# En la función tokenize_and_filter
filtered_tokens = [token for token in tokens 
                   if len(token) >= 4]  # Cambiar de 3 a 4
```

### Ajustar WordCloud

```python
wordcloud = WordCloud(
    width=2000,           # Cambiar ancho
    height=1000,          # Cambiar alto
    max_words=200,        # Más palabras
    colormap='inferno'    # Cambiar paleta
)
```

## 📝 Notas Importantes

- ⚠️ El procesamiento puede tardar varios minutos dependiendo del tamaño del dataset
- ⚠️ Se requiere conexión a internet para la instalación inicial
- ⚠️ Los archivos JSON deben estar en formato UTF-8
- ⚠️ La lematización con spaCy puede consumir bastante memoria con datasets grandes

## 🐛 Solución de Problemas

### Error: "Model 'en_core_web_sm' not found"

```powershell
python -m spacy download en_core_web_sm
```

### Error: "Resource 'stopwords' not found"

```powershell
python -c "import nltk; nltk.download('stopwords')"
```

### Error de Memoria

Si tienes problemas de memoria con datasets grandes:
- Procesa en lotes más pequeños
- Desactiva la lematización (usa tokens directamente)
- Aumenta la memoria virtual de Python

## 👨‍💻 Autor

Proyecto desarrollado para la competición NASA 2025 - Análisis de Biología Espacial

## 📄 Licencia

Este proyecto es de código abierto para uso educativo y de investigación.

---

**¡Buena suerte con la competición NASA! 🚀🌟**
