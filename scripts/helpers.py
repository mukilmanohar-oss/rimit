"""
Shared helpers, styles, and palette for the RIMIT Development Plan.

This module is import-safe (no circular dependencies) — it only imports
from reportlab and stdlib. All section modules (sections_content,
sections_part2, sections_part3) and the main build_dev_plan.py script
import from here.
"""
import os
import sys
import hashlib

PDF_SKILL_DIR = "/home/z/my-project/skills/pdf"
sys.path.insert(0, os.path.join(PDF_SKILL_DIR, "scripts"))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Image, KeepTogether, CondPageBreak, NextPageTemplate, PageTemplate, Frame,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ──────────────────────────── Font Registration ────────────────────────────
FONT_DIR = "/usr/share/fonts"

pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Regular.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FONT_DIR}/truetype/noto-serif-sc/NotoSerifSC-Bold.ttf'))
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')

pdfmetrics.registerFont(TTFont('SarasaMonoSC', f'{FONT_DIR}/truetype/chinese/SarasaMonoSC-Light.ttf'))

pdfmetrics.registerFont(TTFont('FreeSerif', f'{FONT_DIR}/truetype/freefont/FreeSerif.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Bold', f'{FONT_DIR}/truetype/freefont/FreeSerifBold.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-Italic', f'{FONT_DIR}/truetype/freefont/FreeSerifItalic.ttf'))
pdfmetrics.registerFont(TTFont('FreeSerif-BoldItalic', f'{FONT_DIR}/truetype/freefont/FreeSerifBoldItalic.ttf'))
registerFontFamily('FreeSerif', normal='FreeSerif', bold='FreeSerif-Bold',
                   italic='FreeSerif-Italic', boldItalic='FreeSerif-BoldItalic')

