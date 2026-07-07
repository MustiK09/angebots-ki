"""Erzeugt ein PDF, das den kompletten Quellcode formatiert zeigt und ihn
abschnittsweise (Datei für Datei) laienverständlich erklärt.

Aufruf:  python scripts/make_code_pdf.py
Ergebnis: Angebots-KI_Quellcode_Erklaerung.pdf  (im Projektordner)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Angebots-KI_Quellcode_Erklaerung.pdf"

ACCENT = colors.HexColor("#1F3A5F")
CODE_BG = colors.HexColor("#F6F8FA")
LINE_COL = colors.HexColor("#D9DEE4")
COMMENT_COL = "#6A737D"   # grau – Kommentare (Zeilen mit #)
DOC_COL = "#2E7D32"       # grün – Docstrings (dreifache Anführungszeichen)

# ---------------------------------------------------------------------------
# Inhalte: Reihenfolge + laienverständliche Erklärung je Datei
# ---------------------------------------------------------------------------

INTRO = [
    "Stell dir eine Vertriebsmitarbeiterin vor, die eine Kunden-E-Mail liest "
    "(»Wir brauchen 2 Pressen und 3 Kabelschneider …«) und daraus ein ordentliches "
    "Angebots-PDF erstellt. Genau diese Arbeit übernimmt dieses Programm automatisch.",
    "Es liest die E-Mail, sucht die passenden Produkte aus dem Firmenkatalog, "
    "formuliert die Texte, rechnet die Preise, prüft alles noch einmal selbst und "
    "gibt am Ende ein fertiges PDF aus. Für das »Verstehen« und »Formulieren« nutzt "
    "es eine künstliche Intelligenz (KI, hier »Claude«); für die Preise nutzt es "
    "feste Rechenregeln, damit die Zahlen immer stimmen.",
]

FLOW = (
    "E-Mail + Katalog  →  KI liest  →  KI entwirft  →  "
    "Programm rechnet Preise  →  KI prüft selbst  →  PDF"
)

GLOSSARY = [
    ("Python", "Die Programmiersprache, in der alles geschrieben ist."),
    ("Bibliothek", "Fertige Zusatzbausteine von anderen – z. B. »Streamlit« für die "
     "Oberfläche oder »ReportLab« für das PDF."),
    ("Funktion", "Ein benannter Arbeitsschritt (»mache X«), den man wiederverwenden "
     "kann. Im Code am Wort def erkennbar."),
    ("KI / Claude", "Die künstliche Intelligenz, die Texte versteht und schreibt."),
    ("API-Schlüssel", "Eine Art Passwort, mit dem sich das Programm bei der KI anmeldet."),
    ("CSV", "Eine einfache Tabellen-Datei (wie Excel) – hier der Produktkatalog."),
    ("PDF", "Das fertige, druckbare Dokument."),
    ("Kommentare & Docstrings", "Zeilen mit # und Texte in dreifachen Anführungszeichen "
     "(\"\"\") sind Erklärungen für Menschen und werden vom Computer nicht ausgeführt. "
     "Im Code unten sind sie farbig hervorgehoben."),
]

FILES = [
    {
        "path": "app.py",
        "title": "app.py – Die Bedienoberfläche (das Schaufenster)",
        "intro": [
            "Dies ist der Teil, den man im Browser sieht und bedient. Er baut die "
            "Web-Seite auf: Felder zum Hochladen des Katalogs, ein Textfeld für die "
            "Kunden-E-Mail und den Knopf »Angebot erstellen«.",
            "app.py nimmt die Eingaben entgegen, reicht sie an das Programm-Innere "
            "weiter und zeigt am Ende das Ergebnis samt PDF-Download an. Es enthält "
            "bewusst keine komplizierte Logik – es ist nur die Vermittlung zwischen "
            "Mensch und Maschine.",
        ],
        "parts": [
            ("Seitenleiste", "Einstellungen wie API-Schlüssel, Steuersatz und Firmendaten."),
            ("_secret / _check_password", "Lesen des geheimen Schlüssels in der Cloud und "
             "ein optionaler Passwortschutz für die öffentliche Demo."),
            ("Datei-Uploads & Textfeld", "Katalog (CSV), Vorlage (PDF) und die Kundenanfrage."),
            ("Knopf »Angebot erstellen«", "startet den Ablauf und zeigt einen Fortschritt an."),
            ("render_result", "zeigt Positionen, Summen, Hinweise und den PDF-Download."),
        ],
    },
    {
        "path": "angebots_ki/pipeline.py",
        "title": "pipeline.py – Der Ablaufplan (der Dirigent)",
        "intro": [
            "Diese Datei bestimmt die Reihenfolge der Arbeitsschritte – wie ein "
            "Dirigent, der den Musikern nacheinander den Einsatz gibt.",
            "Sie ruft der Reihe nach auf: Anfrage verstehen → Angebot entwerfen → "
            "Preise berechnen → Angebot selbst prüfen → PDF erzeugen.",
        ],
        "parts": [
            ("generate_offer", "führt die fünf Schritte in der richtigen Reihenfolge aus."),
            ("progress", "meldet Zwischenstände (»Analysiere …«) an die Oberfläche."),
            ("OfferResult", "bündelt das Endergebnis (Angebot + fertiges PDF)."),
        ],
    },
    {
        "path": "angebots_ki/claude_client.py",
        "title": "claude_client.py – Das Gehirn: die Verbindung zur KI",
        "intro": [
            "Hier spricht das Programm mit der künstlichen Intelligenz (Claude). "
            "Drei Aufgaben gehen an die KI: (1) die Kunden-E-Mail lesen und verstehen, "
            "(2) ein Angebot entwerfen, (3) das eigene Angebot kritisch prüfen.",
            "Wichtig: Die KI darf Texte schreiben und Artikel auswählen, aber KEINE "
            "Preise erfinden – die kommen später aus dem Katalog. Die langen Texte in "
            "Anführungszeichen sind die »Arbeitsanweisungen« an die KI.",
        ],
        "parts": [
            ("analyze_request", "zieht Kundendaten und gewünschte Positionen aus der E-Mail."),
            ("draft_offer", "wählt passende Artikel (per Artikelnummer) und formuliert die Texte."),
            ("review_offer", "prüft: Ist alles enthalten? Passen die Artikel? Stimmt der Text?"),
            ("_structured", "sorgt dafür, dass die KI-Antwort immer eine feste, "
             "weiterverarbeitbare Form hat."),
        ],
    },
    {
        "path": "angebots_ki/catalog.py",
        "title": "catalog.py – Der Produktkatalog (das Warenverzeichnis)",
        "intro": [
            "Diese Datei liest die CSV-Datei mit allen Produkten ein – vergleichbar "
            "mit einem Warenverzeichnis.",
            "Sie erkennt automatisch, welche Spalte Artikelnummer, Name und Preis "
            "enthält (auch bei unterschiedlichen Überschriften), und kann zu jeder "
            "Artikelnummer die Details nachschlagen.",
        ],
        "parts": [
            ("Catalog.load", "liest die CSV; erkennt Trennzeichen und Spalten automatisch."),
            ("lookup", "schlägt Preis und Daten zu einer Artikelnummer nach."),
            ("to_prompt_text", "fasst den Katalog kompakt zusammen, damit die KI ihn »lesen« kann."),
        ],
    },
    {
        "path": "angebots_ki/storage.py",
        "title": "storage.py – Der Draht zur Cloud (AWS S3)",
        "intro": [
            "Optionaler Zusatz: Statt Katalog und Vorlagen jedes Mal hochzuladen, kann "
            "das Programm sie aus einem privaten Online-Speicher (Amazon S3) laden – wie "
            "aus einem abschließbaren Aktenschrank im Internet.",
            "Diese Datei kümmert sich um das Anmelden mit Zugangsdaten, das Auflisten der "
            "verfügbaren Dateien und das Herunterladen. Ist nichts eingerichtet, wird der "
            "Teil einfach übersprungen und die App nutzt weiter Upload/Beispiele.",
        ],
        "parts": [
            ("is_configured", "prüft, ob Zugangsdaten und Bucket vorhanden sind (sonst bleibt S3 aus)."),
            ("S3Store.list_files", "listet die verfügbaren Kataloge/Vorlagen im Speicher auf."),
            ("S3Store.get_bytes", "lädt eine ausgewählte Datei herunter."),
        ],
    },
    {
        "path": "angebots_ki/pricing.py",
        "title": "pricing.py – Die Rechenabteilung",
        "intro": [
            "Hier werden alle Preise und Summen ausgerechnet – ausschließlich mit den "
            "echten Preisen aus dem Katalog, nicht von der KI. So sind die Zahlen "
            "immer korrekt.",
            "Auch Mehrwertsteuer und Gesamtsumme entstehen an dieser Stelle.",
        ],
        "parts": [
            ("price_offer", "setzt je Position den Katalogpreis ein und rechnet Zwischensumme, "
             "MwSt und Gesamt."),
            ("Warnungen", "weisen darauf hin, wenn ein gewünschter Artikel nicht im Katalog ist."),
            ("assemble_final", "baut das fertige Angebot mit Nummer, Datum und Gültigkeit zusammen."),
        ],
    },
    {
        "path": "angebots_ki/pdf_builder.py",
        "title": "pdf_builder.py – Der Dokumenten-Designer",
        "intro": [
            "Diese Datei verwandelt die fertigen Angebotsdaten in ein schön gestaltetes "
            "PDF: mit Briefkopf, Kundenadresse, Positionstabelle, Summen und Fußzeile.",
            "Man kann es sich wie eine Druckvorlage vorstellen, die automatisch "
            "ausgefüllt wird.",
        ],
        "parts": [
            ("build_offer_pdf", "baut Seite für Seite das PDF zusammen."),
            ("Positionstabelle", "listet Menge, Einzel- und Gesamtpreis je Position."),
            ("Fußzeile", "zeigt Firmenkontakt und Seitenzahl."),
        ],
    },
    {
        "path": "angebots_ki/models.py",
        "title": "models.py – Die Datenschablonen (Formulare)",
        "intro": [
            "Damit sich die Programmteile »verstehen«, gibt es feste Schablonen, wie "
            "Daten aussehen müssen – ähnlich einem Formular mit festen Feldern.",
            "Hier ist z. B. festgelegt, dass eine Position eine Artikelnummer, eine "
            "Menge und einen Preis hat.",
        ],
        "parts": [
            ("RequestAnalysis", "das Ergebnis der E-Mail-Analyse (Kunde + Positionen)."),
            ("OfferDraft", "der Angebotsentwurf der KI (noch ohne Preise)."),
            ("ReviewResult", "das Ergebnis der Selbstprüfung."),
            ("PricedLineItem / FinalOffer", "das fertige, mit Preisen versehene Angebot."),
        ],
    },
    {
        "path": "angebots_ki/config.py",
        "title": "config.py – Die Einstellungen",
        "intro": [
            "Zentrale Stellschrauben: welches KI-Modell benutzt wird, welcher "
            "Mehrwertsteuersatz gilt, wie lange ein Angebot gültig ist und welche "
            "Firmendaten im Briefkopf stehen.",
        ],
        "parts": [
            ("Settings", "allgemeine Einstellungen (Modell, Steuer, Gültigkeit …)."),
            ("CompanyInfo", "die eigenen Firmendaten für den Briefkopf."),
        ],
    },
    {
        "path": "angebots_ki/utils.py",
        "title": "utils.py – Der Werkzeugkasten (kleine Helfer)",
        "intro": [
            "Eine Sammlung kleiner Hilfsfunktionen, die überall gebraucht werden.",
        ],
        "parts": [
            ("fmt_money / fmt_qty", "schöne Darstellung von Beträgen (1.234,56 €) und Mengen."),
            ("parse_price", "versteht »1.299,00« genauso wie »1299.00«."),
            ("extract_pdf_text", "liest den Text aus der hochgeladenen Beispiel-Vorlage."),
        ],
    },
    {
        "path": "angebots_ki/errors.py",
        "title": "errors.py – Die Fehlermeldungen",
        "intro": [
            "Eine winzige, aber wichtige Datei: Sie definiert einen eigenen Fehlertyp, "
            "damit Probleme (z. B. »Katalog nicht lesbar«) als klare, verständliche "
            "Meldung in der Oberfläche erscheinen statt als technisches Kauderwelsch.",
        ],
        "parts": [],
    },
    {
        "path": "angebots_ki/__init__.py",
        "title": "__init__.py – Das »Türschild« des Programmordners",
        "intro": [
            "Diese Datei macht den Ordner angebots_ki zu einem zusammengehörigen "
            "»Paket« und stellt die wichtigsten Bausteine zum einfachen Verwenden "
            "bereit – eine Art Inhaltsverzeichnis des Programmordners.",
        ],
        "parts": [],
    },
    {
        "path": "scripts/create_sample_template.py",
        "title": "create_sample_template.py – Hilfsskript: Beispiel-Vorlage",
        "intro": [
            "Ein kleines Zusatzprogramm, das ein Beispiel-Angebot als PDF erstellt. "
            "Damit kann man die »Vorlage hochladen«-Funktion ausprobieren, ohne selbst "
            "ein PDF zu haben.",
        ],
        "parts": [],
    },
    {
        "path": "scripts/upload_to_s3.py",
        "title": "upload_to_s3.py – Hilfsskript: Daten in die Cloud laden",
        "intro": [
            "Ein kleines Zusatzprogramm, das die Beispieldaten einmalig in den "
            "AWS-Speicher hochlädt – praktisch für die Ersteinrichtung, damit im "
            "Online-Speicher gleich ein Katalog (und eine Vorlage) liegen.",
        ],
        "parts": [],
    },
]


# ---------------------------------------------------------------------------
# Code-Formatierung (Escaping, Einrückung, Farb-Hervorhebung)
# ---------------------------------------------------------------------------

def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def classify(raw: str, state: tuple[bool, str | None]):
    """Bestimmt die Farbe einer Zeile und ob wir in einem Docstring stehen."""
    in_doc, delim = state
    if in_doc:
        if delim and delim in raw:
            return DOC_COL, (False, None)
        return DOC_COL, (True, delim)
    if raw.strip().startswith("#"):
        return COMMENT_COL, (False, None)
    for d in ('"""', "'''"):
        if d in raw:
            if raw.count(d) % 2 == 1:
                return DOC_COL, (True, d)
            return DOC_COL, (False, None)
    return None, (False, None)


