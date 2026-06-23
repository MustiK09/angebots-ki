"""Datenmodelle für KI-Ein-/Ausgabe (Pydantic) und interne Strukturen (Dataclasses).

Hinweis zu strukturierten Outputs: Alle Pydantic-Felder sind verpflichtend (keine
Optionals). Unbekannte Werte trägt die KI als leeren String, 0 oder leere Liste ein.
Das hält das JSON-Schema einfach und kompatibel zu den strukturierten Outputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1) Analyse der Kundenanfrage
# ---------------------------------------------------------------------------


class CustomerInfo(BaseModel):
    company: str = Field(description="Firmenname des Kunden; leer, wenn unbekannt")
    contact_name: str = Field(description="Ansprechpartner/in; leer, wenn unbekannt")
    email: str = Field(description="E-Mail-Adresse; leer, wenn unbekannt")
    phone: str = Field(description="Telefonnummer; leer, wenn unbekannt")
    address: str = Field(
        description="Vollständige Anschrift, Zeilen mit \\n getrennt; leer, wenn unbekannt"
    )


class RequestedItem(BaseModel):
    description: str = Field(description="Was der Kunde angefragt hat")
    quantity: float = Field(description="Angefragte Menge; 0, wenn nicht genannt")
    unit: str = Field(description="Einheit, z. B. 'Stück', 'Stunden'; leer, wenn unklar")
    notes: str = Field(description="Zusätzliche Hinweise/Anforderungen; leer, wenn keine")


class RequestAnalysis(BaseModel):
    customer: CustomerInfo
    items: list[RequestedItem]
    desired_deadline: str = Field(description="Gewünschter Liefer-/Antworttermin; leer, wenn keiner")
    summary: str = Field(description="Kurze Zusammenfassung der Anfrage in 1–2 Sätzen")
    open_questions: list[str] = Field(
        description="Unklarheiten/offene Punkte, die ein Vertriebler klären würde"
    )


# ---------------------------------------------------------------------------
# 2) Angebotsentwurf (Text + Artikelauswahl – OHNE Preise)
# ---------------------------------------------------------------------------


class DraftLineItem(BaseModel):
    sku: str = Field(
        description="Artikelnummer (SKU) aus dem Katalog. Leer lassen, wenn kein "
        "passender Katalogartikel existiert."
    )
    name: str = Field(
        description="Produktname. Bei Katalogartikeln der Katalogname, sonst Freitext."
    )
    description: str = Field(description="Auf den Kunden zugeschnittene Positionsbeschreibung")
    quantity: float = Field(description="Menge für diese Position")
    unit: str = Field(description="Einheit, z. B. 'Stück'")


class OfferDraft(BaseModel):
    offer_title: str = Field(description="Titel/Betreff des Angebots")
    intro_text: str = Field(description="Einleitender Text (Anrede + Bezug zur Anfrage)")
    line_items: list[DraftLineItem]
    closing_text: str = Field(
        description="Abschlusstext (Mehrwert, nächste Schritte, Hinweise zu nicht "
        "lieferbaren Wünschen)"
    )
    payment_terms: str = Field(description="Zahlungsbedingungen")
    delivery_terms: str = Field(description="Liefer-/Leistungsbedingungen")
    validity_days: int = Field(description="Gültigkeit des Angebots in Tagen, z. B. 30")


# ---------------------------------------------------------------------------
# 3) Selbstprüfung
# ---------------------------------------------------------------------------


class ReviewResult(BaseModel):
    approved: bool = Field(description="True, wenn keine wesentlichen Probleme bestehen")
    issues: list[str] = Field(description="Gefundene Probleme/Hinweise; leer, wenn keine")
    corrected_offer: OfferDraft = Field(
        description="Verbesserte Fassung des Angebots (bei approved=true nahezu identisch)"
    )


# ---------------------------------------------------------------------------
# Interne Strukturen mit berechneten Preisen (autoritativ aus dem Katalog)
# ---------------------------------------------------------------------------


@dataclass
class PricedLineItem:
    position: int
    sku: str
    name: str
    description: str
    quantity: float
    unit: str
    unit_price: float
    line_total: float
    in_catalog: bool
    warning: Optional[str] = None


@dataclass
class PricedOffer:
    line_items: list[PricedLineItem]
    subtotal: float
    vat_amount: float
    total: float


@dataclass
class FinalOffer:
    offer_number: str
    date: str
    valid_until: str
    customer: CustomerInfo
    title: str
    intro_text: str
    line_items: list[PricedLineItem]
    closing_text: str
    payment_terms: str
    delivery_terms: str
    subtotal: float
    vat_rate: float
    vat_amount: float
    total: float
    currency: str
    warnings: list[str] = field(default_factory=list)
    review_issues: list[str] = field(default_factory=list)
