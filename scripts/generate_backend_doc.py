"""Generador avanzado de PDF para la documentación del backend.

Características:
 - Portada con título y metadatos.
 - Tabla de contenidos automática.
 - Estilos tipográficos diferenciados.
 - Numeración de secciones (opcional).
 - Numeración de páginas y pie personalizado.

Uso:
  python scripts/generate_backend_doc.py
  python scripts/generate_backend_doc.py --md BACKEND_DOCUMENTACION.md --out backend_documentacion.pdf --no-cover

Requiere: reportlab
"""
from __future__ import annotations
import argparse, re, sys, os, datetime

MD_DEFAULT = "BACKEND_DOCUMENTACION.md"
PDF_DEFAULT = "backend_documentacion.pdf"

def ensure_reportlab():
    try:
        import reportlab  # noqa: F401
        return True
    except Exception:
        print("[ERROR] Falta dependencia 'reportlab'. Instala con: pip install reportlab", file=sys.stderr)
        return False

def parse_markdown(md_text: str):
    """Parser sencillo de markdown para encabezados, listas, párrafos y bloques de código.
    - Elimina comentarios HTML.
    - Soporta bloques con ``` (code fences).
    """
    # Eliminar comentarios HTML multilinea
    md_text = re.sub(r"<!--.*?-->", "", md_text, flags=re.DOTALL)
    lines = md_text.splitlines()
    blocks = []
    buffer: list[str] = []
    list_mode = False
    code_mode = False
    code_buffer: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip('\n')
        # Detectar fences de código
        if line.strip().startswith('```'):
            if code_mode:
                # cierre de bloque
                blocks.append(('code', '\n'.join(code_buffer)))
                code_buffer = []
                code_mode = False
            else:
                # apertura
                if buffer:
                    blocks.append(('para', '\n'.join(buffer)))
                    buffer = []
                list_mode = False
                code_mode = True
            continue
        if code_mode:
            code_buffer.append(line)
            continue
        if re.match(r"^\s*$", line):
            if buffer:
                blocks.append(("para", "\n".join(buffer)))
                buffer = []
            list_mode = False
            continue
        if line.startswith('#'):
            if buffer:
                blocks.append(("para", "\n".join(buffer)))
                buffer = []
            level = len(line) - len(line.lstrip('#'))
            text = line[level:].strip()
            blocks.append((f"h{level}", text))
            list_mode = False
            continue
        if line.lstrip().startswith(('-', '*')) and not line.strip().startswith('---'):
            if not list_mode:
                if buffer:
                    blocks.append(("para", "\n".join(buffer)))
                    buffer = []
                list_mode = True
                blocks.append(("ul", []))
            item = line.lstrip()[1:].strip()
            if blocks and blocks[-1][0] == 'ul':
                blocks[-1][1].append(item)
            continue
        if list_mode:
            list_mode = False
        buffer.append(line)
    if code_mode and code_buffer:
        blocks.append(('code', '\n'.join(code_buffer)))
    if buffer:
        blocks.append(("para", "\n".join(buffer)))
    return blocks

def simple_inline_format(text: str) -> str:
    # Bold y italic primero
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    # Proteger tags permitidos
    placeholders = {
        '<b>':'@@B_OPEN@@', '</b>':'@@B_CLOSE@@',
        '<i>':'@@I_OPEN@@', '</i>':'@@I_CLOSE@@'
    }
    for k,v in placeholders.items():
        text = text.replace(k,v)
    # Escapar el resto de '<', '>' y '&'
    text = text.replace('&', '&amp;').replace('<','&lt;').replace('>','&gt;')
    # Restaurar tags permitidos
    for k,v in placeholders.items():
        text = text.replace(v,k)
    return text

