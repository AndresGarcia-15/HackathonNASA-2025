<!--
Documento diseñado para conversión a PDF con estilos. Evitar la palabra "heurística" y preferir
"generadas a partir de contexto" / "reglas adaptativas".
-->

# Plataforma de Catálogo Científico – Documentación de Backend

> Versión: 1.0  
> Última actualización: (actualizar según despliegue)  
> Alcance: Catálogo unificado de estudios y artículos

---

## 1. Resumen Ejecutivo
El backend consolida información científica procedente de estudios estructurados (archivos JSON por organismo y tipo de proyecto) y artículos de literatura biomédica (archivo unificado con metadatos y citaciones). Su propósito es ofrecer un servicio de consulta ágil que permita filtrar, buscar y obtener descripciones enriquecidas de cada registro, destacando elementos relevantes y generando valor adicional a partir del propio contenido.

El servicio expone endpoints REST que proporcionan:  
* Listado de estudios/artículos con filtros combinables.  
* Búsqueda textual con coincidencia escalonada para minimizar resultados vacíos.  
* Identificación de términos emergentes dentro del subconjunto filtrado.  
* Detalle enriquecido por identificador, fusionando datos agregados y campos originales.  
* Recarga dinámica de datos en memoria para reflejar nuevas fuentes sin reinicio completo.

## 2. Principios de Diseño
* **Unificación**: Varias fuentes heterogéneas se presentan bajo un modelo coherente.  
* **Rapidez**: Operación íntegramente en memoria para respuestas inmediatas.  
* **Claridad Semántica**: Etiquetas de organismo y tipo de proyecto normalizadas.  
* **Valor Añadido**: Campos generados a partir de contexto (títulos alternos, resúmenes compactos, términos emergentes).  
* **Escalabilidad Evolutiva**: Estructura preparada para integrar índices externos o nuevas fuentes.  
* **Transparencia**: Exposición de conteos, etapas de coincidencia y distribución facetada.  

## 3. Panorama Funcional
| Capacidad | Descripción | Beneficio |
|-----------|------------|-----------|
| Filtrado | Organismo y tipo de proyecto | Exploración dirigida |
| Búsqueda escalonada | Adaptación progresiva de coincidencia | Reduce vacíos de resultados |
| Campos generados | Títulos alternos, resúmenes, términos emergentes | Mejora comprensión rápida |
| Destacados | Subconjunto priorizado por reglas adaptativas | Enfoque en lo más relevante |
| Detalle enriquecido | Fusión de vista agregada + fila cruda más completa | Máxima densidad informativa |
| Facetas | Conteos por organismo y proyecto | Navegación intuitiva |
| Recarga | Reconstrucción en caliente | Agilidad operativa |

## 4. Flujo Global de Datos
```
Fuentes JSON  -->  Ingesta  -->  Normalización  -->  Unión Global
	|                              |                 |
	|                              v                 v
  Artículos PMC  ------------>  Consolidación  -->  Vista Agregada
								     |        
								     v        
							 Generación de Campos
								     |
								     v
							     Endpoints API
								     |
								     v
						     Detalle (Fusión Dinámica)
```

## 5. Capas Lógicas
1. **Ingesta**: Lectura de archivos ODR jerárquicos y del archivo de artículos.  
2. **Normalización**: Identificadores, fechas, etiquetas de organismo y tipo de proyecto.  
3. **Consolidación**: Construcción de la vista agregada y preservación del conjunto original (raw).  
4. **Enriquecimiento**: Generación de campos a partir de contexto (resúmenes, títulos alternos, términos emergentes, priorización).  
5. **Búsqueda y Filtrado**: Aplicación de filtros declarativos y coincidencia textual escalonada.  
6. **Exposición REST**: Endpoints para catálogo, facetas, detalle y recarga.  
7. **Caching en Memoria**: Reutilización de estructuras y minimización de reprocesos.  

