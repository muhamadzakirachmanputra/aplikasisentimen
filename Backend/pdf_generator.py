# Backend/pdf_generator.py
"""
Module untuk generate PDF report hasil SVM classification.
Layout redesign sesuai referensi:
  - Logo kiri + Judul besar di header
  - Subtitle deskriptif
  - Card info data (Total, Latih, Uji)
  - Confusion Matrix tabel berwarna
  - Box Akurasi gradient
  - Metrik Macro Avg & Weighted Avg
  - Tabel detail per kelas berwarna
  - TTD Mengetahui (center)
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import uuid

# ─── Warna tema ─────────────────────────────────────────────────────────────────
NAVY        = colors.HexColor('#1B2A4A')
BLUE_PRIMARY = colors.HexColor('#2563EB')
BLUE_LIGHT  = colors.HexColor('#EFF6FF')
BLUE_BORDER = colors.HexColor('#BFDBFE')
ORANGE      = colors.HexColor('#EA580C')
ORANGE_LIGHT = colors.HexColor('#FFF7ED')
ORANGE_BORDER = colors.HexColor('#FED7AA')
GREEN       = colors.HexColor('#16A34A')
GREEN_LIGHT = colors.HexColor('#F0FDF4')
GREEN_BORDER = colors.HexColor('#BBF7D0')
RED         = colors.HexColor('#DC2626')
RED_LIGHT   = colors.HexColor('#FEF2F2')
RED_BORDER  = colors.HexColor('#FECACA')
YELLOW      = colors.HexColor('#CA8A04')
YELLOW_LIGHT = colors.HexColor('#FEFCE8')
YELLOW_BORDER = colors.HexColor('#FEF08A')
PURPLE      = colors.HexColor('#7C3AED')
GREY        = colors.HexColor('#6B7280')
LGREY       = colors.HexColor('#9CA3AF')
BORDER_GREY = colors.HexColor('#E5E7EB')
BG_GREY     = colors.HexColor('#F9FAFB')
WHITE       = colors.white
BLACK       = colors.HexColor('#111827')

# ─── Mapping hari & bulan Indonesia ──────────────────────────────────────────────
BULAN_ID = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
HARI_ID  = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']


def _tanggal_id(dt=None):
    if dt is None:
        dt = datetime.now()
    return f"Jakarta, {HARI_ID[dt.weekday()]}, {dt.day} {BULAN_ID[dt.month]} {dt.year}"


def _find_logo(static_dir):
    """Cari file logo dari beberapa kemungkinan lokasi."""
    candidates = [
        os.path.join(static_dir, 'icons', 'logo_sentimen.png'),
        os.path.join(static_dir, 'icons', 'logo_svm.png'),
        os.path.join(static_dir, 'logo_sentimen.png'),
        os.path.join(static_dir, 'logo_svm.png'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logo_svm.png'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


# ═════════════════════════════════════════════════════════════════════════════════
# HEADER / KOP SURAT — Modern style
# ═════════════════════════════════════════════════════════════════════════════════
def _build_header(elements, styles, report_title, subtitle, logo_path):
    """
    Header modern:
      Logo kiri + Judul besar (warna biru)
      Subtitle di bawah judul
      Garis pemisah
    """
    title_style = ParagraphStyle('HeaderTitle', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold', textColor=BLUE_PRIMARY,
        leading=20, alignment=TA_CENTER, spaceAfter=2)

    subtitle_style = ParagraphStyle('HeaderSubtitle', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica', textColor=GREY,
        leading=12, alignment=TA_CENTER, spaceAfter=0)

    # Logo
    logo_cell = ''
    if logo_path:
        try:
            logo_cell = Image(logo_path, width=0.8*inch, height=0.8*inch)
        except Exception:
            pass

    # Title text
    title_para = Paragraph(report_title.upper(), title_style)
    sub_para = Paragraph(subtitle, subtitle_style)

    if logo_cell:
        inner = Table([[title_para], [sub_para]], colWidths=[5.5*inch])
        inner.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))

        header_data = [[logo_cell, inner]]
        header_tbl = Table(header_data, colWidths=[1.0*inch, 5.8*inch])
        header_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_tbl)
    else:
        elements.append(title_para)
        elements.append(sub_para)

    # Garis kop surat tebal (double-line)
    elements.append(Spacer(1, 4))
    elements.append(HRFlowable(width='100%', thickness=3, color=NAVY, spaceAfter=1.5))
    elements.append(HRFlowable(width='100%', thickness=1, color=NAVY, spaceAfter=8))


# ═════════════════════════════════════════════════════════════════════════════════
# INFO CARDS — Total Data, Data Latih, Data Uji
# ═════════════════════════════════════════════════════════════════════════════════
def _build_info_cards(elements, styles, n_total, n_train, n_test, test_size=None):
    """3 cards in a row: Total Data Layak, Data Latih, Data Uji"""
    if test_size is not None:
        test_pct = round(test_size * 100)
        train_pct = 100 - test_pct
    elif n_total > 0:
        test_pct = round(n_test / n_total * 100)
        train_pct = 100 - test_pct
    else:
        test_pct = 20
        train_pct = 80

    card_title_style = ParagraphStyle('CardTitle', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=GREY,
        leading=10, alignment=TA_CENTER)

    card_value_navy = ParagraphStyle('CardValueNavy', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold', textColor=NAVY,
        leading=20, alignment=TA_CENTER)

    card_value_blue = ParagraphStyle('CardValueBlue', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold', textColor=BLUE_PRIMARY,
        leading=20, alignment=TA_CENTER)

    card_value_orange = ParagraphStyle('CardValueOrange', parent=styles['Normal'],
        fontSize=16, fontName='Helvetica-Bold', textColor=ORANGE,
        leading=20, alignment=TA_CENTER)

    def _fmt_num(n):
        return f"{n:,}".replace(",", ".")

    # Build cards
    card1_rows = [
        [Paragraph("Total Data Layak", card_title_style)],
        [Paragraph(_fmt_num(n_total), card_value_navy)],
    ]
    card1 = Table(card1_rows, colWidths=[2.0*inch])
    card1.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_GREY),
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    card2_rows = [
        [Paragraph(f"Data Latih ({train_pct}%)", card_title_style)],
        [Paragraph(_fmt_num(n_train), card_value_blue)],
    ]
    card2 = Table(card2_rows, colWidths=[2.0*inch])
    card2.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, BLUE_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), BLUE_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    card3_rows = [
        [Paragraph(f"Data Uji ({test_pct}%)", card_title_style)],
        [Paragraph(_fmt_num(n_test), card_value_orange)],
    ]
    card3 = Table(card3_rows, colWidths=[2.0*inch])
    card3.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, ORANGE_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), ORANGE_LIGHT),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    row = Table([[card1, card2, card3]], colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
    row.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(row)
    elements.append(Spacer(1, 10))


# ═════════════════════════════════════════════════════════════════════════════════
# SECTION TITLE
# ═════════════════════════════════════════════════════════════════════════════════
def _section_title(text, styles, icon=""):
    s = ParagraphStyle('SectionTitle', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold', textColor=NAVY,
        leading=14, spaceBefore=8, spaceAfter=6)
    return Paragraph(f"{icon} {text}", s)


# ═════════════════════════════════════════════════════════════════════════════════
# CONFUSION MATRIX — as colored table
# ═════════════════════════════════════════════════════════════════════════════════
def _build_confusion_matrix_table(elements, styles, confusion_matrix):
    """Build confusion matrix as a colored table like the reference image."""
    if not confusion_matrix or len(confusion_matrix) == 0:
        elements.append(Paragraph("<i>Data confusion matrix tidak tersedia.</i>", styles['Normal']))
        return

    labels = ['Positif', 'Negatif', 'Netral']
    cm = confusion_matrix
    n = len(cm)
    if n < 3:
        labels = labels[:n]

    title_style = ParagraphStyle('CMTitle', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', textColor=NAVY,
        leading=12, alignment=TA_CENTER)

    header_style = ParagraphStyle('CMHeader', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=WHITE,
        leading=11, alignment=TA_CENTER)

    cell_style = ParagraphStyle('CMCell', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', textColor=BLACK,
        leading=14, alignment=TA_CENTER)

    elements.append(Paragraph("PREDIKSI SVM", title_style))
    elements.append(Spacer(1, 4))

    label_colors_list = [GREEN, RED, YELLOW]
    cell_bg_colors = [
        [GREEN_LIGHT, WHITE, WHITE],
        [WHITE, RED_LIGHT, WHITE],
        [WHITE, WHITE, YELLOW_LIGHT],
    ]

    # Header row
    header_row = ['']
    for i, l in enumerate(labels):
        header_row.append(Paragraph(l, header_style))

    data_rows = [header_row]

    for i in range(n):
        lbl_color = label_colors_list[i] if i < len(label_colors_list) else NAVY
        row = [Paragraph(labels[i] if i < len(labels) else f"C{i}",
            ParagraphStyle('LabelColor', parent=styles['Normal'],
                fontSize=8, fontName='Helvetica-Bold',
                textColor=lbl_color, leading=11, alignment=TA_CENTER))]
        for j in range(n):
            val = cm[i][j] if i < len(cm) and j < len(cm[i]) else 0
            row.append(Paragraph(str(val), cell_style))
        data_rows.append(row)

    col_w = 0.85 * inch
    tbl = Table(data_rows, colWidths=[0.7*inch] + [col_w]*n)

    tbl_style = [
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (1, 1), (-1, -1), 0.5, BORDER_GREY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]

    # Header backgrounds
    for j in range(n):
        c = label_colors_list[j] if j < len(label_colors_list) else NAVY
        tbl_style.append(('BACKGROUND', (j+1, 0), (j+1, 0), c))

    # Diagonal cell backgrounds
    for i in range(n):
        if i < len(cell_bg_colors) and i < len(cell_bg_colors[i]):
            bg = cell_bg_colors[i][i]
        else:
            bg = WHITE
        tbl_style.append(('BACKGROUND', (i+1, i+1), (i+1, i+1), bg))

    # Bold diagonal values with color
    for i in range(n):
        c = label_colors_list[i] if i < len(label_colors_list) else NAVY
        tbl_style.append(('TEXTCOLOR', (i+1, i+1), (i+1, i+1), c))

    tbl.setStyle(TableStyle(tbl_style))

    # Wrap with KUNCI ASLI label on left
    kunci_style = ParagraphStyle('KunciLabel', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica-Bold', textColor=NAVY,
        leading=9, alignment=TA_CENTER)

    kunci_text = "<br/>".join(['K', 'U', 'N', 'C', 'I', '', 'A', 'S', 'L', 'I'])
    kunci_para = Paragraph(kunci_text, kunci_style)

    wrapper = Table([[kunci_para, tbl]], colWidths=[0.35*inch, None])
    wrapper.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(wrapper)


# ═════════════════════════════════════════════════════════════════════════════════
# ACCURACY BOX
# ═════════════════════════════════════════════════════════════════════════════════
def _build_accuracy_box(styles, accuracy):
    """Big accuracy display box."""
    acc_pct = accuracy * 100

    acc_label_style = ParagraphStyle('AccLabel', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', textColor=ORANGE,
        leading=12, alignment=TA_CENTER)

    acc_value_style = ParagraphStyle('AccValue', parent=styles['Normal'],
        fontSize=22, fontName='Helvetica-Bold', textColor=BLUE_PRIMARY,
        leading=26, alignment=TA_CENTER)

    box_data = [
        [Paragraph("Tingkat Akurasi:", acc_label_style)],
        [Paragraph(f"{acc_pct:.2f}%", acc_value_style)],
    ]
    box = Table(box_data, colWidths=[2.5*inch])
    box.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1.5, ORANGE_BORDER),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    return box


# ═════════════════════════════════════════════════════════════════════════════════
# METRIC BOXES — Macro Avg & Weighted Avg
# ═════════════════════════════════════════════════════════════════════════════════
def _build_metric_box(styles, title, precision, recall, f1, icon=""):
    """Build a metric summary box with Precision, Recall, F1-Score."""
    title_style = ParagraphStyle('MetricTitle', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica-Bold', textColor=NAVY,
        leading=11, alignment=TA_CENTER)

    label_style = ParagraphStyle('MetricLabel', parent=styles['Normal'],
        fontSize=7, fontName='Helvetica', textColor=GREY,
        leading=10, alignment=TA_CENTER)

    value_style = ParagraphStyle('MetricValue', parent=styles['Normal'],
        fontSize=11, fontName='Helvetica-Bold', textColor=BLUE_PRIMARY,
        leading=14, alignment=TA_CENTER)

    title_para = Paragraph(f"{icon} {title}", title_style)

    metric_data = [
        [Paragraph("Precision", label_style),
         Paragraph("Recall", label_style),
         Paragraph("F1-Score", label_style)],
        [Paragraph(f"{precision*100:.0f}%", value_style),
         Paragraph(f"{recall*100:.0f}%", value_style),
         Paragraph(f"{f1*100:.0f}%", value_style)],
    ]
    metric_tbl = Table(metric_data, colWidths=[0.8*inch, 0.8*inch, 0.8*inch])
    metric_tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
    ]))

    box_data = [
        [title_para],
        [metric_tbl],
    ]
    box = Table(box_data, colWidths=[2.6*inch])
    box.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_GREY),
        ('BACKGROUND', (0, 0), (-1, -1), WHITE),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return box


# ═════════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION DETAIL TABLE — per kelas berwarna
# ═════════════════════════════════════════════════════════════════════════════════
def _build_class_detail_table(elements, styles, report_data):
    """Detail Metrik Setiap Kelas Sentimen table."""
    if not report_data:
        elements.append(Paragraph("<i>Classification report tidak tersedia.</i>", styles['Normal']))
        return

    elements.append(_section_title("Detail Metrik Setiap Kelas Sentimen", styles))

    header_style = ParagraphStyle('DTHeader', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold', textColor=NAVY,
        leading=12, alignment=TA_CENTER)

    cell_style = ParagraphStyle('DTCell', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica', textColor=BLACK,
        leading=12, alignment=TA_CENTER)

    data = [[
        Paragraph("Kelas", header_style),
        Paragraph("Precision", header_style),
        Paragraph("Recall", header_style),
        Paragraph("F1-Score", header_style),
        Paragraph("Support", header_style),
    ]]

    class_config = {
        'positif': (GREEN, 'Positif'),
        'negatif': (RED, 'Negatif'),
        'netral': (YELLOW, 'Netral'),
    }

    for cn in ['positif', 'negatif', 'netral']:
        if cn in report_data:
            m = report_data[cn]
            color, display = class_config.get(cn, (NAVY, cn.capitalize()))
            label_s = ParagraphStyle('ClassLabel', parent=styles['Normal'],
                fontSize=9, fontName='Helvetica-Bold', textColor=color,
                leading=12, alignment=TA_LEFT)
            data.append([
                Paragraph(display, label_s),
                Paragraph(f"{m.get('precision', 0)*100:.2f}%", cell_style),
                Paragraph(f"{m.get('recall', 0)*100:.2f}%", cell_style),
                Paragraph(f"{m.get('f1-score', 0)*100:.2f}%", cell_style),
                Paragraph(str(int(m.get('support', 0))), cell_style),
            ])

    tbl = Table(data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.0*inch])
    tbl_style = [
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), BG_GREY),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, BORDER_GREY),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    tbl.setStyle(TableStyle(tbl_style))
    elements.append(tbl)


# ═════════════════════════════════════════════════════════════════════════════════
# TTD / MENGETAHUI — di kanan bawah
# ═════════════════════════════════════════════════════════════════════════════════
def _build_ttd(elements, styles):
    """Bagian tanda-tangan Mengetahui di kanan bawah."""
    tgl = _tanggal_id()

    style_bold = ParagraphStyle('TTDBold', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold', alignment=TA_CENTER,
        leading=14, textColor=BLACK)

    style_normal = ParagraphStyle('TTDNormal', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica', alignment=TA_CENTER,
        leading=14, textColor=colors.HexColor('#333333'))

    elements.append(Spacer(1, 0.3*inch))

    # Inner column (right side)
    inner_rows = [
        [Paragraph("<b>Mengetahui,</b>", style_bold)],
        [Paragraph(tgl, style_normal)],
        [Paragraph("Nama", style_normal)],
        [Spacer(1, 0.5*inch)],
        [Paragraph("( ........................................ )", style_bold)],
    ]
    inner_tbl = Table(inner_rows, colWidths=[3.2*inch])
    inner_tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    # Push ke kanan
    wrapper = Table([[Spacer(1, 1), inner_tbl]], colWidths=[3.6*inch, 3.2*inch])
    wrapper.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(wrapper)


# ═════════════════════════════════════════════════════════════════════════════════
# DATA UJI TAG — right aligned
# ═════════════════════════════════════════════════════════════════════════════════
def _build_data_uji_tag(styles, test_size=None):
    """Small tag showing test split percentage."""
    pct = int((test_size or 0.2) * 100)
    tag_style = ParagraphStyle('DataUjiTag', parent=styles['Normal'],
        fontSize=8, fontName='Helvetica', textColor=GREY,
        leading=11, alignment=TA_RIGHT)
    return Paragraph(f"Data Uji (Testing): {pct}%", tag_style)


# ═════════════════════════════════════════════════════════════════════════════════
# MAIN: generate_pdf_report
# ═════════════════════════════════════════════════════════════════════════════════
def generate_pdf_report(upload_id: str, model_data: dict, static_dir: str,
                        top_features: list = None, label_counts: dict = None,
                        report_type: str = "laporan_1", sample_preds: list = None,
                        **kwargs) -> bytes:
    """
    Generate PDF report.

    report_type:
      laporan_1  – Distribusi label (pie) + pembagian data latih/uji
      laporan_2  – Wordcloud, confusion matrix, evaluasi
      laporan_3  – TF-IDF features
      laporan_4  – 50 sampel data preprocessing
      all        – Semua digabung
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        rightMargin=0.6*inch, leftMargin=0.6*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch)

    elements = []
    styles   = getSampleStyleSheet()
    logo     = _find_logo(static_dir)

    # -- Shared styles --
    h_style = ParagraphStyle('SectionHead', parent=styles['Heading2'],
        fontSize=11, textColor=NAVY, fontName='Helvetica-Bold',
        spaceAfter=6, spaceBefore=8)

    n_style = styles['Normal']

    # -- Subtitle --
    default_subtitle = "Analisis Sentimen Youtube Music menggunakan Support Vector Machine (SVM)"

    # -- Titles --
    TITLES = {
        'laporan_1': 'Laporan Distribusi dan Pembagian Data',
        'laporan_2': 'Laporan Evaluasi Model Support Vector Machine',
        'laporan_3': 'Laporan Fitur TF-IDF',
        'laporan_4': 'Laporan 50 Sampel Data Preprocessing dan Label Prediksi',
        'all':       'Laporan Lengkap Analisis Sentimen Berbasis SVM',
    }
    title = TITLES.get(report_type, TITLES['all'])

    # Extract common data
    n_train = model_data.get('n_train') or 0
    n_test  = model_data.get('n_test') or 0
    n_total = n_train + n_test
    test_size = model_data.get('test_size')
    accuracy = model_data.get('accuracy', 0)
    precision_val = model_data.get('precision', 0)
    recall_val = model_data.get('recall', 0)
    f1_val = model_data.get('f1', 0)
    report_data = model_data.get('report')
    confusion_matrix = model_data.get('confusion_matrix')

    # ================================================================
    #  LAPORAN 1 — Distribusi & Pembagian Data
    # ================================================================
    if report_type in ('laporan_1', 'all'):
        _build_header(elements, styles, TITLES['laporan_1'] if report_type == 'all' else title,
                      default_subtitle, logo)

        elements.append(_section_title("1. Distribusi Label (Pie Chart)", styles))

        if label_counts:
            try:
                pie_path = os.path.join(static_dir, f'pie_{uuid.uuid4().hex}.png')
                lbl = list(label_counts.keys())
                szs = list(label_counts.values())
                cpie = []
                for lb in lbl:
                    if   lb.lower() == 'positif': cpie.append('#16A34A')
                    elif lb.lower() == 'negatif': cpie.append('#DC2626')
                    else:                         cpie.append('#CA8A04')

                fig, ax = plt.subplots(figsize=(3.5, 2.8))
                wedges, texts, autotexts = ax.pie(szs, labels=lbl, autopct='%1.1f%%',
                    startangle=90, colors=cpie,
                    textprops={'fontsize': 8},
                    wedgeprops={'edgecolor': 'white', 'linewidth': 2})
                for t in autotexts:
                    t.set_fontweight('bold')
                    t.set_color('white')
                ax.set_title('Distribusi Sentimen', fontsize=10, fontweight='bold',
                            color='#1B2A4A', pad=8)
                ax.axis('equal')
                plt.tight_layout()
                plt.savefig(pie_path, bbox_inches='tight', dpi=150, facecolor='white')
                plt.close(fig)

                if os.path.exists(pie_path) and os.path.getsize(pie_path) > 0:
                    img = Image(pie_path, width=3.0*inch, height=2.4*inch)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 8))
            except Exception as e:
                print(f"[PDF] Pie chart error: {e}")
                import traceback; traceback.print_exc()

            # Tabel distribusi
            total = sum(label_counts.values())
            tdata = [["Label", "Jumlah", "Persentase"]]
            for k, v in sorted(label_counts.items()):
                tdata.append([str(k).capitalize(), str(v), f"{v/total*100:.1f}%" if total else "0%"])
            tdata.append(["TOTAL", str(total), "100%"])

            t = Table(tdata, colWidths=[2*inch, 1.5*inch, 1.5*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), GREEN),
                ('TEXTCOLOR', (0,0),(-1,0), WHITE),
                ('ALIGN', (0,0),(-1,-1), 'CENTER'),
                ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0),(-1,0), 10),
                ('BOTTOMPADDING', (0,0),(-1,0), 8),
                ('TOPPADDING', (0,0),(-1,0), 8),
                ('BACKGROUND', (0,-1),(-1,-1), NAVY),
                ('TEXTCOLOR', (0,-1),(-1,-1), WHITE),
                ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'),
                ('GRID', (0,0),(-1,-1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0,1),(-1,-2), [WHITE, BG_GREY]),
                ('TOPPADDING', (0,1),(-1,-1), 6),
                ('BOTTOMPADDING', (0,1),(-1,-1), 6),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 12))
        else:
            elements.append(Paragraph("<i>Data label tidak tersedia.</i>", n_style))

        # Pembagian data
        elements.append(_section_title("2. Pembagian Data Latih dan Uji", styles))

        if n_total > 0:
            _build_info_cards(elements, styles, n_total, n_train, n_test, test_size)

            if test_size:
                train_pct = round((1 - test_size) * 100)
                test_pct = round(test_size * 100)
            elif n_total > 0:
                test_pct = round(n_test / n_total * 100)
                train_pct = 100 - test_pct
            else:
                train_pct, test_pct = 80, 20

            sd = [
                ["Keterangan", "Jumlah Data", "Persentase"],
                ["Data Latih (Training)", str(n_train), f"{train_pct}%"],
                ["Data Uji (Testing)", str(n_test), f"{test_pct}%"],
                ["Total", str(n_total), "100%"],
            ]
            st = Table(sd, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            st.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), BLUE_PRIMARY),
                ('TEXTCOLOR', (0,0),(-1,0), WHITE),
                ('ALIGN', (0,0),(-1,-1), 'CENTER'),
                ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0),(-1,0), 10),
                ('BOTTOMPADDING', (0,0),(-1,0), 8),
                ('TOPPADDING', (0,0),(-1,0), 8),
                ('BACKGROUND', (0,-1),(-1,-1), NAVY),
                ('TEXTCOLOR', (0,-1),(-1,-1), WHITE),
                ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'),
                ('GRID', (0,0),(-1,-1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0,1),(-1,-2), [WHITE, BLUE_LIGHT]),
                ('TOPPADDING', (0,1),(-1,-1), 6),
                ('BOTTOMPADDING', (0,1),(-1,-1), 6),
            ]))
            elements.append(st)
        else:
            elements.append(Paragraph("<i>Data pembagian belum tersedia.</i>", n_style))

        _build_ttd(elements, styles)

    # ================================================================
    #  LAPORAN 2 — Evaluasi Model (main reference layout)
    # ================================================================
    if report_type in ('laporan_2', 'all'):
        if report_type == 'all':
            elements.append(PageBreak())

        _build_header(elements, styles,
                      'Laporan Evaluasi Model Support Vector Machine',
                      default_subtitle, logo)

        # Section title with data uji tag
        section_title_p = _section_title("Evaluasi Model SVM", styles)
        uji_tag = _build_data_uji_tag(styles, test_size)
        title_row = Table([[section_title_p, uji_tag]], colWidths=[4.0*inch, 2.8*inch])
        title_row.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(title_row)
        elements.append(Spacer(1, 4))

        # Info cards
        _build_info_cards(elements, styles, n_total, n_train, n_test, test_size)

        # --- Main content: CM left, Metrics right ---
        cm_elements_inner = []
        _build_confusion_matrix_table(cm_elements_inner, styles, confusion_matrix)

        if cm_elements_inner:
            cm_tbl = Table([[e] for e in cm_elements_inner])
            cm_tbl.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
        else:
            cm_tbl = Paragraph("<i>N/A</i>", n_style)

        # Right side: Accuracy + Macro + Weighted
        acc_box = _build_accuracy_box(styles, accuracy)

        macro_p = macro_r = macro_f = 0
        weighted_p = weighted_r = weighted_f = 0
        if report_data:
            if 'macro avg' in report_data:
                ma = report_data['macro avg']
                macro_p = ma.get('precision', 0)
                macro_r = ma.get('recall', 0)
                macro_f = ma.get('f1-score', 0)
            if 'weighted avg' in report_data:
                wa = report_data['weighted avg']
                weighted_p = wa.get('precision', 0)
                weighted_r = wa.get('recall', 0)
                weighted_f = wa.get('f1-score', 0)

        macro_box = _build_metric_box(styles, "Laporan Klasifikasi (Macro Avg)",
                                       macro_p, macro_r, macro_f)
        weighted_box = _build_metric_box(styles, "Laporan Klasifikasi (Weighted Avg)",
                                          weighted_p, weighted_r, weighted_f)

        right_data = [
            [acc_box],
            [Spacer(1, 6)],
            [macro_box],
            [Spacer(1, 6)],
            [weighted_box],
        ]
        right_tbl = Table(right_data, colWidths=[2.8*inch])
        right_tbl.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        # 2-column layout
        main_layout = Table([[cm_tbl, right_tbl]], colWidths=[3.8*inch, 3.0*inch])
        main_layout.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

        # Bordered container
        bordered = Table([[main_layout]], colWidths=[6.8*inch])
        bordered.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, BORDER_GREY),
            ('BACKGROUND', (0, 0), (-1, -1), WHITE),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(bordered)
        elements.append(Spacer(1, 14))

        # Detail per-class table
        _build_class_detail_table(elements, styles, report_data)

        # Visualisasi Gambar (Wordcloud & Confusion Matrix)
        wc = os.path.join(static_dir, 'wordcloud.png')
        cm_img = os.path.join(static_dir, 'cm_heatmap.png')
        
        if os.path.exists(wc) or os.path.exists(cm_img):
            elements.append(PageBreak()) # Pindah halaman agar teks dan gambar tidak terpotong
            
            # 1. Wordcloud (Atas)
            if os.path.exists(wc):
                elements.append(_section_title("Wordcloud (Kata Frekuensi Tinggi)", styles))
                try:
                    wi = Image(wc, width=5*inch, height=2.5*inch)
                    wi.hAlign = 'CENTER'
                    elements.append(wi)
                    elements.append(Spacer(1, 20))
                except Exception:
                    elements.append(Paragraph("<i>Gagal memuat wordcloud.</i>", n_style))
                    
            # 2. Confusion Matrix Image (Bawah Wordcloud)
            if os.path.exists(cm_img):
                elements.append(_section_title("Visualisasi Confusion Matrix (Heatmap)", styles))
                try:
                    ci = Image(cm_img, width=4.5*inch, height=3.2*inch)
                    ci.hAlign = 'CENTER'
                    elements.append(ci)
                    elements.append(Spacer(1, 12))
                except Exception:
                    elements.append(Paragraph("<i>Gagal memuat confusion matrix image.</i>", n_style))

        _build_ttd(elements, styles)

    # ================================================================
    #  LAPORAN 3 — TF-IDF Features
    # ================================================================
    if report_type in ('laporan_3', 'all'):
        if report_type == 'all':
            elements.append(PageBreak())

        _build_header(elements, styles, TITLES['laporan_3'], default_subtitle, logo)

        elements.append(_section_title("Top TF-IDF Features (Kata Kunci)", styles))

        if top_features:
            fd = [["#", "Feature", "Avg Score", "Max Score", "Frequency"]]
            for i, f in enumerate(top_features[:20], 1):
                fd.append([str(i), str(f.get('feature_name','')),
                           f"{f.get('avg_score',0):.4f}", f"{f.get('max_score',0):.4f}",
                           str(f.get('frequency',0))])
            ft = Table(fd, colWidths=[0.4*inch, 2.0*inch, 1.2*inch, 1.2*inch, 1.0*inch])
            ft.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), BLUE_PRIMARY),
                ('TEXTCOLOR', (0,0),(-1,0), WHITE),
                ('ALIGN', (0,0),(-1,-1), 'CENTER'),
                ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0),(-1,0), 10),
                ('BOTTOMPADDING', (0,0),(-1,0), 8),
                ('TOPPADDING', (0,0),(-1,0), 8),
                ('GRID', (0,0),(-1,-1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0,1),(-1,-1), [WHITE, BLUE_LIGHT]),
                ('ALIGN', (1,1),(1,-1), 'LEFT'),
                ('TOPPADDING', (0,1),(-1,-1), 5),
                ('BOTTOMPADDING', (0,1),(-1,-1), 5),
            ]))
            elements.append(ft)
        else:
            elements.append(Paragraph("<i>Data TF-IDF tidak tersedia.</i>", n_style))

        _build_ttd(elements, styles)

    # ================================================================
    #  LAPORAN 4 — Sampel Data Preprocessing
    # ================================================================
    if report_type in ('laporan_4', 'all'):
        if report_type == 'all':
            elements.append(PageBreak())

        _build_header(elements, styles, TITLES['laporan_4'], default_subtitle, logo)

        elements.append(_section_title("Sampel Data Preprocessing dengan Label Prediksi (50 Data)", styles))

        if sample_preds and len(sample_preds) > 0:
            sd4 = [["No", "Teks Asli", "Label Asli", "Prediksi SVM"]]
            for i, p in enumerate(sample_preds[:50], 1):
                teks = (p.get("content_original") or p.get("content_stemmed")
                        or p.get("teks_asli") or p.get("teks_clean") or p.get("teks") or "")
                if len(str(teks)) > 80:
                    teks = str(teks)[:77] + "..."
                la = p.get("label_asli") or p.get("label") or "-"
                ps = p.get("prediksi_svm") or p.get("sentimen") or p.get("prediksi") or "-"

                label_color = '#333333'
                pred_color = '#333333'
                if str(la).lower() == 'positif': label_color = '#16A34A'
                elif str(la).lower() == 'negatif': label_color = '#DC2626'
                elif str(la).lower() == 'netral': label_color = '#CA8A04'
                if str(ps).lower() == 'positif': pred_color = '#16A34A'
                elif str(ps).lower() == 'negatif': pred_color = '#DC2626'
                elif str(ps).lower() == 'netral': pred_color = '#CA8A04'

                sd4.append([
                    str(i),
                    Paragraph(str(teks), ParagraphStyle('Sm', parent=n_style, fontSize=7, leading=9)),
                    Paragraph(str(la), ParagraphStyle('La', parent=n_style, fontSize=8,
                        leading=10, textColor=colors.HexColor(label_color), alignment=TA_CENTER)),
                    Paragraph(str(ps), ParagraphStyle('Ps', parent=n_style, fontSize=8,
                        leading=10, textColor=colors.HexColor(pred_color), alignment=TA_CENTER)),
                ])

            st4 = Table(sd4, colWidths=[0.4*inch, 3.6*inch, 0.8*inch, 0.8*inch])
            st4.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), NAVY),
                ('TEXTCOLOR', (0,0),(-1,0), WHITE),
                ('ALIGN', (0,0),(-1,0), 'CENTER'),
                ('ALIGN', (0,1),(0,-1), 'CENTER'),
                ('ALIGN', (2,1),(-1,-1), 'CENTER'),
                ('VALIGN', (0,0),(-1,-1), 'TOP'),
                ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0),(-1,0), 9),
                ('BOTTOMPADDING', (0,0),(-1,0), 8),
                ('TOPPADDING', (0,0),(-1,0), 8),
                ('GRID', (0,0),(-1,-1), 0.5, BORDER_GREY),
                ('ROWBACKGROUNDS', (0,1),(-1,-1), [WHITE, BG_GREY]),
                ('TOPPADDING', (0,1),(-1,-1), 4),
                ('BOTTOMPADDING', (0,1),(-1,-1), 4),
            ]))
            elements.append(st4)
        else:
            elements.append(Paragraph("<i>Data prediksi tidak tersedia.</i>", n_style))

        _build_ttd(elements, styles)

    # ============ BUILD ============
    doc.build(elements)
    content = buf.getvalue()
    buf.close()
    return content
