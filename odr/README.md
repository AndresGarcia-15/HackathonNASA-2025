# Carpeta `odr/`

Archivos JSON originales usados para construir el catálogo.

Recomendaciones:
- No subir el dataset completo si es grande o tiene restricciones.
- Mantener una pequeña muestra (1–2 archivos por organismo) para reproducibilidad.
- Documentar cómo obtener el dataset completo (script, enlace o instrucción manual).

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

Si decides usar Git LFS, crea `.gitattributes` y añade patrones para `*.json` grandes.
