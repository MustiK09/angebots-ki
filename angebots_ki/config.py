"""Konfiguration: Modell, Firmendaten, Steuersatz usw."""

from __future__ import annotations

from dataclasses import dataclass, field

# Aktuelles, leistungsfähigstes Claude-Modell (Stand der claude-api-Referenz).
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass
class CompanyInfo:
    """Daten des eigenen Unternehmens, die im Angebot erscheinen."""

    name: str = "Muster GmbH"
    address_lines: list[str] = field(
        default_factory=lambda: ["Musterstraße 1", "12345 Musterstadt", "Deutschland"]
    )
    phone: str = "+49 30 1234567"
    email: str = "vertrieb@muster-gmbh.de"
    website: str = "www.muster-gmbh.de"
    tax_id: str = "USt-IdNr. DE123456789"
    bank: str = "Muster Bank · IBAN DE00 0000 0000 0000 0000 00 · BIC XXXXDEXX"

    def address_block(self) -> str:
        """Mehrzeiliger Adressblock für den Briefkopf."""
        return "\n".join([self.name, *self.address_lines])


@dataclass
class Settings:
    """Allgemeine Einstellungen für einen Angebotslauf."""

    model: str = DEFAULT_MODEL
    currency: str = "EUR"
    vat_rate: float = 0.19
    default_validity_days: int = 30
    # Wie oft die KI höchstens eine Korrekturschleife dreht (mind. 1 Prüflauf).
    max_review_iterations: int = 1
    # Adaptives Thinking für die anspruchsvollen Schritte (Entwurf/Prüfung).
    use_thinking: bool = True
    company: CompanyInfo = field(default_factory=CompanyInfo)
