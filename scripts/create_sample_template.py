"""Erzeugt ein Beispiel-Angebot als PDF, das als Vorlage hochgeladen werden kann.

Aufruf:  python scripts/create_sample_template.py
Ergebnis: sample_data/beispiel_angebot_vorlage.pdf
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
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

OUT = Path(__file__).resolve().parent.parent / "sample_data" / "beispiel_angebot_vorlage.pdf"
ACCENT = colors.HexColor("#1F3A5F")


def main() -> None:
    base = getSampleStyleSheet()
    normal = ParagraphStyle("n", parent=base["Normal"], fontSize=10, leading=14)
    title = ParagraphStyle("t", parent=base["Heading1"], fontSize=16, textColor=ACCENT)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], fontSize=11, textColor=ACCENT)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    story = []

    story.append(Paragraph("<b>Muster GmbH</b> · Musterstraße 1 · 12345 Musterstadt", normal))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", color=ACCENT, thickness=1.2))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Beispiel Kunde GmbH<br/>Beispielweg 5<br/>10115 Berlin", normal))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Angebot Nr. ANG-20260101-1000 &nbsp;|&nbsp; Datum: 01.01.2026 "
                           "&nbsp;|&nbsp; Gültig bis: 31.01.2026", normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Angebot über Büroausstattung", title))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Sehr geehrte Frau Beispiel,<br/><br/>vielen Dank für Ihre Anfrage und Ihr "
        "Interesse an unseren Produkten. Gerne unterbreiten wir Ihnen das folgende "
        "Angebot, das genau auf Ihren Bedarf zugeschnitten ist.", normal))
    story.append(Spacer(1, 10))

    rows = [
        ["Pos.", "Art.-Nr.", "Beschreibung", "Menge", "Einzelpreis", "Gesamt"],
        ["1", "MON-2400", "Office Monitor 24", "2 Stück", "179,00 €", "358,00 €"],
        ["2", "KB-MX1", "Funktastatur Comfort", "2 Stück", "69,90 €", "139,80 €"],
    ]
    table = Table(rows, colWidths=[12 * mm, 24 * mm, 60 * mm, 22 * mm, 26 * mm, 26 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF2F7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Zwischensumme: 497,80 €<br/>zzgl. MwSt (19%): 94,58 €<br/>"
                           "<b>Gesamtbetrag: 592,38 €</b>", normal))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "Wir sind überzeugt, dass diese Lösung Ihre Anforderungen optimal erfüllt, und "
        "stehen für Rückfragen jederzeit gern zur Verfügung.", normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Konditionen", h2))
    story.append(Paragraph(
        "<b>Zahlung:</b> 14 Tage netto nach Rechnungserhalt.<br/>"
        "<b>Lieferung:</b> frei Haus innerhalb von 5 Werktagen.<br/>"
        "<b>Gültigkeit:</b> Dieses Angebot ist gültig bis 31.01.2026.", normal))
    story.append(Spacer(1, 14))
    story.append(Paragraph("Mit freundlichen Grüßen<br/><br/>Muster GmbH", normal))

    doc.build(story)
    print(f"Beispiel-Vorlage erstellt: {OUT}")


if __name__ == "__main__":
    main()
