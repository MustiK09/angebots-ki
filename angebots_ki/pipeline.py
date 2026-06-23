"""Orchestrierung: E-Mail -> Analyse -> Entwurf -> Preise -> Selbstprüfung -> PDF."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .catalog import Catalog
from .claude_client import AngebotsKI
from .config import Settings
from .models import FinalOffer, OfferDraft, RequestAnalysis
from .pdf_builder import build_offer_pdf
from .pricing import assemble_final, price_offer, render_priced_for_review

ProgressCallback = Optional[Callable[[str], None]]


@dataclass
class OfferResult:
    final: FinalOffer
    pdf_bytes: bytes
    analysis: RequestAnalysis
    draft: OfferDraft


def generate_offer(
    *,
    email_text: str,
    catalog: Catalog,
    template_text: str,
    ki: AngebotsKI,
    settings: Settings,
    progress: ProgressCallback = None,
) -> OfferResult:
    """Führt den kompletten Ablauf aus und liefert Angebot + PDF.

    ``progress`` wird (falls gesetzt) mit kurzen Statusmeldungen aufgerufen.
    """

    def step(msg: str) -> None:
        if progress:
            progress(msg)

    if not email_text.strip():
        from .errors import OfferGenerationError

        raise OfferGenerationError("Bitte zuerst den Text der Kundenanfrage einfügen.")

    step("Analysiere die Kundenanfrage …")
    analysis = ki.analyze_request(email_text, catalog)

    step("Erstelle den Angebotsentwurf …")
    draft = ki.draft_offer(analysis, catalog, template_text)
    priced = price_offer(draft, catalog, settings)

    review_issues: list[str] = []
    iterations = max(1, settings.max_review_iterations)
    for n in range(iterations):
        step(f"Prüfe Text und Daten (Durchlauf {n + 1}/{iterations}) …")
        review_text = render_priced_for_review(draft, priced, analysis, settings)
        review = ki.review_offer(review_text, analysis, catalog, template_text)
        review_issues = review.issues
        # Verbesserte Fassung übernehmen; Preise bleiben durch erneutes Pricing autoritativ.
        draft = review.corrected_offer
        priced = price_offer(draft, catalog, settings)
        if review.approved:
            break

    step("Erzeuge das PDF …")
    final = assemble_final(analysis, draft, priced, review_issues, settings)
    pdf_bytes = build_offer_pdf(final, settings)

    step("Fertig.")
    return OfferResult(final=final, pdf_bytes=pdf_bytes, analysis=analysis, draft=draft)
