# Handoff – Angebots-KI

> Stand: 2026-06-16 · Zweck: Vollständiger Kontext, damit die Arbeit an diesem
> Projekt in einer späteren Sitzung nahtlos fortgesetzt werden kann.
> Sprache des Nutzers: **Deutsch** (Antworten, UI-Texte und Kommentare auf Deutsch).

---

## 1. Ziel des Projekts

Eine Python-Anwendung, die mit **Claude (Anthropic)** aus einer **Kunden-E-Mail
(Angebotsanfrage)** automatisch ein **Angebot als PDF** erstellt. Die KI:

1. liest und analysiert die Anfrage,
2. erstellt ein Angebot anhand eines **CSV-Produktkatalogs** und orientiert sich
   optional an einem **hochgeladenen Beispiel-Angebot (PDF)** als Stil-Vorlage,
3. **prüft das Ergebnis selbst** (Text und Artikelauswahl),
4. gibt am Ende ein **fertiges PDF** zum Download aus.

Bedienung über eine **Streamlit-Weboberfläche**.

---

## 2. Tech-Stack & getroffene Entscheidungen

- **UI:** Streamlit (vom Nutzer gewählt – passt zu „hochladen/herunterladen").
- **KI:** Anthropic Claude, Modell **`claude-opus-4-8`** (Default, in Seitenleiste änderbar).
- **PDF:** ReportLab (robust unter Windows, keine externen Systemabhängigkeiten).
- **PDF-Text lesen (Vorlage):** pypdf.
- **CSV:** pandas (von Streamlit ohnehin mitgebracht).
- **Strukturierte KI-Ausgaben:** `client.messages.parse(output_format=<PydanticModel>)`
  mit Fallback auf `messages.create(output_config={"format": {"type": "json_schema", …}})`
  für ältere SDKs (`_strictify` baut das Schema dafür um).
- **Adaptives Thinking:** `thinking={"type": "adaptive"}` für Entwurf + Prüfung
  (Analyse ohne Thinking, schneller). Per Checkbox abschaltbar.

### Zentrale Design-Entscheidung (wichtig!)
**Preise und Summen kommen IMMER aus dem Katalog und werden in Python gerechnet
(`pricing.py`).** Die KI liefert nur Artikel (per SKU), Mengen und Texte. So kann die
KI keine Preise erfinden; die Selbstprüfung konzentriert sich auf Artikelauswahl,
Vollständigkeit und Textqualität. Artikel, die der Kunde wünscht, die aber **nicht im
Katalog** sind, werden nicht als Position aufgenommen, sondern als Warnung
ausgewiesen und im Angebotstext erwähnt.

---

## 3. Projektstruktur

```
WAGP1/
├─ app.py                         # Streamlit-Oberfläche (Eingaben, Fortschritt, Ergebnis, Download)
├─ angebots_ki/
│  ├─ __init__.py                 # exportiert CompanyInfo, Settings, OfferGenerationError
│  ├─ config.py                   # DEFAULT_MODEL="claude-opus-4-8", CompanyInfo, Settings
│  ├─ errors.py                   # OfferGenerationError (für UI-Meldungen)
│  ├─ utils.py                    # Formatierung (fmt_money/fmt_qty), parse_price, PDF-Textextraktion, Datum, Angebotsnummer
│  ├─ models.py                   # Pydantic-Modelle (KI-I/O) + Dataclasses (PricedLineItem, FinalOffer, …)
│  ├─ catalog.py                  # Catalog.load(): tolerantes CSV-Mapping, lookup(sku), to_prompt_text()
│  ├─ claude_client.py            # AngebotsKI: analyze_request / draft_offer / review_offer (+ _structured)
│  ├─ pricing.py                  # price_offer() [autoritativ], render_priced_for_review(), assemble_final()
│  ├─ pdf_builder.py              # build_offer_pdf() → bytes (ReportLab)
│  └─ pipeline.py                 # generate_offer(): orchestriert den Gesamtablauf, OfferResult
├─ scripts/
│  └─ create_sample_template.py   # erzeugt sample_data/beispiel_angebot_vorlage.pdf
├─ sample_data/
│  ├─ produktkatalog.csv          # 18 Beispielartikel (akkuhydraulische Werkzeuge + Zubehör)
│  └─ beispiel_email.txt          # Beispiel-Angebotsanfrage (Industrieservice Westfalen GmbH)
├─ requirements.txt               # anthropic, streamlit, reportlab, pypdf, python-dotenv, pandas
├─ .env.example                   # Vorlage für ANTHROPIC_API_KEY
├─ README.md                      # ausführliche Doku
├─ SCHNELLSTART.md                # Kurzanleitung Start + Bedienung
└─ handoff.md                     # dieses Dokument
```

---

## 4. Datenfluss / Pipeline (`pipeline.generate_offer`)

```
E-Mail + Katalog + (Vorlage-PDF)
   │
   ├─ 1. analyze_request()  → RequestAnalysis (Kunde, Positionen)            [KI, ohne Thinking]
   ├─ 2. draft_offer()      → OfferDraft (SKUs, Mengen, Texte, KEINE Preise) [KI, adaptiv]
   ├─ 3. price_offer()      → PricedOffer (Preise/Summen aus Katalog)        [Python, autoritativ]
   ├─ 4. review_offer()     → ReviewResult (approved, issues, corrected)     [KI, adaptiv]
   │        └─ Schleife bis approved oder max_review_iterations; danach erneut price_offer()
   ├─ 5. assemble_final()   → FinalOffer (Nummer, Datum, gültig-bis, Summen)
   └─ 6. build_offer_pdf()  → PDF-Bytes  →  Download
```

Drei KI-Aufrufe pro Angebot bei `max_review_iterations=1` (Default).

---

## 5. Umgebung (Maschine des Nutzers)

- **OS:** Windows 10, Shell: **PowerShell**.
- Ursprünglich **kein nutzbares Python** (nur Microsoft-Store-Platzhalter).
- Nutzer hat inzwischen **Python installiert** und eine **venv unter `.venv\`** angelegt;
  `pip install -r requirements.txt` lief durch.
- venv-Python: `C:\Users\aydin\Desktop\WAGP1\.venv\Scripts\python.exe`
- Projektpfad: `C:\Users\aydin\Desktop\WAGP1`
- API-Key: noch zu setzen (Seitenleiste oder `.env`). Nutzer-E-Mail laut Umgebung:
  mustafa.k.kulakoglu@gmail.com.

---

## 6. Setup & Start

```powershell
cd C:\Users\aydin\Desktop\WAGP1
# venv aktiviert ((.venv) sichtbar):
streamlit run app.py
# oder ohne Aktivierung:
.\.venv\Scripts\python.exe -m streamlit run app.py
```
API-Key: `Copy-Item .env.example .env` → `ANTHROPIC_API_KEY=sk-ant-...` eintragen,
oder direkt in der Streamlit-Seitenleiste eingeben.

Beispiel-Vorlage erzeugen (optional): `python scripts/create_sample_template.py`

---

## 7. Verifizierungsstand

✅ **Geprüft und funktioniert:**
- `python -m compileall` über alle `.py` → keine Syntaxfehler.
- Import von `pipeline`, `claude_client`, `pdf_builder` → alle Module + Drittbibliotheken laden.
- Kompletter **Nicht-KI-Pfad** mit Beispieldaten: Katalog (14 Artikel) geladen,
  Spalten korrekt erkannt, `price_offer` rechnet korrekt
  (10×1.499 + 10×219 + 16×95 = 18.700 € netto, 3.553 € MwSt, 22.253 € gesamt),
  Warnung für Nicht-Katalog-Artikel erzeugt, gültiges **PDF** (`%PDF-`-Header) geschrieben.
- `fmt_money` liefert deutsches Format („1.499,00 €").

⏳ **Noch nicht getestet (braucht API-Key + Kosten):**
- Die drei echten Claude-Aufrufe (`analyze_request`, `draft_offer`, `review_offer`)
  über die Live-API. Erster echter End-to-End-Lauf steht noch aus.

Schnelle Re-Verifikation (ohne API):
```powershell
.\.venv\Scripts\python.exe -m compileall -q angebots_ki app.py scripts
.\.venv\Scripts\python.exe -c "import angebots_ki.pipeline; print('ok')"
```

---

## 8. Bekannte Stolpersteine (bereits gelöst / zu beachten)

1. **PowerShell-Ausführungsrichtlinie** blockierte `Activate.ps1`.
   Lösung: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
   (oder venv-Python direkt aufrufen, ohne Aktivierung).
2. **„source code string cannot contain null bytes"** beim Start.
   Ursache: In `utils.py` (Funktion `fmt_money`, Zeile 33) waren zwei Leerzeichen in
   `.replace(",", " ")` / `.replace(" ", ".")` zu Null-Bytes (`0x00`) geworden.
   Lösung: Null-Bytes wieder durch Leerzeichen ersetzt (Datei ist jetzt reines UTF-8).
   **Watch-out:** Falls erneut ein solcher Fehler kommt, mit Byte-Scan prüfen, welche
   `.py` betroffen ist, und Null-Bytes ersetzen / Datei sauber als UTF-8 neu schreiben.
3. **`€` erscheint in der PowerShell-Konsole als `�`** – reines Anzeigeproblem der
   Konsole, nicht in den Daten/im PDF.
4. **anthropic-SDK-Version:** `claude-opus-4-8` und strukturierte Outputs brauchen ein
   aktuelles SDK. Bei seltsamen API-Fehlern zuerst `pip install -U anthropic`.
   `claude_client._structured` hat einen Fallback, falls `messages.parse` fehlt.

---

## 9. Konfiguration (Streamlit-Seitenleiste → `Settings`)

- Modell (Default `claude-opus-4-8`), Währung, **MwSt-Satz** (Default 19 %),
  Gültigkeit (Tage), **max. Prüf-/Korrekturdurchläufe** (Default 1), adaptives Thinking an/aus.
- **Eigene Firmendaten** (`CompanyInfo`) für den Briefkopf des PDFs.

---

## 10. CSV-Katalogformat

Spalten werden tolerant erkannt (deutsch/englisch, Groß/Klein egal). Pflicht:
**Artikelnummer/SKU**, **Name**, **Preis**. Erkannt werden u. a. `Artikelnummer/SKU`,
`Name/Bezeichnung`, `Einzelpreis/Preis`, `Einheit`, `Beschreibung`, `Währung`.
**Alle übrigen Spalten** = Produktspezifikationen (gehen in `to_prompt_text` an die KI).
Trennzeichen (`, ; Tab`) und Preisformate (`1.299,00` / `1299.00`) werden automatisch erkannt.

---

## 11. Mögliche nächste Schritte / Ideen

- Erster echter API-Lauf und Feinschliff der Prompts (`claude_client.py`).
- Firmen-Logo im PDF-Briefkopf (`pdf_builder._footer` / Header).
- Mehrere Korrekturdurchläufe testen (`max_review_iterations` > 1).
- Optional: Angebotsnummer fortlaufend/persistiert statt zufällig (`utils.make_offer_number`).
- Optional: erkannte „open_questions" der Analyse stärker in der UI hervorheben.
- Optional: Export zusätzlich als DOCX, oder Versand-Funktion.

---

## 12. Wichtige Symbole/Einstiegspunkte (für schnelles Wiederfinden)

- Ablauf: `angebots_ki/pipeline.py` → `generate_offer()`
- KI-Prompts: `angebots_ki/claude_client.py` (System-Prompts je Schritt)
- Preislogik: `angebots_ki/pricing.py` → `price_offer()`
- PDF-Layout: `angebots_ki/pdf_builder.py` → `build_offer_pdf()`
- UI: `app.py` (`build_settings()`, `render_result()`)
