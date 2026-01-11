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
        st.subheader("API (Albion)")
        st.info("TODO: later")
        st.button("Run", disabled=True, key="api_run")
        st.button("Open summary", disabled=True, key="api_open")
        st.button("Show status", disabled=True, key="api_status")


def render_actions(form_data: dict, prefix: str) -> None:
    col_run, col_summary, col_status = st.columns(3)

    with col_run:
        if st.button("Run", key=f"{prefix}_run"):
            if not form_data["keywords"]:
                st.error("Keywords are required.")
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
                st.warning("No status found at runtime/output/mapper_report.json")
            else:
                st.json(report)
