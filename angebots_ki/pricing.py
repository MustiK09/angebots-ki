"""Preisberechnung (autoritativ aus dem Katalog) und Zusammenbau des Endangebots."""

from __future__ import annotations

from .catalog import Catalog
from .config import Settings
from .models import (
    FinalOffer,
    OfferDraft,
    PricedLineItem,
    PricedOffer,
    RequestAnalysis,
)
from .utils import add_days_str, fmt_money, fmt_qty, make_offer_number, today_str


def price_offer(draft: OfferDraft, catalog: Catalog, settings: Settings) -> PricedOffer:
    """Setzt für jede Position den Katalogpreis ein und berechnet die Summen.

    Die KI liefert nur SKU + Menge + Texte; Preise kommen ausschließlich hier aus
    dem Katalog. So sind die Zahlen garantiert konsistent und nicht erfunden.
    """
    items: list[PricedLineItem] = []
    for pos, di in enumerate(draft.line_items, start=1):
        entry = catalog.lookup(di.sku)
        warning = None
        if entry is not None:
            sku = entry["sku"]
            name = entry["name"]
            unit_price = entry["unit_price"]
            unit = entry["unit"] or di.unit or "Stück"
            in_catalog = True
        else:
            sku = di.sku
            name = di.name or di.sku or "Position"
            unit_price = 0.0
            unit = di.unit or "Stück"
            in_catalog = False
            ref = di.sku or di.name or "unbekannt"
            warning = (
                f"Position {pos} ('{ref}') wurde nicht im Katalog gefunden – "
                f"Preis bitte manuell ergänzen."
            )

        quantity = float(di.quantity or 0)
        line_total = round(quantity * unit_price, 2)
        items.append(
            PricedLineItem(
                position=pos,
                sku=sku,
                name=name,
                description=di.description,
                quantity=quantity,
                unit=unit,
                unit_price=unit_price,
                line_total=line_total,
                in_catalog=in_catalog,
                warning=warning,
            )
        )

    subtotal = round(sum(i.line_total for i in items), 2)
    vat_amount = round(subtotal * settings.vat_rate, 2)
    total = round(subtotal + vat_amount, 2)
    return PricedOffer(line_items=items, subtotal=subtotal, vat_amount=vat_amount, total=total)


def render_priced_for_review(
    draft: OfferDraft,
    priced: PricedOffer,
    analysis: RequestAnalysis,
    settings: Settings,
) -> str:
    """Lesbare Textfassung des aktuellen Angebots für den Prüfschritt."""
    lines: list[str] = []
    lines.append(f"Titel: {draft.offer_title}")
    lines.append(f"\nEinleitung:\n{draft.intro_text}")
    lines.append("\nPositionen:")
    for it in priced.line_items:
        flag = "" if it.in_catalog else "  [NICHT IM KATALOG]"
        lines.append(
            f"  {it.position}. [{it.sku}] {it.name} – {it.description} | "
            f"Menge: {fmt_qty(it.quantity)} {it.unit} | "
            f"Einzelpreis: {fmt_money(it.unit_price, settings.currency)} | "
            f"Gesamt: {fmt_money(it.line_total, settings.currency)}{flag}"
        )
    lines.append(
        f"\nZwischensumme: {fmt_money(priced.subtotal, settings.currency)}"
        f"\nMwSt ({settings.vat_rate * 100:.0f}%): {fmt_money(priced.vat_amount, settings.currency)}"
        f"\nGesamtbetrag: {fmt_money(priced.total, settings.currency)}"
    )
    lines.append(f"\nAbschlusstext:\n{draft.closing_text}")
    lines.append(f"\nZahlungsbedingungen: {draft.payment_terms}")
    lines.append(f"Lieferbedingungen: {draft.delivery_terms}")
    lines.append(f"Gültigkeit: {draft.validity_days} Tage")
    return "\n".join(lines)


def assemble_final(
    analysis: RequestAnalysis,
    draft: OfferDraft,
    priced: PricedOffer,
    review_issues: list[str],
    settings: Settings,
) -> FinalOffer:
    """Baut aus Analyse, Entwurf und berechneten Preisen das finale Angebot."""
    warnings = [i.warning for i in priced.line_items if i.warning]
    validity = draft.validity_days or settings.default_validity_days
    title = draft.offer_title.strip() or "Angebot"
    return FinalOffer(
        offer_number=make_offer_number(),
        date=today_str(),
        valid_until=add_days_str(validity),
        customer=analysis.customer,
        title=title,
        intro_text=draft.intro_text,
        line_items=priced.line_items,
        closing_text=draft.closing_text,
        payment_terms=draft.payment_terms,
        delivery_terms=draft.delivery_terms,
        subtotal=priced.subtotal,
        vat_rate=settings.vat_rate,
        vat_amount=priced.vat_amount,
        total=priced.total,
        currency=settings.currency,
        warnings=warnings,
        review_issues=list(review_issues),
    )
