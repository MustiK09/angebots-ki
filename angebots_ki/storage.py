"""Optionaler Zugriff auf Produktdaten und Vorlagen in einem privaten AWS-S3-Bucket.

Die Anbindung ist bewusst optional: Ist kein Bucket/keine Zugangsdaten gesetzt (oder
boto3 nicht installiert), meldet ``is_configured()`` False und die App nutzt weiter
den Datei-Upload bzw. die lokalen Beispieldaten.

Konfiguration ausschließlich über Umgebungsvariablen (auf Streamlit Community Cloud
aus den Secrets gespiegelt):

    AWS_ACCESS_KEY_ID       Zugangsschlüssel des IAM-Nutzers
    AWS_SECRET_ACCESS_KEY   geheimer Schlüssel des IAM-Nutzers
    AWS_DEFAULT_REGION      z. B. eu-central-1
    S3_BUCKET               Name des Buckets
    S3_CATALOG_PREFIX       Ordner für Kataloge (Standard: produktdaten/)
    S3_TEMPLATE_PREFIX      Ordner für Vorlagen (Standard: vorlagen/)
"""

from __future__ import annotations

import os

from .errors import OfferGenerationError


def _config() -> dict:
    return {
        "bucket": os.getenv("S3_BUCKET", "").strip(),
        "region": (os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "").strip(),
        "catalog_prefix": os.getenv("S3_CATALOG_PREFIX", "produktdaten/").strip(),
        "template_prefix": os.getenv("S3_TEMPLATE_PREFIX", "vorlagen/").strip(),
    }


def catalog_prefix() -> str:
    return _config()["catalog_prefix"]


def template_prefix() -> str:
    return _config()["template_prefix"]


def _boto3_available() -> bool:
    try:
        import boto3  # noqa: F401
        return True
    except Exception:
        return False


def is_configured() -> bool:
    """True, wenn Bucket + Zugangsdaten vorhanden sind und boto3 installiert ist."""
    cfg = _config()
    has_creds = bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
    return bool(cfg["bucket"]) and has_creds and _boto3_available()


class S3Store:
    """Dünne Hülle um boto3 für Auflisten und Herunterladen von Objekten."""

    def __init__(self) -> None:
        try:
            import boto3
        except ImportError as exc:  # pragma: no cover
            raise OfferGenerationError(
                "Das Paket 'boto3' ist nicht installiert. Bitte 'pip install boto3' ausführen."
            ) from exc

        cfg = _config()
        if not cfg["bucket"]:
            raise OfferGenerationError("Kein S3-Bucket konfiguriert (S3_BUCKET fehlt).")

        self.bucket = cfg["bucket"]
        client_kwargs = {}
        if cfg["region"]:
            client_kwargs["region_name"] = cfg["region"]
        self.client = boto3.client("s3", **client_kwargs)

    def list_files(self, prefix: str, extensions: tuple = ()) -> list:
        """Listet Objekt-Schlüssel unter ``prefix`` (optional nach Endung gefiltert)."""
        keys: list[str] = []
        try:
            paginator = self.client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key.endswith("/"):
                        continue  # Ordner-Platzhalter überspringen
                    if extensions and not key.lower().endswith(tuple(extensions)):
                        continue
                    keys.append(key)
        except Exception as exc:
            raise OfferGenerationError(
                f"AWS S3: Auflisten fehlgeschlagen ({exc}). Bucket-Name, Region und "
                f"Zugangsdaten prüfen."
            ) from exc
        return sorted(keys)

    def get_bytes(self, key: str) -> bytes:
        """Lädt den Inhalt eines Objekts als Bytes herunter."""
        try:
            resp = self.client.get_object(Bucket=self.bucket, Key=key)
            return resp["Body"].read()
        except Exception as exc:
            raise OfferGenerationError(
                f"AWS S3: Datei '{key}' konnte nicht geladen werden ({exc})."
            ) from exc
