# ui/tabs.py
import streamlit as st

from ui import actions, forms


def render_tabs() -> None:
    telegram_tab, web_tab, api_tab = st.tabs(["Telegram", "Web", "API (Albion)"])

    with telegram_tab:
        st.subheader("Telegram")
        form_data = forms.render_telegram_form()
        render_actions(form_data, prefix="tg")

    with web_tab:
        st.subheader("Web")
        form_data = forms.render_web_form()
        render_actions(form_data, prefix="web")

    with api_tab:
        st.info("TODO: later")
        st.button("Run", disabled=True, key="api_run")
        st.button("Open summary", disabled=True, key="api_open")
        st.button("Show status", disabled=True, key="api_status")


def _validate_event_text_v1(form_data: dict) -> tuple[bool, str]:
    # Strict minimal UI-gate before writing input.json.
    # We only validate what UI itself creates for event_text_v1.
    if not isinstance(form_data, dict):
        return False, "Internal error: form data is not a dict."

    keywords = form_data.get("keywords")
    if not isinstance(keywords, list) or not keywords or not all(isinstance(x, str) and x.strip() for x in keywords):
        return False, "Keywords are required (comma-separated)."

    has_tg = "telegram" in form_data
    has_web = "web" in form_data
    if has_tg and has_web:
        return False, "Internal error: input cannot contain both telegram and web in this UI tab."

    if not has_tg and not has_web:
        return False, "Internal error: missing source section (telegram/web)."

    if has_tg:
        tg = form_data.get("telegram")
        channels = (tg or {}).get("channels") if isinstance(tg, dict) else None
        if not isinstance(channels, list) or not channels:
            return False, "Telegram channels are required."
        if not all(isinstance(x, str) and x.strip() for x in channels):
            return False, "Telegram channels must be non-empty strings."

    if has_web:
        web = form_data.get("web")
        urls = (web or {}).get("urls") if isinstance(web, dict) else None
        if not isinstance(urls, list) or not urls:
            return False, "At least one URL/RSS is required."
        if not all(isinstance(x, str) and x.strip() for x in urls):
            return False, "Web URLs must be non-empty strings."

    if "days" in form_data:
        days = form_data["days"]
        if not isinstance(days, int) or days < 1:
            return False, "Lookback (days) must be an integer >= 1."

    # No extra fields policy for this UI:
    allowed_top = {"keywords", "days", "telegram", "web"}
    extra = set(form_data.keys()) - allowed_top
    if extra:
        return False, f"Internal error: extra fields in input: {sorted(extra)}"

    return True, ""


def render_actions(form_data: dict, prefix: str) -> None:
    col_run, col_summary, col_status = st.columns(3)

    with col_run:
        if st.button("Run", key=f"{prefix}_run"):
            ok, msg = _validate_event_text_v1(form_data)
            if not ok:
                st.error(msg)
            else:
                try:
                    actions.write_input_json(form_data)
                    actions.run_parser()
                    st.success("Parser finished.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Run failed: {exc}")

    with col_summary:
        if st.button("Open summary", key=f"{prefix}_open"):
            summary = actions.open_summary()
            if summary is None:
                st.warning("No summary found at runtime/output/summary.md")
            else:
                st.markdown(summary)

    with col_status:
        if st.button("Show status", key=f"{prefix}_status"):
            report = actions.show_status()
            if report is None:
                st.warning("No mapper report found at runtime/mapper/mapper_report.json")
            else:
                st.json(report)