def build_pdf(md_path: str, pdf_path: str, include_cover: bool = True, number_sections: bool = True):
    from reportlab.lib.pagesizes import LETTER
    from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, ListFlowable,
                                    ListItem, PageBreak, Preformatted)
    # Import específico de TOC (no siempre incluido en __init__)
    try:
        from reportlab.platypus.tableofcontents import TableOfContents  # type: ignore
        TOC_AVAILABLE = True
    except Exception:
        TOC_AVAILABLE = False
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch

    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    blocks = parse_markdown(md_text)

    styles = getSampleStyleSheet()
    # Paleta
    PRIMARY = colors.HexColor('#0B3D91')  # azul profundo
    ACCENT = colors.HexColor('#FFB800')   # dorado NASA‑like

    # Estilos personalizados
    styles.add(ParagraphStyle(name='TitlePage', fontSize=28, leading=32, textColor=PRIMARY, alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name='Subtitle', fontSize=14, leading=18, textColor=colors.black, alignment=1, spaceAfter=40))
    styles.add(ParagraphStyle(name='H1', parent=styles['Heading1'], fontSize=18, textColor=PRIMARY, spaceBefore=12, spaceAfter=8))
    styles.add(ParagraphStyle(name='H2', parent=styles['Heading2'], fontSize=15, textColor=PRIMARY, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name='H3', parent=styles['Heading3'], fontSize=13, textColor=PRIMARY, spaceBefore=8, spaceAfter=4))
    styles.add(ParagraphStyle(name='Body', parent=styles['BodyText'], fontSize=10, leading=14))
    styles.add(ParagraphStyle(name='List', parent=styles['BodyText'], fontSize=10, leftIndent=16, bulletIndent=8, leading=13))
    styles.add(ParagraphStyle(name='TOCHeading', fontSize=16, leading=20, textColor=PRIMARY, spaceAfter=12, alignment=1))

    toc = None
    if TOC_AVAILABLE:
        toc = TableOfContents()
        toc.levelStyles = [
            ParagraphStyle(fontSize=11, name='TOCLevel1', leftIndent=4, firstLineIndent=-4, spaceBefore=4),
            ParagraphStyle(fontSize=10, name='TOCLevel2', leftIndent=18, firstLineIndent=-4, spaceBefore=2),
            ParagraphStyle(fontSize=9, name='TOCLevel3', leftIndent=32, firstLineIndent=-4, spaceBefore=1)
        ]

    # Mecanismo para numerar secciones
    section_counters = {1:0, 2:0, 3:0}
    def format_section(level: int, text: str) -> str:
        if not number_sections:
            return text
        if level == 1:
            section_counters[1] += 1
            section_counters[2] = 0
            section_counters[3] = 0
        elif level == 2:
            section_counters[2] += 1
            section_counters[3] = 0
        elif level == 3:
            section_counters[3] += 1
        nums = [str(section_counters[i]) for i in (1,2,3) if section_counters[i] > 0]
        return '.'.join(nums) + ' ' + text

    def add_toc_entry(level: int, text: str, page_num_func):
        # El texto sin markup para TOC
        raw_text = re.sub(r'<.*?>', '', text)
        toc.addEntry(level, raw_text, page_num_func())

    # Página maestra con pie
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(inch*0.7, 0.6*inch, f"Página {doc.page}")
        canvas.drawRightString(LETTER[0]-inch*0.7, 0.6*inch, 'Documentación Backend')
        canvas.setStrokeColor(PRIMARY)
        canvas.setLineWidth(0.5)
        canvas.line(inch*0.7, 0.75*inch, LETTER[0]-inch*0.7, 0.75*inch)
        canvas.restoreState()

    frame = Frame(inch*0.7, inch, LETTER[0]-inch*1.4, LETTER[1]-inch*1.8, id='normal')
    doc = BaseDocTemplate(pdf_path, pagesize=LETTER, title='Documentación Backend', author='Generado')
    template = PageTemplate(id='base', frames=[frame], onPage=footer)
    doc.addPageTemplates([template])

    story = []

    if include_cover:
        story.append(Paragraph('Plataforma de Catálogo Científico', styles['TitlePage']))
        story.append(Paragraph('Documentación Funcional y Técnica Resumida', styles['Subtitle']))
        meta = f"Generado: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        story.append(Paragraph(meta, styles['Body']))
        story.append(PageBreak())

    story.append(Paragraph('Tabla de Contenidos', styles['TOCHeading']))
    if toc is not None:
        story.append(toc)
    else:
        story.append(Paragraph('<i>(TOC no disponible en esta instalación de reportlab)</i>', styles['Body']))
    story.append(PageBreak())

    # Construcción de contenido
    # Usamos doc.canv en afterFlowable para registrar entradas del TOC
    def _after_flowable(flowable):
        from reportlab.platypus import Paragraph
        if toc is None:
            return
        if isinstance(flowable, Paragraph):
            style_name = flowable.style.name
            if style_name in ('H1','H2','H3'):
                level = {'H1':0,'H2':1,'H3':2}[style_name]
                text = flowable.getPlainText()
                toc.addEntry(level, text, doc.page)
    doc.afterFlowable = _after_flowable

    for kind, content in blocks:
        if kind.startswith('h'):
            lvl = int(kind[1:])
            if lvl > 3:
                lvl = 3
            formatted = format_section(lvl, content)
            style_name = 'H1' if lvl == 1 else 'H2' if lvl == 2 else 'H3'
            story.append(Paragraph(simple_inline_format(formatted), styles[style_name]))
            story.append(Spacer(1, 4))
        elif kind == 'para':
            paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
            for p in paragraphs:
                story.append(Paragraph(simple_inline_format(p), styles['Body']))
                story.append(Spacer(1, 4))
        elif kind == 'ul':
            # Lista con bullets estilizados
            from reportlab.platypus import ListFlowable, ListItem
            items = []
            for it in content:
                items.append(ListItem(Paragraph(simple_inline_format(it), styles['Body']), bulletColor=ACCENT))
            story.append(ListFlowable(items, bulletType='bullet', start='bullet', leftIndent=18))
            story.append(Spacer(1, 6))
        elif kind == 'code':
            # Bloque de código monoespaciado
            code_text = content.replace('\t','    ')
            story.append(Preformatted(code_text, styles['Body']))
            story.append(Spacer(1, 8))

    doc.build(story)
    print(f"[OK] PDF generado: {pdf_path}")

def main():
    parser = argparse.ArgumentParser(description='Generar PDF estilizado de documentación backend')
    parser.add_argument('--md', default=MD_DEFAULT, help='Ruta del archivo Markdown origen')
    parser.add_argument('--out', default=PDF_DEFAULT, help='Nombre del archivo PDF resultante')
    parser.add_argument('--no-cover', action='store_true', help='Omitir portada')
    parser.add_argument('--no-section-numbers', action='store_true', help='Omitir numeración automática de secciones')
    args = parser.parse_args()

    if not os.path.exists(args.md):
        print(f"[ERROR] No existe archivo markdown: {args.md}", file=sys.stderr)
        sys.exit(1)
    if not ensure_reportlab():
        sys.exit(1)
    build_pdf(args.md, args.out, include_cover=not args.no_cover, number_sections=not args.no_section_numbers)

if __name__ == '__main__':
    main()