pdfmetrics.registerFont(TTFont('DejaVuSans', f'{FONT_DIR}/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', f'{FONT_DIR}/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSansMono', f'{FONT_DIR}/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold')

from pdf import install_font_fallback
install_font_fallback()

# ──────────────────────────── Cascade Palette (cold/minimal, seed=42) ─────────
PAGE_BG       = colors.HexColor('#f4f5f5')
SECTION_BG    = colors.HexColor('#f0f1f2')
CARD_BG       = colors.HexColor('#e8eaeb')
TABLE_STRIPE  = colors.HexColor('#ebeded')
HEADER_FILL   = colors.HexColor('#32454e')
COVER_BLOCK   = colors.HexColor('#566a74')
BORDER        = colors.HexColor('#acbdc5')
ICON          = colors.HexColor('#4b86a4')
ACCENT        = colors.HexColor('#1f6c92')
ACCENT_2      = colors.HexColor('#c23a50')
TEXT_PRIMARY  = colors.HexColor('#131515')
TEXT_MUTED    = colors.HexColor('#747b7e')
SEM_SUCCESS   = colors.HexColor('#529067')
SEM_WARNING   = colors.HexColor('#8c7443')
SEM_ERROR     = colors.HexColor('#a25b54')
SEM_INFO      = colors.HexColor('#507aa4')

TABLE_HEADER_COLOR = HEADER_FILL
TABLE_HEADER_TEXT  = colors.white
TABLE_ROW_EVEN     = colors.white
TABLE_ROW_ODD      = TABLE_STRIPE

# ──────────────────────────── Page Geometry ────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN

# ──────────────────────────── Paragraph Styles ────────────────────────────
ss = getSampleStyleSheet()

H1 = ParagraphStyle('H1', parent=ss['Heading1'],
    fontName='FreeSerif-Bold', fontSize=20, leading=26,
    textColor=HEADER_FILL, spaceBefore=18, spaceAfter=10, alignment=TA_LEFT)

H2 = ParagraphStyle('H2', parent=ss['Heading2'],
    fontName='FreeSerif-Bold', fontSize=14, leading=18,
    textColor=ACCENT, spaceBefore=14, spaceAfter=6, alignment=TA_LEFT)

H3 = ParagraphStyle('H3', parent=ss['Heading3'],
    fontName='FreeSerif-Bold', fontSize=11.5, leading=15,
    textColor=TEXT_PRIMARY, spaceBefore=10, spaceAfter=4, alignment=TA_LEFT)

BODY = ParagraphStyle('Body', parent=ss['BodyText'],
    fontName='FreeSerif', fontSize=10.5, leading=16,
    textColor=TEXT_PRIMARY, spaceBefore=0, spaceAfter=8, alignment=TA_JUSTIFY,
    firstLineIndent=0)

BODY_LEFT = ParagraphStyle('BodyLeft', parent=BODY, alignment=TA_LEFT)

BULLET = ParagraphStyle('Bullet', parent=BODY,
    leftIndent=18, bulletIndent=6, firstLineIndent=0,
    spaceBefore=0, spaceAfter=4, alignment=TA_LEFT)

CAPTION = ParagraphStyle('Caption', parent=BODY,
    fontName='FreeSerif-Italic', fontSize=9.5, leading=12,
    textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=4, spaceAfter=12)

CODE = ParagraphStyle('Code', parent=BODY,
    fontName='DejaVuSansMono', fontSize=8.5, leading=11,
    textColor=TEXT_PRIMARY, leftIndent=12, rightIndent=12,
    spaceBefore=4, spaceAfter=8, alignment=TA_LEFT,
    backColor=CARD_BG, borderColor=BORDER, borderWidth=0.5,
    borderPadding=6)

TABLE_HEADER_STYLE = ParagraphStyle('TableHeader',
    fontName='FreeSerif-Bold', fontSize=9.5, leading=12,
    textColor=colors.white, alignment=TA_CENTER)

TABLE_CELL_STYLE = ParagraphStyle('TableCell',
    fontName='FreeSerif', fontSize=9, leading=12,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, wordWrap='CJK')

# TOC styles
TOC_LEVEL_0 = ParagraphStyle('TOCLevel0',
    fontName='FreeSerif-Bold', fontSize=11, leading=18,
    textColor=TEXT_PRIMARY, leftIndent=0, firstLineIndent=0,
    spaceBefore=4, spaceAfter=2)

TOC_LEVEL_1 = ParagraphStyle('TOCLevel1',
    fontName='FreeSerif', fontSize=10, leading=15,
    textColor=TEXT_MUTED, leftIndent=18, firstLineIndent=0,
    spaceBefore=0, spaceAfter=0)

# ──────────────────────────── Helpers ────────────────────────────
def add_heading(text, style, level=0):
    """Create a heading paragraph with TOC bookmark."""
    key = f'h_{hashlib.md5(text.encode()).hexdigest()[:8]}'
    p = Paragraph(f'<a name="{key}"/>{text}', style)
    p.bookmark_name = key
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    return p

def h1(text):
    return add_heading(text, H1, level=0)

def h2(text):
    return add_heading(text, H2, level=1)

def h3(text):
    return [Paragraph(text, H3)]

def p(text):
    return Paragraph(text, BODY)

def pl(text):
    return Paragraph(text, BODY_LEFT)

def bullet(text):
    return Paragraph(f'<bullet>&bull;</bullet>{text}', BULLET)

def caption(text):
    return Paragraph(text, CAPTION)

def code(text):
    safe = (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                .replace(' ', '&nbsp;').replace('\n', '<br/>'))
    return Paragraph(safe, CODE)

def spacer(h=8):
    return Spacer(1, h)

MAX_KEEP_HEIGHT = PAGE_H * 0.4

def safe_keep(elements):
    """Wrap in KeepTogether only if total height ≤ 40% of page."""
    total_h = 0
    for el in elements:
        try:
            _, h = el.wrap(CONTENT_W, PAGE_H)
            total_h += h
        except Exception:
            return list(elements)
    if total_h <= MAX_KEEP_HEIGHT:
        return [KeepTogether(elements)]
    elif len(elements) >= 2:
        return [KeepTogether(elements[:2])] + list(elements[2:])
    return list(elements)

def fit_image(path, max_w=None, max_h=None):
    if max_w is None:
        max_w = CONTENT_W
    if max_h is None:
        max_h = PAGE_H * 0.42
    img = Image(path)
    ow, oh = img.drawWidth, img.drawHeight
    rw = max_w / ow if ow > max_w else 1.0
    rh = max_h / oh if oh > max_h else 1.0
    r = min(rw, rh)
    img.drawWidth = ow * r
    img.drawHeight = oh * r
    img.hAlign = 'CENTER'
    return img

def make_table(data, col_weights=None, header=True, font_size=9):
    n_cols = len(data[0])
    if col_weights is None:
        col_weights = [1.0] * n_cols
    total = sum(col_weights)
    col_widths = [CONTENT_W * (w / total) for w in col_weights]

    cell_style = ParagraphStyle('TC', parent=TABLE_CELL_STYLE, fontSize=font_size, leading=font_size + 3)
    head_style = ParagraphStyle('TH', parent=TABLE_HEADER_STYLE, fontSize=font_size + 0.5, leading=font_size + 4)

    wrapped = []
    for ri, row in enumerate(data):
        wr = []
        for ci, cell in enumerate(row):
            if isinstance(cell, Paragraph):
                wr.append(cell)
            else:
                style = head_style if (header and ri == 0) else cell_style
                wr.append(Paragraph(str(cell), style))
        wrapped.append(wr)

    t = Table(wrapped, colWidths=col_widths, repeatRows=1 if header else 0, hAlign='CENTER')
    style_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ]
    if header:
        style_cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'FreeSerif-Bold'),
        ]
        for i in range(1, len(data)):
            bg = TABLE_ROW_EVEN if i % 2 == 1 else TABLE_ROW_ODD
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t

# ──────────────────────────── TOC Doc Template ────────────────────────────
class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            self.notify('TOCEntry', (level, text, self.page, key))

def footer_arabic(canv, doc):
    canv.saveState()
    canv.setFont('FreeSerif', 9)
    canv.setFillColor(TEXT_MUTED)
    canv.drawCentredString(PAGE_W / 2, 0.5 * inch, str(doc.page))
    canv.restoreState()
