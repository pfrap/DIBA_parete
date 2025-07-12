import streamlit as st

def login():
    #st.session_state["logged_in"] = True
    credenziali = st.secrets["auth"]
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in credenziali and credenziali[username] == password:
                st.session_state["logged_in"] = True
                st.sidebar.success(f"Benvenuto, {username}!")
                st.rerun()  # ⬅️ Forza il rerun subito dopo login
            else:
                st.sidebar.error("Credenziali non valide")
    else:
        if st.sidebar.button("🔒 Logout"):
            st.session_state["logged_in"] = False
            st.rerun()  # ⬅️ Forza il rerun anche al logout

    return st.session_state["logged_in"]
