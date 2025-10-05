# Imagen base ligera
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema mínimas (amplía si necesitas compilar modelos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar código
COPY app ./app
COPY streamlit_app.py ./
COPY BACKEND_DOCUMENTACION.md ./

# Copiar muestra de datos ODR (en producción podrías montar un volumen)
COPY odr ./odr

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
