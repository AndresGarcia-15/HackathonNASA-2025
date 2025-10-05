# Guía de Contribución

Gracias por tu interés en contribuir.

## Flujo Básico
1. Haz fork del repositorio.
2. Crea una rama: `git checkout -b feature/mi-cambio`.
3. Realiza commits descriptivos (convención: `feat:`, `fix:`, `docs:`, `refactor:`...).
4. Asegúrate de que la API arranca (`uvicorn app.main:app`).
5. Abre un Pull Request con descripción clara.

## Estilo de Código
- Python 3.10+
- Formato sugerido: black (opcional de momento).
- Importaciones agrupadas (stdlib / terceros / local) cuando sea posible.

## Tests (Pendiente)
Cuando se añada carpeta `tests/`, ejecutar:
```
pytest -q
```

## Commits
Ejemplos:
```
feat: añadir endpoint /summarize
fix: corregir selección de fila raw más rica
refactor: extraer función de parseo de fechas
```

## Reporte de Issues
Incluye:
- Descripción breve.
- Pasos para reproducir.
- Resultado actual vs esperado.
- Fragmento de payload si aplica.

## Seguridad
No incluyas credenciales ni datasets privados en los PR.

## Roadmap (Extracto)
Ver `README.md` y `BACKEND_DOCUMENTACION.md` para alineación antes de proponer grandes cambios.

---
Gracias por ayudar a mejorar el proyecto.
