"""Angebots-KI – KI-gestützte Erstellung von Angebotsdokumenten als PDF.

Das Paket liest eine Kunden-E-Mail (Angebotsanfrage), nutzt einen Produktkatalog
(CSV) und ein optionales Beispiel-Angebot (PDF) als Vorlage, lässt Claude ein
Angebot erstellen, dieses noch einmal selbst prüfen und gibt am Ende ein fertiges
PDF aus.

Wichtig: Preise und Summen stammen IMMER aus dem Katalog und werden in Python
berechnet – die KI wählt nur Artikel aus und formuliert die Texte.
"""

from .config import CompanyInfo, Settings
from .errors import OfferGenerationError

__all__ = ["CompanyInfo", "Settings", "OfferGenerationError"]
