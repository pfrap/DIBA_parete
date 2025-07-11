import streamlit as st
from moduli.login import login
from Navigation import navbar

import Home
import Listino_pareti
import Quotazioni

st.set_page_config(page_title="Unifor partitions")

# --- Login ---
login()
if st.session_state["logged_in"]:
    st.set_page_config(layout="wide", page_title="Unifor partitions")
    # --- Navbar ---
    selected = navbar()
    # --- Routing ---
    if selected == "Area tecnica":
        Home.show()
    elif selected == "Listino":
        Listino_pareti.show()
    elif selected == "Quotazioni":
        Quotazioni.show()
