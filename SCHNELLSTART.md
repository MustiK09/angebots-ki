# Schnellstart – Angebots-KI

## 1. API-Key hinterlegen (einmalig)

Entweder eine `.env`-Datei anlegen …

```powershell
Copy-Item .env.example .env
notepad .env
```

… und dort `ANTHROPIC_API_KEY=sk-ant-...` eintragen und speichern.
**Oder** den Key später direkt in der Oberfläche (linke Seitenleiste) einfügen.

## 2. Programm starten

```powershell
cd C:\Users\aydin\Desktop\WAGP1
```

Mit aktivierter venv (`(.venv)` steht vor der Zeile):

```powershell
streamlit run app.py
```

Ohne Aktivierung:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Der Browser öffnet sich automatisch unter `http://localhost:8501`.
**Beenden:** im PowerShell-Fenster `Strg + C`.

## 3. Angebot erstellen (im Browser)

1. **Produktkatalog (CSV)** – eigenen hochladen **oder** „Beispielkatalog verwenden" aktiviert lassen.
2. **Beispiel-Angebot (PDF)** – optional als Stil-Vorlage hochladen.
3. **Kundenanfrage** – E-Mail-Text einfügen **oder** „📨 Beispiel-Anfrage laden" klicken.
4. **🚀 Angebot erstellen** klicken und warten (KI analysiert → entwirft → prüft).
5. **⬇️ Angebot als PDF herunterladen.**

## 4. Was die KI macht

- Liest die Anfrage und erkennt Kunde + gewünschte Positionen.
- Wählt passende Artikel aus dem Katalog und formuliert die Texte.
- **Preise/Summen kommen immer aus dem Katalog** (werden in Python gerechnet, nicht von der KI).
- Prüft das Angebot anschließend selbst; Hinweise erscheinen über dem Ergebnis.

## Einstellungen (Seitenleiste)

Modell, Währung, MwSt-Satz, Gültigkeit, Anzahl Prüfdurchläufe und eigene Firmendaten
(Briefkopf des PDFs) lassen sich dort anpassen.
