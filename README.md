# Angebots-KI 📄

Eine Python-Anwendung, die mit **Claude (Anthropic)** aus einer **Kunden-E-Mail**
automatisch ein **Angebotsdokument als PDF** erstellt. Die KI orientiert sich dabei
an einem **hochgeladenen Beispiel-Angebot (PDF)** und wählt Produkte aus einem
**CSV-Produktkatalog**. Bevor das PDF ausgegeben wird, **prüft die KI ihr eigenes
Angebot** noch einmal auf Vollständigkeit, passende Artikel und Textqualität.

Bedienung über eine **Streamlit-Weboberfläche** (Datei-Upload + Download-Button).

---

## Ablauf

```
Kunden-E-Mail ─┐
Produktkatalog ─┤→ 1. Anfrage analysieren (KI)
Beispiel-PDF ───┘      ↓
                  2. Angebot entwerfen (KI wählt Artikel per SKU + schreibt Texte)
                       ↓
                  3. Preise & Summen aus dem Katalog berechnen (Python, autoritativ)
                       ↓
                  4. Selbstprüfung (KI prüft Auswahl, Vollständigkeit, Text)
                       ↓
                  5. PDF erzeugen  →  Download
```

**Wichtig:** Preise und Summen werden **immer aus dem Katalog in Python berechnet** –
die KI legt nur Artikelauswahl, Mengen und Texte fest. Dadurch kann die KI keine
Preise erfinden, und die Zahlen sind garantiert konsistent.

---

## Voraussetzungen

### 1. Python installieren

Auf diesem Rechner ist aktuell **kein nutzbares Python** installiert (nur der
Microsoft-Store-Platzhalter). Installiere zunächst **Python 3.10 oder neuer**:

- Von <https://www.python.org/downloads/> herunterladen und installieren.
- Beim Setup unbedingt **„Add python.exe to PATH"** anhaken.
- PowerShell **neu öffnen** und prüfen:

```powershell
python --version
```

### 2. Anthropic API-Key

Einen API-Key unter <https://platform.claude.com> (Console) erstellen.

---

## Installation

```powershell
# in das Projektverzeichnis wechseln
cd C:\Users\aydin\Desktop\WAGP1

# virtuelle Umgebung anlegen und aktivieren
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install -r requirements.txt
```

> Falls `Activate.ps1` durch die Ausführungsrichtlinie blockiert wird:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### API-Key hinterlegen

Entweder `.env.example` nach `.env` kopieren und den Key eintragen …

```powershell
Copy-Item .env.example .env
# .env öffnen und ANTHROPIC_API_KEY=... eintragen
```

… oder den Key direkt in der Oberfläche (Seitenleiste) eingeben.

---

## Starten

```powershell
streamlit run app.py
```

Es öffnet sich automatisch der Browser (sonst die angezeigte URL aufrufen).

1. **Produktkatalog (CSV)** hochladen – oder „Beispielkatalog verwenden" aktiviert lassen.
2. Optional ein **Beispiel-Angebot (PDF)** als Vorlage hochladen.
3. **Kundenanfrage** einfügen – oder „Beispiel-Anfrage laden" klicken.
4. **🚀 Angebot erstellen** – am Ende das **PDF herunterladen**.

### Beispiel-Vorlage erzeugen (optional)

Ein einfaches Beispiel-Angebot als PDF zum Testen des Vorlagen-Uploads erstellen:

```powershell
python scripts/create_sample_template.py
# erzeugt sample_data/beispiel_angebot_vorlage.pdf
```

---

## Eigener Produktkatalog (CSV-Format)

Die Spaltenüberschriften werden flexibel erkannt (deutsch/englisch, Groß-/Kleinschreibung
egal). Erforderlich sind mindestens **Artikelnummer**, **Name** und **Preis**:

| Zweck | Erkannte Spaltennamen (Auswahl) |
|---|---|
| Artikelnummer | `Artikelnummer`, `Art.-Nr.`, `SKU`, `Nummer`, `ID` |
| Name | `Name`, `Bezeichnung`, `Produkt`, `Artikel` |
| Preis (netto) | `Einzelpreis`, `Preis`, `Stückpreis`, `Nettopreis`, `price` |
| Einheit | `Einheit`, `unit`, `Mengeneinheit` |
| Beschreibung | `Beschreibung`, `description`, `Details` |

Alle **weiteren Spalten** werden automatisch als **Produktspezifikationen** behandelt
(z. B. `cpu`, `ram_gb`, `display_inch`) und der KI für die Artikelauswahl mitgegeben.

Trennzeichen (`,` `;` Tab) und Preisformate (`1.299,00` oder `1299.00`) werden
automatisch erkannt. Ein vollständiges Beispiel: [`sample_data/produktkatalog.csv`](sample_data/produktkatalog.csv).

---

## Projektstruktur

```
WAGP1/
├─ app.py                     # Streamlit-Oberfläche
├─ angebots_ki/
│  ├─ config.py               # Modell, Firmendaten, Steuersatz
│  ├─ catalog.py              # CSV-Katalog laden & aufbereiten
│  ├─ models.py               # Datenmodelle (Pydantic + Dataclasses)
│  ├─ claude_client.py        # KI-Aufrufe: analysieren / entwerfen / prüfen
│  ├─ pricing.py              # Preisberechnung (autoritativ) + Zusammenbau
│  ├─ pdf_builder.py          # PDF-Erzeugung (ReportLab)
│  └─ pipeline.py             # Gesamtablauf
├─ scripts/
│  └─ create_sample_template.py
├─ sample_data/
│  ├─ produktkatalog.csv
│  └─ beispiel_email.txt
├─ requirements.txt
└─ .env.example
```

---

## Einstellungen (Seitenleiste)

- **Modell** (Standard `claude-opus-4-8`), **Währung**, **MwSt-Satz**, **Gültigkeit**.
- **Max. Prüf-/Korrekturdurchläufe**: Wie oft die KI das Angebot prüft und überarbeitet
  (mind. 1 Durchlauf).
- **Eigene Firmendaten** für den Briefkopf des PDFs.

---

## Hinweise

- Artikel, die der Kunde anfragt, **die nicht im Katalog stehen**, werden nicht als
  Position aufgenommen, sondern im Angebotstext transparent erwähnt und in der
  Oberfläche als Hinweis angezeigt.
- Kosten/Latenz entstehen durch mehrere Claude-Aufrufe pro Angebot (Analyse, Entwurf,
  Prüfung). Mit „Max. Prüfdurchläufe = 1" bleibt es bei drei Aufrufen.
- Es werden keine Daten dauerhaft gespeichert; alles läuft lokal bzw. über die
  Anthropic-API.