def code_table(source: str, code_style, lineno_style, code_width: float) -> Table:
    rows = []
    state: tuple[bool, str | None] = (False, None)
    for i, raw in enumerate(source.split("\n"), start=1):
        raw = raw.replace("\t", "    ")
        color, state = classify(raw, state)
        n_indent = len(raw) - len(raw.lstrip(" "))
        body = esc(raw[n_indent:]) or "&nbsp;"
        indent = "&nbsp;" * n_indent
        markup = f"{indent}{body}" if not color else f'{indent}<font color="{color}">{body}</font>'
        rows.append([Paragraph(str(i), lineno_style), Paragraph(markup, code_style)])

    table = Table(rows, colWidths=[26, code_width - 26])
    table.hAlign = "LEFT"
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0.4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0.4),
        ("LEFTPADDING", (0, 0), (0, -1), 4),
        ("RIGHTPADDING", (0, 0), (0, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 6),
        ("RIGHTPADDING", (1, 0), (1, -1), 6),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, LINE_COL),
    ]))
    return table


# ---------------------------------------------------------------------------
# Seiten-Fußzeile
# ---------------------------------------------------------------------------

def footer(canvas, doc):
    canvas.saveState()
    w, _ = A4
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#8A8F98"))
    canvas.drawString(doc.leftMargin, 10 * mm, "Angebots-KI – Quellcode & Erklärungen")
    canvas.drawRightString(w - doc.rightMargin, 10 * mm, f"Seite {doc.page}")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# PDF-Aufbau
