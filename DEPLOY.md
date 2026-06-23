# Deployment auf Streamlit Community Cloud

Damit läuft die App unter einer **öffentlichen URL** – du brauchst zur Präsentation
nur einen Browser, dein Desktop muss **nicht** an sein.

## Voraussetzungen
- **GitHub-Konto** (kostenlos): <https://github.com/signup>
- **Anthropic API-Key** (für die KI-Aufrufe)

---

## Schritt 1 – Code zu GitHub bringen

Das lokale Git-Repository ist **bereits angelegt und committet** (siehe unten).
Du musst nur noch ein leeres Repo auf GitHub erstellen und hochladen.

1. Auf <https://github.com/new> ein **neues, leeres** Repository anlegen
   (Name z. B. `angebots-ki`). **Kein** README/.gitignore/License anhaken
   (haben wir schon). Sichtbarkeit *privat* ist ok – Streamlit Cloud kann auch
   private Repos deployen.
2. GitHub zeigt dir die Repo-URL. Im Projektordner ausführen:

```powershell
cd C:\Users\aydin\Desktop\WAGP1
git remote add origin https://github.com/<DEIN-NAME>/angebots-ki.git
git push -u origin main
```

Beim ersten Push öffnet sich ein Browser-Fenster zur GitHub-Anmeldung
(Git Credential Manager) – einmal anmelden, fertig.

---

## Schritt 2 – App auf Streamlit Cloud deployen

1. <https://share.streamlit.io> öffnen → **Continue with GitHub** → Zugriff erlauben.
2. **Create app** → **Deploy a public app from GitHub**.
3. Felder ausfüllen:
   - **Repository:** `<DEIN-NAME>/angebots-ki`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. **Advanced settings**:
   - **Python version:** `3.12`
   - **Secrets:** folgenden Inhalt einfügen (mit deinen echten Werten):
     ```toml
     ANTHROPIC_API_KEY = "sk-ant-..."
     APP_PASSWORD = "dein-demo-passwort"
     ```
     (`APP_PASSWORD` ist optional – schützt die öffentliche URL. Weglassen = offen.)
5. **Deploy** klicken. Nach 1–3 Minuten ist die App unter einer URL wie
   `https://<name>.streamlit.app` erreichbar.

> Secrets später ändern: App-Seite → **⋮ / Manage app → Settings → Secrets**.

---

## Schritt 3 – Sicherheit & Kosten (wichtig bei öffentlicher URL)

- **Passwortschutz aktivieren:** `APP_PASSWORD` als Secret setzen (s. o.). So kann
  niemand Fremdes dein API-Guthaben verbrauchen. Alternativ in den App-Einstellungen
  unter **Sharing** die Sichtbarkeit auf bestimmte Personen beschränken.
- **Anthropic-Ausgabenlimit** im Console-Dashboard setzen und am besten einen
  **eigenen Key nur für die Demo** verwenden – nach der Präsentation einfach löschen/rotieren.
- **Den Key niemals committen.** Er gehört ausschließlich in die Streamlit-Secrets
  (`.env` und `.streamlit/secrets.toml` sind in `.gitignore` ausgeschlossen).
- Kosten pro Angebot sind gering (wenige Cent bis ~30 ct je Lauf, je nach Katalog/Länge).

---

## Updates veröffentlichen

Einfach Änderungen committen und pushen – die Cloud baut automatisch neu:

```powershell
git add -A
git commit -m "Update"
git push
```

---

## Tipps für die Präsentation

- **Vorher aufwecken:** Community-Cloud-Apps gehen bei Inaktivität in den
  Ruhezustand. Öffne die URL **einige Minuten vor** deinem Vortrag einmal, damit sie
  wach und schnell ist.
- **Schneller Demo-Ablauf:** „Beispielkatalog verwenden" + Beispiel-Anfrage einfügen
  + „Angebot erstellen". (Für die Werkzeug-Variante: `produktkatalog_akkuhydraulik.csv`
  hochladen und Text aus `beispiel_email_akkuhydraulik.txt` einfügen.)
- **Backup einplanen:** Erzeuge vorab **ein fertiges Angebots-PDF** und mach ein paar
  **Screenshots / eine kurze Bildschirmaufnahme**. Falls Uni-WLAN oder API zicken,
  hast du trotzdem etwas zu zeigen.

---

## Fehlerbehebung

- **Build/Start schlägt fehl:** In der App rechts unten **„Manage app" → Logs** ansehen.
- **`ModuleNotFoundError`:** Paket fehlt in `requirements.txt`.
- **KI-Fehler / „Anmeldung fehlgeschlagen":** `ANTHROPIC_API_KEY` als Secret gesetzt?
  Stimmt der Key? Ausgabenlimit erreicht?
- **Falsches Passwort-Loop:** `APP_PASSWORD`-Secret prüfen (Groß-/Kleinschreibung).
