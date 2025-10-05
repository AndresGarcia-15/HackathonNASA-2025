# Guía de Despliegue

## 1. Estructura Recomendada
```
NASA-2025/
  app/
    main.py
    services/
    models/
  streamlit_app.py
  odr/
  data/
    raw/
    processed/
  results/
  scripts/
  docs/
  requirements.txt
  Dockerfile
  README.md
  BACKEND_DOCUMENTACION.md
  .gitignore
```

## 2. Publicar en GitHub
1. git init
2. git add .
3. git commit -m "feat: estructura inicial"
4. git branch -M main
5. git remote add origin <URL_REPO>
6. git push -u origin main

## 3. Variables de Entorno (Sugerido)
Crear `.env.example`:
```
API_TITLE=NASA Studies API
API_VERSION=0.1.0
LOG_LEVEL=info
```

## 4. Construcción Docker
```
docker build -t nasa-backend:latest .
docker run -p 8000:8000 nasa-backend:latest
```
Swagger: http://localhost:8000/docs

## 5. Opciones de Despliegue
| Plataforma | Método | Notas |
|-----------|--------|-------|
| Render/Railway | Dockerfile | Ajustar timeout inicial |
| Cloud Run | Imagen container | Escalado automático |
| ECS / Fargate | Task Definition | Montar datos externos |
| Kubernetes | Deployment + Service | ConfigMap + Secret |

## 6. Datos
- Mantener muestras mínimas en `odr/`.
- Dataset completo: usar bucket externo (S3 / Blob / GCS) y descargar al arranque si es necesario.

## 7. Tests (Ejemplo)
`tests/test_health.py`:
```python
def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
```

## 8. CI (Sugerido)
Workflow con: instalación deps, lint, tests.

## 9. Seguridad
- Restringir CORS en producción.
- Proteger `/reload` con API key.
- Añadir rate limiting si expones públicamente.

## 10. Streamlit
Ejecutar aparte (otro servicio) o en otra imagen. Evitar correr API y Streamlit en el mismo proceso en producción.

## 11. Próximos Pasos
- Añadir `pyproject.toml`.
- Añadir pre-commit (black, isort, flake8).
- Incluir logging estructurado.

Última edición: (actualizar)
