"""Fehlerklassen der Angebots-KI."""

from __future__ import annotations


class OfferGenerationError(Exception):
    """Wird ausgelöst, wenn die Angebotserstellung fehlschlägt.

    Die Nachricht ist für die Anzeige in der Oberfläche gedacht.
    """
