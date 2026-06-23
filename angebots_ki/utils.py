"""Hilfsfunktionen: Formatierung, Datumswerte, PDF-Textextraktion."""

from __future__ import annotations

import math
import random
import re
from datetime import date, timedelta
from typing import Any

_CURRENCY_SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF"}


def is_empty(value: Any) -> bool:
    """True für None, NaN oder leere/whitespace Strings."""
    if value is None:
        return True
    if isinstance(value, float):
        try:
            return math.isnan(value)
        except (TypeError, ValueError):
            return False
    return str(value).strip() == ""


def fmt_money(value: float, currency: str = "EUR") -> str:
    """Formatiert einen Betrag im deutschen Format, z. B. ``1.234,56 €``."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    # 1234567.89 -> "1,234,567.89" -> deutsches Format
    s = f"{value:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    symbol = _CURRENCY_SYMBOLS.get(currency.upper(), currency)
    return f"{s} {symbol}"


def fmt_qty(value: float) -> str:
    """Menge ohne unnötige Nachkommastellen (3 statt 3,00)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"
    if value == int(value):
        return str(int(value))
    return f"{value:.2f}".replace(".", ",")


def parse_price(value: Any) -> float:
    """Wandelt einen Preis-String robust in eine Zahl um.

    Versteht ``1.234,56``, ``1,234.56``, ``1234.56``, ``€ 99,90`` usw.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        try:
            return 0.0 if math.isnan(float(value)) else float(value)
        except (TypeError, ValueError):
            return 0.0

    s = re.sub(r"[^0-9.,-]", "", str(value))
    if not s:
        return 0.0

    has_comma, has_dot = "," in s, "." in s
    if has_comma and has_dot:
        # Das letzte Trennzeichen ist das Dezimaltrennzeichen.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif has_comma:
        # Komma ist Dezimaltrenner, wenn 1–2 Stellen folgen, sonst Tausender.
        if re.search(r",\d{1,2}$", s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def today_str() -> str:
    return date.today().strftime("%d.%m.%Y")


def add_days_str(days: int) -> str:
    return (date.today() + timedelta(days=int(days or 0))).strftime("%d.%m.%Y")


def make_offer_number() -> str:
    """Eindeutige Angebotsnummer, z. B. ``ANG-20260616-4821``."""
    return f"ANG-{date.today():%Y%m%d}-{random.randint(1000, 9999)}"


def extract_pdf_text(file_or_path: Any, max_chars: int = 12000) -> str:
    """Liest den Text aus einem (Beispiel-)PDF aus.

    ``file_or_path`` kann ein Pfad oder ein dateiähnliches Objekt sein.
    Bei Problemen wird ein leerer String zurückgegeben – die Vorlage ist optional.
    """
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover
        return ""

    try:
        reader = PdfReader(file_or_path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""

    text = text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…(gekürzt)…"
    return text
