"""Erzeugt das Angebots-PDF mit ReportLab."""

from __future__ import annotations

from functools import partial
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .config import Settings
from .models import FinalOffer
from .utils import fmt_money, fmt_qty

ACCENT = colors.HexColor("#1F3A5F")
LIGHT = colors.HexColor("#EEF2F7")
GREY = colors.HexColor("#6B7280")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "small": ParagraphStyle("small", parent=base["Normal"], fontSize=8, leading=10,
                                textColor=GREY),
        "small_r": ParagraphStyle("small_r", parent=base["Normal"], fontSize=8,
                                  leading=10, textColor=GREY, alignment=TA_RIGHT),
        "normal": ParagraphStyle("normal", parent=base["Normal"], fontSize=9.5,
                                 leading=13.5),
        "addr": ParagraphStyle("addr", parent=base["Normal"], fontSize=10, leading=14),
        "title": ParagraphStyle("title", parent=base["Heading1"], fontSize=16,
                                leading=20, textColor=ACCENT, spaceAfter=2),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=10.5, leading=14,
                             textColor=ACCENT, spaceBefore=6, spaceAfter=2),
        "cell": ParagraphStyle("cell", parent=base["Normal"], fontSize=9, leading=12),
        "cell_name": ParagraphStyle("cell_name", parent=base["Normal"], fontSize=9,
                                    leading=12, fontName="Helvetica-Bold"),
        "cell_r": ParagraphStyle("cell_r", parent=base["Normal"], fontSize=9,
                                 leading=12, alignment=TA_RIGHT),
        "th": ParagraphStyle("th", parent=base["Normal"], fontSize=9,
                             textColor=colors.white, fontName="Helvetica-Bold"),
        "th_r": ParagraphStyle("th_r", parent=base["Normal"], fontSize=9,
                               textColor=colors.white, fontName="Helvetica-Bold",
                               alignment=TA_RIGHT),
    }


def _paragraphs(text: str, style) -> list:
    """Wandelt Mehrzeilen-Text in mehrere Paragraphs (Absätze bleiben erhalten)."""
    out = []
    for block in (text or "").split("\n"):
        block = block.strip()
        out.append(Paragraph(block.replace("&", "&amp;"), style) if block else Spacer(1, 4))
    return out


def _footer(canvas, doc, company, st) -> None:
    canvas.saveState()
    width, _ = A4
    y = 12 * mm
    canvas.setStrokeColor(LIGHT)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, y + 6 * mm, width - doc.rightMargin, y + 6 * mm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    line1 = f"{company.name} · {' · '.join(company.address_lines)}"
    line2 = f"Tel.: {company.phone} · {company.email} · {company.website} · {company.tax_id}"
    canvas.drawString(doc.leftMargin, y + 2.5 * mm, line1[:140])
    canvas.drawString(doc.leftMargin, y, line2[:160])
    canvas.drawRightString(width - doc.rightMargin, y, f"Seite {doc.page}")
    canvas.restoreState()


