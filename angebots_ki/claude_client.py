"""Anbindung an Claude: Anfrage analysieren, Angebot entwerfen, selbst prüfen."""

from __future__ import annotations

from typing import Any, Optional, Type, TypeVar

import anthropic
from pydantic import BaseModel

from .catalog import Catalog
from .config import Settings
from .errors import OfferGenerationError
from .models import OfferDraft, RequestAnalysis, ReviewResult

T = TypeVar("T", bound=BaseModel)


def _strictify(node: Any) -> Any:
    """Macht ein Pydantic-JSON-Schema kompatibel zu strukturierten Outputs.

    Wird nur im Fallback (ältere SDKs ohne ``messages.parse``) benötigt: setzt auf
    jedem Objekt ``additionalProperties: false`` und ``required`` = alle Felder.
    """
    if isinstance(node, dict):
        node.pop("title", None)
        if node.get("type") == "object" and "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node["properties"].keys())
        return {k: _strictify(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_strictify(v) for v in node]
    return node


class AngebotsKI:
    """Kapselt alle KI-Aufrufe für die Angebotserstellung."""

    def __init__(self, settings: Settings, api_key: Optional[str] = None):
        self.settings = settings
        # Ohne expliziten Key liest das SDK ANTHROPIC_API_KEY aus der Umgebung.
        self.client = (
            anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        )

    # -- generischer strukturierter Aufruf --------------------------------

    def _structured(
        self,
        *,
        system: str,
        user: str,
        schema: Type[T],
        thinking: bool = True,
        max_tokens: int = 16000,
    ) -> T:
        base: dict[str, Any] = dict(
            model=self.settings.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        if thinking and self.settings.use_thinking:
            base["thinking"] = {"type": "adaptive"}

        # Bevorzugt: messages.parse() validiert direkt gegen das Pydantic-Modell.
        parse = getattr(self.client.messages, "parse", None)
        if parse is not None:
            try:
                resp = parse(output_format=schema, **base)
            except TypeError:
                resp = None  # SDK-Variante akzeptiert die Argumente nicht -> Fallback
            else:
                parsed = getattr(resp, "parsed_output", None)
                if parsed is not None:
                    return parsed
                raise OfferGenerationError(
                    "Die KI hat keine verwertbare Antwort geliefert "
                    "(mögliche Ablehnung oder Token-Limit erreicht)."
                )

        # Fallback: create() mit JSON-Schema und manueller Validierung.
        try:
            resp = self.client.messages.create(
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": _strictify(schema.model_json_schema()),
                    }
                },
                **base,
            )
        except anthropic.APIError as exc:
            raise OfferGenerationError(f"Fehler beim KI-Aufruf: {exc}") from exc

        text = next(
            (b.text for b in resp.content if getattr(b, "type", None) == "text"), ""
        )
        if not text:
            raise OfferGenerationError("Die KI hat eine leere Antwort geliefert.")
        try:
            return schema.model_validate_json(text)
        except Exception as exc:
            raise OfferGenerationError(
                f"Die KI-Antwort entsprach nicht dem erwarteten Format: {exc}"
            ) from exc

    def _call(self, **kwargs: Any) -> Any:
        """Wrappt _structured und übersetzt API-Fehler in klare Meldungen."""
        try:
            return self._structured(**kwargs)
        except anthropic.AuthenticationError as exc:
            raise OfferGenerationError(
                "Anmeldung bei der Claude-API fehlgeschlagen. Bitte ANTHROPIC_API_KEY prüfen."
            ) from exc
        except anthropic.APIError as exc:
            raise OfferGenerationError(f"Fehler beim KI-Aufruf: {exc}") from exc

    # -- Schritt 1: Anfrage analysieren -----------------------------------

    def analyze_request(self, email_text: str, catalog: Catalog) -> RequestAnalysis:
        system = (
            "Du bist ein erfahrener Vertriebsassistent. Analysiere die E-Mail einer "
            "Angebotsanfrage und extrahiere strukturiert die Kundendaten und die "
            "angefragten Positionen.\n"
            "- Erfinde keine Informationen. Was nicht in der E-Mail steht, bleibt leer "
            "(leerer String, 0 oder leere Liste).\n"
            "- Erfasse jede angefragte Position einzeln mit Menge und Einheit, soweit genannt.\n"
            "- Halte open_questions kurz und nur für echte Unklarheiten."
        )
        user = f"Hier ist die Angebotsanfrage des Kunden:\n\n---\n{email_text}\n---"
        return self._call(system=system, user=user, schema=RequestAnalysis,
                          thinking=False, max_tokens=8000)

    # -- Schritt 2: Angebot entwerfen -------------------------------------

    def draft_offer(
        self, analysis: RequestAnalysis, catalog: Catalog, template_text: str
    ) -> OfferDraft:
        system = (
            "Du bist ein Vertriebsprofi und erstellst ein professionelles, "
            "verkaufsstarkes Angebot auf Deutsch.\n"
            "Regeln:\n"
            "- Wähle Positionen AUSSCHLIESSLICH aus dem bereitgestellten Produktkatalog "
            "und referenziere sie über die korrekte Artikelnummer (sku).\n"
            "- Erfinde keine Artikel und KEINE Preise. Die Preise und Summen berechnet "
            "das System autoritativ aus dem Katalog – gib selbst keine Preise an.\n"
            "- Wähle die Artikel, deren Spezifikationen am besten zur Anfrage passen.\n"
            "- Ist ein angefragter Artikel nicht im Katalog, nimm ihn NICHT als Position "
            "auf, sondern weise im closing_text transparent darauf hin.\n"
            "- Orientiere dich in Tonalität, Aufbau und Formulierungen an der Beispiel-"
            "Vorlage, falls eine vorhanden ist.\n"
            "- Schreibe vollständige, höfliche Texte (Anrede, Bezug zur Anfrage, "
            "Mehrwert, nächste Schritte)."
        )
        template_block = (
            f"\n\n=== BEISPIEL-VORLAGE (nur Stil/Struktur) ===\n{template_text}"
            if template_text.strip()
            else "\n\n(Keine Beispiel-Vorlage vorhanden – nutze einen üblichen, "
            "professionellen Angebotsaufbau.)"
        )
        user = (
            "=== ANALYSE DER KUNDENANFRAGE (JSON) ===\n"
            f"{analysis.model_dump_json(indent=2)}\n\n"
            "=== PRODUKTKATALOG ===\n"
            f"{catalog.to_prompt_text()}"
            f"{template_block}\n\n"
            "Erstelle nun den Angebotsentwurf. Denke an: passende Artikel per sku, "
            "sinnvolle Mengen, überzeugende Texte, Zahlungs- und Lieferbedingungen, "
            "Gültigkeitsdauer in Tagen."
        )
        return self._call(system=system, user=user, schema=OfferDraft, max_tokens=16000)

    # -- Schritt 3: Selbstprüfung -----------------------------------------

    def review_offer(
        self,
        offer_review_text: str,
        analysis: RequestAnalysis,
        catalog: Catalog,
        template_text: str,
    ) -> ReviewResult:
        system = (
            "Du bist eine sorgfältige zweite Person im Vertrieb und prüfst ein bereits "
            "erstelltes Angebot kritisch gegen die ursprüngliche Anfrage und den Katalog.\n"
            "Prüfe insbesondere:\n"
            "1. Wurde alles Angefragte berücksichtigt? Fehlt etwas?\n"
            "2. Passen die gewählten Artikel und ihre Spezifikationen zur Anfrage?\n"
            "3. Sind die Mengen plausibel und korrekt?\n"
            "4. Ist der Text professionell, fehlerfrei, höflich und konsistent zur Vorlage?\n"
            "Wichtig: Preise und Summen wurden vom System autoritativ aus dem Katalog "
            "berechnet – prüfe sie NICHT rechnerisch und ändere keine Preise. Weise aber "
            "auf falsch ausgewählte Artikel hin.\n"
            "Liste konkrete Probleme in 'issues'. Setze approved=true nur, wenn keine "
            "wesentlichen Mängel bestehen. Gib in 'corrected_offer' eine verbesserte "
            "Fassung zurück (bei approved=true praktisch identisch). Verwende auch dort "
            "nur Artikelnummern aus dem Katalog und keine Preise."
        )
        template_block = (
            f"\n\n=== BEISPIEL-VORLAGE ===\n{template_text}"
            if template_text.strip()
            else ""
        )
        user = (
            "=== URSPRÜNGLICHE ANFRAGE (JSON) ===\n"
            f"{analysis.model_dump_json(indent=2)}\n\n"
            "=== AKTUELLES ANGEBOT (inkl. systemberechneter Preise) ===\n"
            f"{offer_review_text}\n\n"
            "=== PRODUKTKATALOG ===\n"
            f"{catalog.to_prompt_text()}"
            f"{template_block}\n\n"
            "Prüfe das Angebot und liefere das Ergebnis im geforderten Format."
        )
        return self._call(system=system, user=user, schema=ReviewResult, max_tokens=16000)
