import streamlit as st

from ui import tabs


def main() -> None:
    st.set_page_config(page_title="Smart Parser UI", layout="wide")
    st.title("Smart Parser UI")
    tabs.render_tabs()


if __name__ == "__main__":
    main()