## 6. Fuentes de Datos
| Fuente | Formato | Contenido Clave |
|--------|---------|-----------------|
| ODR/<organismo>/*.json | JSON jerárquico (`hits.hits`) | Metadatos de estudios, fechas, identificadores |
| articulos_actualizado.json | JSON lineal | Título, abstract, conclusiones, DOI, fecha, citaciones, figuras |

## 7. Normalización Esencial
* **Identificador**: Se prioriza `Study Identifier`; fallback a `Accession` o URL autoritativa.  
* **Etiquetas**: Mapas de organismo y tipo de proyecto soportan variantes de escritura.  
* **Fechas**: Detección flexible (epoch y múltiples formatos) → ISO 8601 UTC.  
* **Artículos**: Se consolidan abstract y conclusiones en una descripción compuesta; se mantienen también campos separados.  
* **URL**: Derivada de `pmc` o `pmid` para acceso directo.  

## 8. Modelo Interno Bifásico
| Estructura | Descripción | Uso |
|------------|------------|-----|
| Vista Agregada | Una fila por (Identificador, Organismo, Proyecto) | Listados y facetas |
| Dataset Raw | Todas las filas originales | Enriquecimiento de detalle |

Esta dualidad permite mantener compacidad en catálogos y riqueza en los detalles.

## 9. Campos Generados a partir de Contexto
| Campo | Propósito | Fuente de Cálculo |
|-------|-----------|-------------------|
| Título alterno | Clarificar registros genéricos | Análisis del propio título/descripción |
| Resumen compacto | Lectura rápida | Selección de fragmentos relevantes |
| Términos emergentes | Orientación temática | Frecuencia y distintividad local |
| Destacados | Foco inicial | Reglas adaptativas (densidad, fecha, citaciones, metadatos) |

## 10. Búsqueda Escalonada
Etapas aplicadas secuencialmente hasta obtener resultados suficientes:
1. Coincidencia completa de palabras.  
2. Coincidencia parcial mínima (subset).  
3. Coincidencia de frase (secuencias textuales).  
4. Coincidencia aproximada (tolerancia a pequeñas variaciones).  

## 11. Generación de Resultados
Cada respuesta de listado incluye:  
* Página solicitada (paginación configurable).  
* Colección de elementos destacados.  
* Términos emergentes.  
* Campos generados diferenciados visualmente (según frontend).  
* Datos diagnósticos opcionales (etapa de coincidencia, tokens ignorados).  

## 12. Facetas y Filtros
* Facetas precomputadas: organismo y tipo de proyecto con conteos únicos.  
* Filtros acumulativos antes de la búsqueda textual.  
* Base para futuros filtros (fechas, citaciones).  

## 13. Detalle Enriquecido
Proceso de respuesta al consultar un identificador:  
1. Se localiza la fila en la vista agregada.  
2. Se selecciona la fila raw con mayor cantidad de campos no vacíos.  
3. Se fusionan valores sin sobrescribir datos ya válidos.  
4. Se establecen alias (`study_id`) y se recuperan etiquetas faltantes.  
5. Artículos PMC muestran abstract y conclusiones por separado, citaciones, figuras y DOI.  

## 14. Rendimiento y Caching
* In-memory para baja latencia.  
* Reutilización de resultados intermedios por combinación de filtros.  
* Paginación limita el tamaño de payload.  
* Recarga puntual sin reiniciar el proceso.  

## 15. Endpoint de Recarga
`/reload` recompone: dataset raw, vista agregada y estructuras generadoras. Devuelve conteos y número de columnas para validación rápida.  

## 16. Gestión de Fechas
* Módulo centralizado de parseo.  
* Normalización a ISO UTC.  
* Fechas ilegibles se preservan como null evitando falsos positivos.  

## 17. Estrategia contra Duplicados
| Escenario | Acción |
|----------|--------|
| Repetición exacta (vista) | Eliminación por clave compuesta |
| Artículos repetidos | Eliminación por identificador PMC/PMID |
| Detalle | Selección fila con mayor densidad de valores |

## 18. Calidad y Mitigaciones
| Riesgo | Mitigación |
|-------|-----------|
| Identificador ausente | Búsqueda fallback en Accession / URL |
| Fechas irregulares | Parseo progresivo y fallback a null |
| Títulos demasiado genéricos | Título alterno generado |
| Búsquedas estériles | Escalonamiento de coincidencia |
| Valores tipo lista en chequeos nulos | Función segura de evaluación |
| Organismos no mapeados | Formato legible (title case) |

## 19. Seguridad (Estado Actual y Recomendaciones)
Estado: CORS abierto y endpoints sin autenticación.  
Recomendaciones inmediatas:  
* Autenticación para `/reload`.  
* Lista blanca de orígenes.  
* Registro estructurado y rate limiting.  

## 20. Extensibilidad
Pasos para sumar una nueva fuente:  
1. Lector dedicado → DataFrame.  
2. Alinear columnas esenciales.  
3. Unir con dataset raw.  
4. Regenerar vista agregada.  
5. Ajustar mapeos y generación contextual si aparecen nuevos metadatos.  

## 21. Limitaciones Vigentes
* Dependencia de memoria (no índice invertido externo).  
* Sin versionado histórico de snapshots.  
* Búsqueda aproximada simple (sin lematización profunda).  
* Citaciones aún no aplican un peso diferenciado avanzado.  

## 22. Ruta Evolutiva Propuesta
1. Incorporar autores y formato de cita normalizado.  
2. Introducir ponderación por citaciones y recencia.  
3. Resaltar términos coincidentes en fragmentos.  
4. Filtrado por rango de fechas y umbral mínimo de citaciones.  
5. Persistencia incremental (arranque más rápido).  
6. Autenticación / autorización basada en roles.  
7. Configuración externalizada (variables entorno).  
8. Logging estructurado y métricas.  

## 23. Glosario
| Término | Definición |
|---------|-----------|
| Vista Agregada | Fila representativa por combinación clave |
| Campos Generados | Valores añadidos a partir del propio contenido |
| Términos Emergentes | Tokens distintivos del subconjunto filtrado |
| Destacados | Subconjunto priorizado por reglas adaptativas |
| Fusión de Detalle | Mezcla vista + fila raw más completa |
| Coincidencia Escalonada | Estrategia progresiva de búsqueda textual |

## 24. Endpoints
| Endpoint | Método | Propósito | Notas |
|----------|--------|----------|-------|
| /health | GET | Estado y conteos básicos | Diagnóstico rápido |
| /facets | GET | Facetas y distribución | Para paneles laterales |
| /studies | GET | Listado filtrado | Parámetros en query |
| /studies/search | POST | Búsqueda avanzada | Parámetros en body JSON |
| /studies/{id} | GET | Detalle enriquecido | Fusión dinámica |
| /reload | POST | Reconstruir dataset | Uso controlado recomendado |

## 25. Campos Clave
Identificación (Study Identifier, pmc, pmid, DOI), taxonomía (organism_label, project_label), contenido (Study Title, Study Description, abstract_raw, conclusions_raw), metadatos (release_date, url, cited_by, fig_ids) y campos generados (título alterno, resumen compacto, términos emergentes, destacados).

## 26. Ejemplo Narrativo de Búsqueda
1. Usuario selecciona organismo “Plant” y tipo “High Altitude”.  
2. Se filtra la vista agregada.  
3. Se aplica coincidencia completa sobre título y descripción.  
4. Si insuficiente, se avanza a coincidencia parcial / frase / aproximada.  
5. Se generan campos añadidos (resumen, título alterno, términos emergentes).  
6. Se etiqueta subconjunto destacado.  
7. Se entrega JSON paginado listo para interfaz.  

## 27. Conclusión
El backend constituye una base robusta para descubrimiento científico: integra fuentes dispares, aporta valor interpretativo, optimiza la navegación y prepara el terreno para expansión (ranking avanzado, seguridad fortalecida y escalado con índices especializados). Su diseño modular permite evolucionar sin comprometer la claridad del modelo actual.

---
Fin del documento.
