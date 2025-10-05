import json
import pathlib
import shutil
import time
import logging
from typing import Dict, Any, List

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
ODR_DIR = BASE_DIR / 'odr'
DOI_DICT_PATH = ODR_DIR / 'doi_dict.json'
OUTPUT_ROOT = None  # Ya no usamos carpeta 'enriched'; escritura in-place

SUPPORTED_KEYS = [
    'Study Identifier', 'Accession', 'Authoritative Source URL'
]


def setup_logger(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    logging.debug('Logger inicializado (verbose=%s)', verbose)


def load_doi_map() -> Dict[str, str]:
    with open(DOI_DICT_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # normalizar: quitar vacíos/null
    return {k: v for k, v in data.items() if v is not None and str(v).strip() != ''}


def find_osd_id(record: Dict[str, Any]) -> str | None:
    # Busca algún campo que tenga patrón OSD-###
    for key in SUPPORTED_KEYS:
        val = record.get(key)
        if not val or not isinstance(val, str):
            continue
        # Typical: 'OSD-615', or 'OSD-615/'
        parts = val.strip().split()
        for p in parts:
            if p.startswith('OSD-'):
                # limpiar sufijo '/'
                p = p.rstrip('/')
                if len(p) > 4:
                    return p
    return None


def enrich_hit(hit: Dict[str, Any], doi_map: Dict[str, str]) -> bool:
    """Enriquece un objeto 'hit' añadiendo DOI y url asociada.
    Reglas:
      - Si no hay DOI y el OSD tiene mapeo, añade DOI y url.
      - Si ya hay DOI pero falta url, añade solo url.
      - No sobreescribe DOI existente.
    Retorna True si se modificó algo."""
    src = hit.get('_source') if isinstance(hit, dict) else None
    if not isinstance(src, dict):
        return False
    modified = False
    osd = find_osd_id(src)
    existing_doi = src.get('DOI')
    if existing_doi and isinstance(existing_doi, str) and existing_doi.strip():
        # DOI ya existe: solo aseguramos 'url'
        if 'url' not in src:
            src['url'] = f"https://doi.org/{existing_doi.strip()}"
            modified = True
        return modified
    # No había DOI: intentamos agregar
    if not osd:
        return False
    doi_val = doi_map.get(osd)
    if not doi_val:
        return False
    src['DOI'] = doi_val
    if 'url' not in src:
        src['url'] = f"https://doi.org/{doi_val}"
    modified = True
    return modified


def enrich_file(input_path: pathlib.Path, doi_map: Dict[str, str]) -> dict:
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    modified = 0
    hits = data.get('hits', {}).get('hits', []) if isinstance(data, dict) else []
    for h in hits:
        if enrich_hit(h, doi_map):
            modified += 1
    meta = {
        'file': str(input_path.relative_to(ODR_DIR)),
        'modified_records': modified,
        'total_records': len(hits)
    }
    # Escritura in-place
    with open(input_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return meta


def _collect_input_files(scan_debug: bool = False, scan_interval: int = 10) -> List[pathlib.Path]:
    """Recolecta los archivos originales SIN incluir la carpeta de salida.
    Añade logging incremental para diagnosticar demoras en el escaneo."""
    files: List[pathlib.Path] = []
    start_scan = time.time()
    count = 0
    if not ODR_DIR.exists():
        logging.error("Directorio ODR no existe: %s", ODR_DIR)
        return files
    for root, dirs, filenames in os.walk(ODR_DIR):  # os.walk suele dar feedback más rápido que rglob en algunos entornos
        for fname in filenames:
            if not fname.lower().endswith('.json'):
                continue
            if fname == 'doi_dict.json':
                continue
            path = pathlib.Path(root) / fname
            files.append(path)
            count += 1
            if scan_debug and count % scan_interval == 0:
                elapsed = time.time() - start_scan
                logging.debug("Escaneo: %d archivos hallados (%.2fs)", count, elapsed)
    logging.info("Escaneo completo: %d archivos (%.2fs)", len(files), time.time() - start_scan)
    return sorted(files)


def main(dry_run: bool = False, progress_interval: int = 10, verbose: bool = False, limit: int | None = None, scan_debug: bool = False):
    setup_logger(verbose)
    start = time.time()
    doi_map = load_doi_map()
    logging.info("DOIs disponibles (no vacíos): %d", len(doi_map))

    logging.info("Iniciando escaneo de archivos en %s", ODR_DIR)
    input_files = _collect_input_files(scan_debug=scan_debug, scan_interval=5 if scan_debug else 25)
    total_files = len(input_files)
    if limit is not None:
        input_files = input_files[:limit]
        logging.info("Limitando a primeros %d archivos de %d totales", len(input_files), total_files)
    else:
        logging.info("Archivos a procesar (excluyendo 'enriched'): %d", total_files)

    # Ya no creamos carpeta de salida; escritura in-place

    metas = []
    last_print = time.time()
    for idx, path in enumerate(input_files, start=1):
        file_start = time.time()
        rel = path.relative_to(ODR_DIR)
        # Escritura in-place -> out_path == path (se mantiene variable para compatibilidad del flujo)
        try:
            if verbose:
                logging.debug("Procesando %s (%d/%d)", rel, idx, len(input_files))
            if dry_run:
                with open(path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        metas.append({'file': str(rel), 'error': 'json_load_failed'})
                        logging.warning("Fallo al cargar JSON %s", rel)
                        continue
                hits = data.get('hits', {}).get('hits', []) if isinstance(data, dict) else []
                possible = 0
                for h in hits:
                    src = h.get('_source', {}) if isinstance(h, dict) else {}
                    osd = find_osd_id(src) if isinstance(src, dict) else None
                    if osd and osd in doi_map:
                        possible += 1
                metas.append({'file': str(rel), 'potential_matches': possible, 'total_records': len(hits)})
            else:
                meta = enrich_file(path, doi_map)
                metas.append(meta)
        except KeyboardInterrupt:
            logging.error("Interrumpido por el usuario. Generando reporte parcial...")
            break
        except Exception as e:
            logging.exception("Error inesperado procesando %s", rel)
            metas.append({'file': str(rel), 'error': str(e)})

        file_elapsed = time.time() - file_start
        if verbose:
            logging.debug("Archivo %s procesado en %.2fs", rel, file_elapsed)

        if idx % progress_interval == 0 or (time.time() - last_print) > 30:
            elapsed = time.time() - start
            pct = (idx/len(input_files))*100 if input_files else 100
            logging.info("Progreso: %d/%d (%.1f%%) - %.1fs transcurridos", idx, len(input_files), pct, elapsed)
            last_print = time.time()

    report_path = ODR_DIR / ('dry_run_report.json' if dry_run else 'enrichment_report.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(metas, f, ensure_ascii=False, indent=2)
    elapsed_total = time.time() - start
    logging.info("Reporte guardado en: %s (tiempo total %.1fs)", report_path, elapsed_total)

    if not dry_run:
        total_mod = sum(m.get('modified_records', 0) for m in metas)
        logging.info("Registros modificados con DOI: %d", total_mod)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Enriquecer JSON ODR con DOI a partir de doi_dict.json')
    parser.add_argument('--dry-run', action='store_true', help='Solo calcula coincidencias sin escribir archivos')
    parser.add_argument('--progress-interval', type=int, default=10, help='Cada cuántos archivos imprimir progreso')
    parser.add_argument('--verbose', action='store_true', help='Logging detallado por archivo')
    parser.add_argument('--limit', type=int, help='Procesar solo primeros N archivos (debug)')
    parser.add_argument('--scan-debug', action='store_true', help='Mostrar progreso detallado durante el escaneo inicial')
    args = parser.parse_args()
    # Import tardío de os para evitar dependencias arriba
    global os
    import os  # noqa
    main(dry_run=args.dry_run, progress_interval=args.progress_interval, verbose=args.verbose, limit=args.limit, scan_debug=args.scan_debug)
