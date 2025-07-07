import streamlit as st

def login():
    credenziali = st.secrets["auth"]
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if username in credenziali and credenziali[username] == password:
                st.session_state["logged_in"] = True
                st.sidebar.success(f"Benvenuto, {username}!")
            else:
                st.sidebar.error("Credenziali non valide")
    else:
        if st.sidebar.button("🔒 Logout"):
            st.session_state["logged_in"] = False

    return st.session_state["logged_in"]