def build_offer_pdf(offer: FinalOffer, settings: Settings) -> bytes:
    """Baut das fertige Angebots-PDF und gibt es als Bytes zurück."""
    s = _styles()
    company = settings.company
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=24 * mm,
        title=f"Angebot {offer.offer_number}", author=company.name,
    )

    story: list = []

    # Briefkopf: Firmenname (Akzent) + Kontakt rechts
    header = Table(
        [[
            Paragraph(f"<b>{company.name}</b>", ParagraphStyle(
                "co", fontSize=15, leading=18, textColor=ACCENT)),
            Paragraph("<br/>".join([*company.address_lines, company.phone,
                                    company.email, company.website]), s["small_r"]),
        ]],
        colWidths=[doc.width * 0.55, doc.width * 0.45],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT))
    story.append(Spacer(1, 10))

    # Kundenadresse links + Angebots-Metadaten rechts
    cust = offer.customer
    addr_lines = [cust.company] if cust.company else []
    if cust.contact_name:
        addr_lines.append(cust.contact_name)
    if cust.address:
        addr_lines.extend(cust.address.split("\n"))
    if not addr_lines:
        addr_lines = ["(Kundenanschrift bitte ergänzen)"]
    addr_html = "<br/>".join(line.strip() for line in addr_lines if line.strip())

    meta = Table(
        [
            ["Angebotsnummer:", offer.offer_number],
            ["Datum:", offer.date],
            ["Gültig bis:", offer.valid_until],
            ["Kunden-E-Mail:", cust.email or "—"],
        ],
        colWidths=[28 * mm, doc.width * 0.45 - 28 * mm],
    )
    meta.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    addr_block = Table([[Paragraph(addr_html, s["addr"]), meta]],
                       colWidths=[doc.width * 0.55, doc.width * 0.45])
    addr_block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(addr_block)
    story.append(Spacer(1, 14))

    # Titel + Einleitung
    story.append(Paragraph(offer.title.replace("&", "&amp;"), s["title"]))
    story.append(Spacer(1, 6))
    story.extend(_paragraphs(offer.intro_text, s["normal"]))
    story.append(Spacer(1, 10))

    # Positionstabelle
    head = [
        Paragraph("Pos.", s["th"]), Paragraph("Art.-Nr.", s["th"]),
        Paragraph("Beschreibung", s["th"]), Paragraph("Menge", s["th_r"]),
        Paragraph("Einzelpreis", s["th_r"]), Paragraph("Gesamt", s["th_r"]),
    ]
    rows = [head]
    for it in offer.line_items:
        desc = f"<b>{it.name}</b>".replace("&", "&amp;")
        if it.description:
            desc += "<br/>" + it.description.replace("&", "&amp;")
        rows.append([
            Paragraph(str(it.position), s["cell"]),
            Paragraph(it.sku or "—", s["cell"]),
            Paragraph(desc, s["cell"]),
            Paragraph(f"{fmt_qty(it.quantity)} {it.unit}", s["cell_r"]),
            Paragraph(fmt_money(it.unit_price, offer.currency), s["cell_r"]),
            Paragraph(fmt_money(it.line_total, offer.currency), s["cell_r"]),
        ])

    table = Table(
        rows, repeatRows=1,
        colWidths=[12 * mm, 24 * mm, doc.width - 12 * mm - 24 * mm - 18 * mm - 24 * mm - 24 * mm,
                   18 * mm, 24 * mm, 24 * mm],
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))

    # Summenblock (rechtsbündig)
    summary = Table(
        [
            ["Zwischensumme (netto):", fmt_money(offer.subtotal, offer.currency)],
            [f"zzgl. MwSt ({offer.vat_rate * 100:.0f}%):",
             fmt_money(offer.vat_amount, offer.currency)],
            ["Gesamtbetrag:", fmt_money(offer.total, offer.currency)],
        ],
        colWidths=[45 * mm, 35 * mm],
        hAlign="RIGHT",
    )
    summary.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LINEABOVE", (0, 2), (-1, 2), 0.75, ACCENT),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 2), (-1, 2), ACCENT),
        ("TOPPADDING", (0, 2), (-1, 2), 4),
    ]))
    story.append(summary)
    story.append(Spacer(1, 12))

    # Abschlusstext
    if offer.closing_text.strip():
        story.extend(_paragraphs(offer.closing_text, s["normal"]))
        story.append(Spacer(1, 8))

    # Konditionen
    story.append(Paragraph("Konditionen", s["h2"]))
    cond_bits = []
    if offer.payment_terms.strip():
        cond_bits.append(f"<b>Zahlung:</b> {offer.payment_terms}")
    if offer.delivery_terms.strip():
        cond_bits.append(f"<b>Lieferung/Leistung:</b> {offer.delivery_terms}")
    cond_bits.append(f"<b>Gültigkeit:</b> Dieses Angebot ist gültig bis {offer.valid_until}.")
    for bit in cond_bits:
        story.append(Paragraph(bit.replace("&", "&amp;"), s["normal"]))

    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f"Wir freuen uns auf Ihre Rückmeldung.<br/>Mit freundlichen Grüßen<br/><br/>"
        f"{company.name}", s["normal"]))

    on_page = partial(_footer, company=company, st=s)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
