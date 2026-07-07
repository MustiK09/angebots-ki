"""Lädt die lokalen Beispieldaten in den S3-Bucket hoch (einmalige Erstbefüllung).

Voraussetzung: Umgebungsvariablen AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
AWS_DEFAULT_REGION und S3_BUCKET sind gesetzt (z. B. über eine .env-Datei).

Aufruf:  python scripts/upload_to_s3.py

Lädt hoch:
  sample_data/produktkatalog.csv            -> <S3_CATALOG_PREFIX>produktkatalog.csv
  sample_data/beispiel_angebot_vorlage.pdf  -> <S3_TEMPLATE_PREFIX>standard_angebot.pdf  (falls vorhanden)
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "sample_data"

CATALOG_PREFIX = os.getenv("S3_CATALOG_PREFIX", "produktdaten/")
TEMPLATE_PREFIX = os.getenv("S3_TEMPLATE_PREFIX", "vorlagen/")


def main() -> None:
    bucket = os.getenv("S3_BUCKET", "").strip()
    if not bucket:
        raise SystemExit("Fehler: S3_BUCKET ist nicht gesetzt (z. B. in .env).")
    if not (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")):
        raise SystemExit("Fehler: AWS-Zugangsdaten fehlen (AWS_ACCESS_KEY_ID/SECRET).")

    try:
        import boto3
    except ImportError:
        raise SystemExit("Fehler: boto3 nicht installiert. Bitte 'pip install boto3'.")

    region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION")
    client = boto3.client("s3", **({"region_name": region} if region else {}))

    uploads = [
        (SAMPLE / "produktkatalog.csv", CATALOG_PREFIX + "produktkatalog.csv", "text/csv"),
    ]
    template = SAMPLE / "beispiel_angebot_vorlage.pdf"
    if template.exists():
        uploads.append((template, TEMPLATE_PREFIX + "standard_angebot.pdf", "application/pdf"))

    for path, key, content_type in uploads:
        if not path.exists():
            print(f"Übersprungen (nicht gefunden): {path.name}")
            continue
        client.upload_file(
            str(path), bucket, key,
            ExtraArgs={"ContentType": content_type},
        )
        print(f"Hochgeladen: {path.name}  ->  s3://{bucket}/{key}")

    print("\nFertig. Tipp: Weitere Kataloge/Vorlagen kannst du direkt in der "
          "AWS-Konsole in die Ordner "
          f"'{CATALOG_PREFIX}' bzw. '{TEMPLATE_PREFIX}' hochladen.")


if __name__ == "__main__":
    main()
