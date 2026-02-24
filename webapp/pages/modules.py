import streamlit as st
from pathlib import Path

def util_sidebar():
    # material symbols
    st.markdown(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />',
        unsafe_allow_html=True
    )
  
    # основной css
    css_path = Path(__file__).parent.parent / "static" / "css" / "sidebar.css"

    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.write("Menu")

        # HOME 
        if st.button("На главную", icon=":material/home:"):
            st.switch_page("home.py")

        # PAGE 1
        if st.button("Генератор отчётов", icon=":material/edit_document:"):
            st.switch_page("pages/Template.py")

        # PAGE 2
        if st.button("Генератор блоксхем", icon=":material/schema:"):
            st.switch_page("pages/SchemeAI.py")

        if st.button("Баг репорт", icon=":material/bug_report:"):
            st.switch_page("pages/page3.py")

