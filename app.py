"""Streamlit-Oberfläche der Angebots-KI.

Start:  streamlit run app.py
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from angebots_ki.catalog import Catalog
from angebots_ki.claude_client import AngebotsKI
from angebots_ki.config import CompanyInfo, Settings
from angebots_ki.errors import OfferGenerationError
from angebots_ki.pipeline import generate_offer
from angebots_ki.utils import extract_pdf_text, fmt_money, fmt_qty

load_dotenv()


def _secret(name: str, default: str = "") -> str:
    """Liest einen Wert aus st.secrets, ohne lokal (ohne secrets.toml) zu crashen."""
    try:
        return str(st.secrets[name])
    except Exception:
        return default


# Auf Streamlit Community Cloud wird der API-Key als Secret hinterlegt. Hier in die
# Umgebung spiegeln, damit der bestehende Key-Pfad (os.getenv / anthropic) unverändert
# funktioniert. Lokal (ohne Secret) bleibt alles wie gehabt (.env oder Seitenleiste).
if not os.getenv("ANTHROPIC_API_KEY"):
    _cloud_key = _secret("ANTHROPIC_API_KEY")
    if _cloud_key:
        os.environ["ANTHROPIC_API_KEY"] = _cloud_key

SAMPLE_DIR = Path(__file__).parent / "sample_data"

st.set_page_config(page_title="Angebots-KI", page_icon="📄", layout="wide")


def _check_password() -> None:
    """Optionaler Passwortschutz – nur aktiv, wenn das Secret APP_PASSWORD gesetzt ist.

    Schützt die öffentliche Demo-URL davor, dass Fremde dein API-Guthaben verbrauchen.
    Ohne gesetztes Secret (z. B. lokal) ist die App frei zugänglich.
    """
    expected = _secret("APP_PASSWORD")
    if not expected or st.session_state.get("auth_ok"):
        return
    st.title("🔒 Angebots-KI")
    st.caption("Bitte Passwort eingeben, um die Demo zu öffnen.")
    pw = st.text_input("Passwort", type="password")
    if pw == expected:
        st.session_state["auth_ok"] = True
        st.rerun()
    elif pw:
        st.error("Falsches Passwort.")
    st.stop()


_check_password()


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------
def _read_sample(name: str) -> str:
    path = SAMPLE_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _load_catalog(uploaded, use_sample: bool) -> Catalog | None:
    try:
        if uploaded is not None:
            return Catalog.load(io.BytesIO(uploaded.getvalue()))
        if use_sample and (SAMPLE_DIR / "produktkatalog.csv").exists():
            return Catalog.load(SAMPLE_DIR / "produktkatalog.csv")
    except OfferGenerationError as exc:
        st.error(str(exc))
    return None


# --------------------------------------------------------------------------
# Sidebar: Einstellungen
# --------------------------------------------------------------------------
st.sidebar.header("⚙️ Einstellungen")

env_key = os.getenv("ANTHROPIC_API_KEY", "")
api_key_input = st.sidebar.text_input(
    "Anthropic API-Key",
    type="password",
    value="",
    help="Leer lassen, wenn ANTHROPIC_API_KEY als Umgebungsvariable/.env gesetzt ist.",
)
if env_key and not api_key_input:
    st.sidebar.caption("✅ API-Key aus der Umgebung wird verwendet.")
elif not env_key and not api_key_input:
    st.sidebar.warning("Kein API-Key gefunden – bitte oben eingeben oder .env setzen.")

with st.sidebar.expander("Modell & Steuer", expanded=False):
    model = st.text_input("Modell", value=Settings.model)
    currency = st.selectbox("Währung", ["EUR", "USD", "GBP", "CHF"], index=0)
    vat_pct = st.number_input("MwSt-Satz (%)", min_value=0.0, max_value=30.0,
                              value=19.0, step=0.5)
    validity = st.number_input("Gültigkeit (Tage)", min_value=1, max_value=365, value=30)
    review_iters = st.number_input("Max. Prüf-/Korrekturdurchläufe", min_value=1,
                                   max_value=3, value=1)
    use_thinking = st.checkbox("Adaptives Thinking nutzen", value=True)

with st.sidebar.expander("Eigene Firmendaten (Briefkopf)", expanded=False):
    c_name = st.text_input("Firmenname", value=CompanyInfo.name)
    c_addr = st.text_area("Adresse (eine Zeile pro Feld)",
                          value="\n".join(CompanyInfo().address_lines), height=90)
    c_phone = st.text_input("Telefon", value=CompanyInfo.phone)
    c_email = st.text_input("E-Mail", value=CompanyInfo.email)
    c_web = st.text_input("Website", value=CompanyInfo.website)
    c_tax = st.text_input("Steuernummer/USt-IdNr.", value=CompanyInfo.tax_id)
    c_bank = st.text_input("Bankverbindung", value=CompanyInfo().bank)


def build_settings() -> Settings:
    company = CompanyInfo(
        name=c_name.strip() or "Unternehmen",
        address_lines=[ln.strip() for ln in c_addr.splitlines() if ln.strip()],
        phone=c_phone.strip(), email=c_email.strip(), website=c_web.strip(),
        tax_id=c_tax.strip(), bank=c_bank.strip(),
    )
    return Settings(
        model=model.strip() or Settings.model,
        currency=currency,
        vat_rate=vat_pct / 100.0,
        default_validity_days=int(validity),
        max_review_iterations=int(review_iters),
        use_thinking=use_thinking,
        company=company,
    )


# --------------------------------------------------------------------------
# Hauptbereich: Eingaben
# --------------------------------------------------------------------------
st.title("📄 Angebots-KI")
st.caption(
    "Liest eine Kunden-E-Mail, erstellt mit Claude ein Angebot anhand deines "
    "Produktkatalogs und einer Beispiel-Vorlage, prüft es selbst und gibt ein PDF aus."
)

left, right = st.columns(2)

with left:
    st.subheader("1 · Produktkatalog (CSV)")
    catalog_file = st.file_uploader("Produktkatalog hochladen", type=["csv"],
                                    key="catalog")
    use_sample_catalog = st.checkbox("Beispielkatalog verwenden", value=True,
                                     help="Nutzt sample_data/produktkatalog.csv")

    st.subheader("2 · Beispiel-Angebot als Vorlage (PDF, optional)")
    template_file = st.file_uploader("Vorlage hochladen", type=["pdf"], key="template")

with right:
    st.subheader("3 · Kundenanfrage (E-Mail)")
    email_upload = st.file_uploader("E-Mail-Datei (.txt/.eml, optional)",
                                    type=["txt", "eml"], key="email")
    if st.button("📨 Beispiel-Anfrage laden"):
        st.session_state["email_text"] = _read_sample("beispiel_email.txt")

    if email_upload is not None and "email_loaded" not in st.session_state:
        st.session_state["email_text"] = email_upload.getvalue().decode(
            "utf-8", errors="replace")
        st.session_state["email_loaded"] = True

    email_text = st.text_area(
        "Text der Angebotsanfrage",
        key="email_text",
        height=260,
        placeholder="Sehr geehrte Damen und Herren, wir benötigen ein Angebot über …",
    )

# Katalog laden + Vorschau
catalog = _load_catalog(catalog_file, use_sample_catalog)
if catalog is not None:
    with st.expander(f"Katalogvorschau ({len(catalog)} Artikel)", expanded=False):
        st.caption(
            f"Erkannt – Artikelnummer: '{catalog.col_sku}', Name: '{catalog.col_name}', "
            f"Preis: '{catalog.col_price}'"
            + (f", Einheit: '{catalog.col_unit}'" if catalog.col_unit else "")
            + (f", {len(catalog.spec_cols)} Spezifikationsspalten" if catalog.spec_cols else "")
        )
        st.dataframe(catalog.preview_df(), use_container_width=True, hide_index=True)

template_text = ""
if template_file is not None:
    template_text = extract_pdf_text(io.BytesIO(template_file.getvalue()))
    st.caption(f"📎 Vorlage gelesen: {len(template_text)} Zeichen Text extrahiert.")

st.divider()
generate = st.button("🚀 Angebot erstellen", type="primary", use_container_width=True)


# --------------------------------------------------------------------------
# Generierung
# --------------------------------------------------------------------------
def render_result(result) -> None:
    final = result.final
    st.success(f"Angebot **{final.offer_number}** erstellt.")

    # Download oben anbieten
    st.download_button(
        "⬇️ Angebot als PDF herunterladen",
        data=result.pdf_bytes,
        file_name=f"Angebot_{final.offer_number}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    if final.warnings:
        st.warning("Hinweise zu Positionen:\n\n- " + "\n- ".join(final.warnings))
    if final.review_issues:
        st.info("Anmerkungen aus der KI-Selbstprüfung:\n\n- "
                + "\n- ".join(final.review_issues))

    tab_pos, tab_text, tab_analysis = st.tabs(
        ["Positionen & Summen", "Texte", "Erkannte Anfrage"])

    with tab_pos:
        rows = [
            {
                "Pos.": it.position,
                "Art.-Nr.": it.sku,
                "Bezeichnung": it.name,
                "Menge": f"{fmt_qty(it.quantity)} {it.unit}",
                "Einzelpreis": fmt_money(it.unit_price, final.currency),
                "Gesamt": fmt_money(it.line_total, final.currency),
            }
            for it in final.line_items
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Zwischensumme", fmt_money(final.subtotal, final.currency))
        c2.metric(f"MwSt ({final.vat_rate * 100:.0f}%)",
                  fmt_money(final.vat_amount, final.currency))
        c3.metric("Gesamtbetrag", fmt_money(final.total, final.currency))

    with tab_text:
        st.markdown(f"**Titel:** {final.title}")
        st.markdown("**Einleitung**")
        st.write(final.intro_text)
        st.markdown("**Abschluss**")
        st.write(final.closing_text)
        st.markdown(f"**Zahlung:** {final.payment_terms}")
        st.markdown(f"**Lieferung/Leistung:** {final.delivery_terms}")

    with tab_analysis:
        cust = result.analysis.customer
        st.markdown(
            f"**Kunde:** {cust.company or '—'} · {cust.contact_name or '—'} · "
            f"{cust.email or '—'}"
        )
        if result.analysis.summary:
            st.markdown(f"**Zusammenfassung:** {result.analysis.summary}")
        st.markdown("**Angefragte Positionen:**")
        st.dataframe(
            [
                {"Beschreibung": i.description, "Menge": fmt_qty(i.quantity),
                 "Einheit": i.unit, "Hinweis": i.notes}
                for i in result.analysis.items
            ],
            use_container_width=True, hide_index=True,
        )
        if result.analysis.open_questions:
            st.markdown("**Offene Punkte:**\n\n- "
                        + "\n- ".join(result.analysis.open_questions))


if generate:
    if catalog is None:
        st.error("Bitte zuerst einen Produktkatalog (CSV) bereitstellen.")
    elif not (email_text or "").strip():
        st.error("Bitte den Text der Kundenanfrage einfügen.")
    else:
        settings = build_settings()
        try:
            ki = AngebotsKI(settings, api_key=api_key_input or None)
        except Exception as exc:  # z. B. fehlender Key
            st.error(f"KI konnte nicht initialisiert werden: {exc}")
        else:
            status = st.status("Starte Angebotserstellung …", expanded=True)
            try:
                result = generate_offer(
                    email_text=email_text,
                    catalog=catalog,
                    template_text=template_text,
                    ki=ki,
                    settings=settings,
                    progress=lambda m: status.write(m),
                )
                status.update(label="Angebot fertig erstellt ✅", state="complete")
                st.session_state["result"] = result
            except OfferGenerationError as exc:
                status.update(label="Abgebrochen", state="error")
                st.error(str(exc))
            except Exception as exc:  # unerwartete Fehler
                status.update(label="Unerwarteter Fehler", state="error")
                st.exception(exc)

if "result" in st.session_state:
    st.divider()
    render_result(st.session_state["result"])
