"""Laden und Aufbereiten des Produktkatalogs (CSV)."""

from __future__ import annotations

import io
from typing import Any, Optional

import pandas as pd

from .errors import OfferGenerationError
from .utils import fmt_money, is_empty, parse_price

# Mögliche Spaltennamen (klein geschrieben) je Feld – das erste Treffer-Feld gewinnt.
_COLUMN_CANDIDATES = {
    "sku": [
        "sku", "artikelnummer", "artikel-nr", "artikelnr", "art-nr", "artnr",
        "art.-nr.", "artikel_nr", "nummer", "id",
    ],
    "name": ["name", "bezeichnung", "produkt", "produktname", "artikel", "titel"],
    "price": [
        "einzelpreis", "stückpreis", "stueckpreis", "preis", "price", "nettopreis",
        "netto", "unit_price", "listenpreis", "vk",
    ],
    "unit": ["einheit", "unit", "mengeneinheit", "me"],
    "description": ["beschreibung", "description", "details", "spezifikation", "info"],
    "currency": ["währung", "waehrung", "currency"],
}


def _pick_column(columns: list[str], candidates: list[str]) -> Optional[str]:
    lower = {c.lower().strip(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


class Catalog:
    """Produktkatalog mit tolerantem Spalten-Mapping und Lookup per SKU."""

    def __init__(self, df: pd.DataFrame):
        cols = list(df.columns)
        self.col_sku = _pick_column(cols, _COLUMN_CANDIDATES["sku"])
        self.col_name = _pick_column(cols, _COLUMN_CANDIDATES["name"])
        self.col_price = _pick_column(cols, _COLUMN_CANDIDATES["price"])
        self.col_unit = _pick_column(cols, _COLUMN_CANDIDATES["unit"])
        self.col_desc = _pick_column(cols, _COLUMN_CANDIDATES["description"])
        self.col_currency = _pick_column(cols, _COLUMN_CANDIDATES["currency"])

        if not self.col_sku or not self.col_name or not self.col_price:
            raise OfferGenerationError(
                "Im Katalog fehlt eine erkennbare Spalte für Artikelnummer, Name "
                "oder Preis. Erwartet werden z. B. 'Artikelnummer', 'Name', 'Preis'."
            )

        self.df = df.copy()
        # Alle Spalten, die nicht bereits belegt sind, gelten als Spezifikationen.
        used = {
            self.col_sku, self.col_name, self.col_price, self.col_unit,
            self.col_desc, self.col_currency,
        }
        self.spec_cols = [c for c in cols if c not in used]

        # Währung aus den Daten ableiten, sonst EUR.
        self.currency = "EUR"
        if self.col_currency:
            vals = [str(v).strip() for v in self.df[self.col_currency] if not is_empty(v)]
            if vals:
                self.currency = vals[0].upper()

        # Schneller Lookup-Index per SKU (als String, getrimmt).
        self._index: dict[str, int] = {}
        for pos, value in self.df[self.col_sku].items():
            if not is_empty(value):
                self._index[str(value).strip()] = pos

    # -- Laden -------------------------------------------------------------

    @classmethod
    def load(cls, file_or_path: Any) -> "Catalog":
        """Lädt eine CSV (Pfad oder dateiähnliches Objekt) mit Trennzeichen-Erkennung."""
        # Bytes für mehrfaches Lesen puffern (UploadedFile wird sonst leer gelesen).
        if hasattr(file_or_path, "read"):
            raw = file_or_path.read()
            if isinstance(raw, str):
                raw = raw.encode("utf-8")
            buffer: Any = io.BytesIO(raw)
        else:
            buffer = file_or_path

        last_error: Optional[Exception] = None
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                if hasattr(buffer, "seek"):
                    buffer.seek(0)
                # sep=None + engine="python" erkennt , ; oder Tab automatisch.
                df = pd.read_csv(buffer, sep=None, engine="python", dtype=str,
                                 encoding=encoding, keep_default_na=False)
                if df.shape[1] >= 2:
                    return cls(df)
            except Exception as exc:  # nächste Kodierung versuchen
                last_error = exc

        raise OfferGenerationError(
            f"Der Produktkatalog konnte nicht gelesen werden: {last_error}"
        )

    # -- Zugriff -----------------------------------------------------------

    def __len__(self) -> int:
        return len(self.df)

    def _price_of(self, row: pd.Series) -> float:
        return round(parse_price(row[self.col_price]), 2)

    def _unit_of(self, row: pd.Series) -> str:
        if self.col_unit and not is_empty(row[self.col_unit]):
            return str(row[self.col_unit]).strip()
        return "Stück"

    def lookup(self, sku: str) -> Optional[dict]:
        """Liefert die Katalogdaten zu einer SKU oder None."""
        if is_empty(sku):
            return None
        pos = self._index.get(str(sku).strip())
        if pos is None:
            return None
        row = self.df.loc[pos]
        specs = {
            c: str(row[c]).strip()
            for c in self.spec_cols
            if not is_empty(row[c])
        }
        return {
            "sku": str(row[self.col_sku]).strip(),
            "name": str(row[self.col_name]).strip(),
            "unit_price": self._price_of(row),
            "unit": self._unit_of(row),
            "description": "" if not self.col_desc else str(row[self.col_desc]).strip(),
            "specs": specs,
        }

    def to_prompt_text(self) -> str:
        """Kompakte Textdarstellung des gesamten Katalogs für die KI."""
        lines: list[str] = []
        for _, row in self.df.iterrows():
            if is_empty(row[self.col_sku]):
                continue
            parts = [
                f"SKU: {str(row[self.col_sku]).strip()}",
                f"Name: {str(row[self.col_name]).strip()}",
                f"Preis: {fmt_money(self._price_of(row), self.currency)} / {self._unit_of(row)}",
            ]
            if self.col_desc and not is_empty(row[self.col_desc]):
                parts.append(f"Beschreibung: {str(row[self.col_desc]).strip()}")
            specs = [
                f"{c}={str(row[c]).strip()}"
                for c in self.spec_cols
                if not is_empty(row[c])
            ]
            if specs:
                parts.append("Spezifikationen: " + ", ".join(specs))
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    def preview_df(self) -> pd.DataFrame:
        """DataFrame für die Vorschau in der Oberfläche."""
        return self.df
