# data/processed

Resultados intermedios o transformaciones derivadas (parquet, csv, modelos, índices secundarios).

Política:
- No versionar archivos grandes o regenerables.
- Documentar en `scripts/` cómo reproducirlos.
- Mantener formatos columnar (parquet) para velocidad si se requiere.

Ejemplo regeneración (pseudo):
```bash
python scripts/build_indices.py --input odr --output data/processed
```

Incluye un `.placeholder` si necesitas forzar la presencia del directorio.
