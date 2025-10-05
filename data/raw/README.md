# data/raw

Coloca aquí datos crudos adicionales si integras nuevas fuentes externas.

Versionado:
- Solo este README se incluye en el repositorio.
- Agrega un script de descarga si los datos son públicos.
- Usa nombres descriptivos por fuente (ej: `esa_*.json`, `pubmed_*.json`).

Sugerencia script (pseudo):
```bash
python scripts/fetch_external_sources.py --output data/raw
```

Añade un `.placeholder` si alguna plataforma de despliegue requiere que exista la carpeta vacía.