# ---------------------------------------------------------------------------

def build() -> None:
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("title", parent=base["Title"], fontSize=24,
                                textColor=ACCENT, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontSize=12,
                                   textColor=colors.HexColor("#555555"), alignment=TA_CENTER),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontSize=15, textColor=ACCENT,
                             spaceBefore=2, spaceAfter=8),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontSize=11.5, textColor=ACCENT,
                             spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("body", parent=base["Normal"], fontSize=10, leading=14.5,
                               spaceAfter=6),
        "bullet": ParagraphStyle("bullet", parent=base["Normal"], fontSize=9.5, leading=13,
                                leftIndent=10, spaceAfter=2),
        "center": ParagraphStyle("center", parent=base["Normal"], fontSize=10.5,
                                 alignment=TA_CENTER, textColor=ACCENT, leading=15),
        "code": ParagraphStyle("code", parent=base["Normal"], fontName="Courier",
                               fontSize=7.5, leading=9.6, textColor=colors.black),
        "lineno": ParagraphStyle("lineno", parent=base["Normal"], fontName="Courier",
                                 fontSize=7, leading=9.6, alignment=2,
                                 textColor=colors.HexColor("#9AA0A6")),
    }

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
        title="Angebots-KI – Quellcode & Erklärungen",
    )
    code_width = doc.width

    story: list = []

    # --- Deckblatt ---
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("Angebots-KI", styles["title"]))
    story.append(Paragraph("Der komplette Quellcode – Schritt für Schritt erklärt", styles["subtitle"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(f"Stand: {date.today():%d.%m.%Y}", styles["subtitle"]))
    story.append(PageBreak())

    # --- Einleitung ---
    story.append(Paragraph("Was macht dieses Programm?", styles["h1"]))
    for p in INTRO:
        story.append(Paragraph(p, styles["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Wie alles zusammenspielt (vereinfacht):", styles["h2"]))
    story.append(Paragraph(FLOW, styles["center"]))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", color=LINE_COL))
    story.append(Spacer(1, 8))

    # --- Glossar ---
    story.append(Paragraph("Kleines Glossar (für Nicht-Techniker)", styles["h1"]))
    for term, desc in GLOSSARY:
        story.append(Paragraph(f"<b>{term}:</b> {desc}", styles["bullet"]))
    story.append(PageBreak())

    # --- Dateien ---
    for entry in FILES:
        path = ROOT / entry["path"]
        story.append(Paragraph(entry["title"], styles["h1"]))
        for p in entry["intro"]:
            story.append(Paragraph(p, styles["body"]))
        if entry["parts"]:
            story.append(Paragraph("Die wichtigsten Teile", styles["h2"]))
            for name, desc in entry["parts"]:
                story.append(Paragraph(f"• <b>{esc(name)}</b> — {esc(desc)}", styles["bullet"]))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Quellcode:</b> {entry['path']}", styles["h2"]))
        if path.exists():
            source = path.read_text(encoding="utf-8")
            story.append(code_table(source, styles["code"], styles["lineno"], code_width))
        else:
            story.append(Paragraph(f"(Datei nicht gefunden: {entry['path']})", styles["body"]))
        story.append(PageBreak())

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF erstellt: {OUT}")


if __name__ == "__main__":
    build()
