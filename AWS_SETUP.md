# Produktdaten & Vorlagen aus AWS S3 (Einrichtung von Grund auf)

Die App kann den Produktkatalog (CSV) und die Angebots-Vorlagen (PDF) aus einem
**privaten** Amazon-S3-Bucket laden. Zugriff erfolgt über einen IAM-Nutzer mit
**reinen Leserechten**; die Zugangsdaten liegen in den Streamlit-Secrets, nie im Code.

> Warum S3 und kein Server? S3 ist Objektspeicher für Dateien – nichts zu warten,
> Kosten im Cent-Bereich, sehr zuverlässig. Ein EC2-Server wäre hier unnötig.

---

## 1. AWS-Konto anlegen
<https://portal.aws.amazon.com/billing/signup> – Konto erstellen (Kreditkarte nötig,
Free Tier deckt diese Nutzung praktisch ab).

## 2. S3-Bucket erstellen
1. In der AWS-Konsole **S3** öffnen → **Create bucket**.
2. **Bucket name:** global eindeutig, z. B. `angebots-ki-<deinname>`.
3. **Region:** z. B. `eu-central-1` (Frankfurt) – merken, wird später gebraucht.
4. **Block Public Access:** **eingeschaltet lassen** (der Bucket bleibt privat).
5. **Create bucket**.

## 3. Ordner & Dateien hochladen
Im Bucket zwei „Ordner" (Präfixe) anlegen und Dateien hineinlegen:

- `produktdaten/`  → hier die Katalog-CSV(s), z. B. `produktkatalog.csv`
- `vorlagen/`      → hier die Vorlage-PDF(s), z. B. `standard_angebot.pdf`

Entweder per **Create folder** + **Upload** in der Konsole – oder bequem per Skript
(siehe Abschnitt 6).

## 4. IAM-Nutzer mit Leserechten anlegen
1. In der Konsole **IAM** → **Users** → **Create user** (z. B. `angebots-ki-reader`).
2. **Ohne** Konsolenzugang (nur programmatischer Zugriff).
3. **Permissions** → **Attach policies directly** → **Create policy** → Reiter **JSON**
   und folgende Richtlinie einfügen (Bucket-Namen anpassen, hier `angebots-ki-deinname`):

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "ListBucket",
         "Effect": "Allow",
         "Action": "s3:ListBucket",
         "Resource": "arn:aws:s3:::angebots-ki-deinname"
       },
       {
         "Sid": "ReadObjects",
         "Effect": "Allow",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::angebots-ki-deinname/*"
       }
     ]
   }
   ```

   Diese Richtlinie erlaubt **nur Lesen** aus genau diesem Bucket – nichts anderes.
4. Policy speichern, dem Nutzer zuweisen, Nutzer anlegen.

## 5. Zugangsschlüssel erzeugen
Nutzer öffnen → **Security credentials** → **Create access key** →
Anwendungsfall „Application running outside AWS". Es werden angezeigt:

- **Access key ID** (z. B. `AKIA…`)
- **Secret access key** (nur **einmal** sichtbar – sicher kopieren!)

## 6. (Optional) Beispieldaten per Skript hochladen
Lokal die Zugangsdaten in eine `.env` schreiben (siehe unten), dann:

```powershell
.\.venv\Scripts\python.exe -m pip install boto3
.\.venv\Scripts\python.exe scripts/upload_to_s3.py
```

Das lädt `sample_data/produktkatalog.csv` nach `produktdaten/` und – falls vorhanden –
`sample_data/beispiel_angebot_vorlage.pdf` nach `vorlagen/`.

## 7. Zugangsdaten hinterlegen

### Auf Streamlit Community Cloud
App → **Settings → Secrets** und ergänzen:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."

AWS_ACCESS_KEY_ID = "AKIA..."
AWS_SECRET_ACCESS_KEY = "..."
AWS_DEFAULT_REGION = "eu-central-1"
S3_BUCKET = "angebots-ki-deinname"
# optional, falls andere Ordnernamen:
# S3_CATALOG_PREFIX = "produktdaten/"
# S3_TEMPLATE_PREFIX = "vorlagen/"
```

### Lokal (Datei `.env`)
```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=eu-central-1
S3_BUCKET=angebots-ki-deinname
```

> Für schnelle Tests kannst du Bucket/Region/Schlüssel auch direkt in der
> **Seitenleiste** der App unter „AWS S3" eingeben.

## 8. Nutzung in der App
Nach dem Hinterlegen erscheint bei **Produktkatalog** und **Vorlage** jeweils die
Quelle **„AWS S3"**. Dort die gewünschte Datei aus dem Bucket auswählen – fertig.
Upload und Beispieldaten bleiben als Alternative erhalten.

---

## Sicherheit
- Bucket bleibt **privat** (Block Public Access an).
- IAM-Nutzer hat **nur Lesezugriff** auf genau diesen Bucket.
- Schlüssel nur in Secrets/`.env` – **niemals** committen (`.env` ist in `.gitignore`).
- Bei Verdacht auf Leck: in IAM den Access Key **deaktivieren/rotieren**.
