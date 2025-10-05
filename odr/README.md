# Carpeta `odr/`

Archivos JSON originales usados para construir el catálogo.

Recomendaciones:

- Subir solo el subconjunto mínimo necesario para reproducir la API localmente.
- Indicar fuente oficial si hay redistribución con licencias específicas.
- Para datasets grandes: usar descarga dinámica en arranque o Git LFS.

Estructura esperada:

```
odr/
  articulos_actualizado.json        # Literatura consolidada (o fallback)
  <organismo>/
      space_flight.json
      ground.json
      high_altitude.json
      ...
```

Validación rápida (opcional):
```bash
python - <<'PY'
from app.main import load_all_datasets
datasets = load_all_datasets()
print('Vista agregada:', datasets['studies_view'].shape)
PY
```

Si decides usar Git LFS, crea `.gitattributes` y añade patrones para `*.json` grandes.
