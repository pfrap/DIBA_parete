import streamlit as st
import pandas as pd
import base64
import os

def path_to_base64_img_html(img_path, width=300):
    if not os.path.exists(img_path):
        return None
    with open(img_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
    return f'<img src="data:image/jpeg;base64,{b64}" width="{width}"/>'

def filtro_sidebar_listino(df_listino: pd.DataFrame) -> pd.DataFrame:
    # Filtri nella sidebar (o puoi metterli in colonna sx)
    st.sidebar.header("🎛️ Filtri articoli")
    search_text = st.sidebar.text_input("🔍 Ricerca libera (codice, descrizione, C1, C2...)").strip().lower()
    df_filtrato = df_listino.copy()

    if search_text:
        colonne_ricerca = ["CONCAT_3", "DESCRIZIONE", "C1", "C2"]
        parole = search_text.split()
        def match(row):
            testo = " ".join(str(row[col]).lower() for col in colonne_ricerca if col in row and pd.notna(row[col]))
            return all(p in testo for p in parole)
        df_filtrato = df_filtrato[df_filtrato.apply(match, axis=1)]

    macro_opzioni = sorted(df_filtrato["MACRO_SISTEMA"].dropna().unique())
    selected_macro = st.sidebar.selectbox("🏗 Macro Sistema", ["Tutti"] + macro_opzioni)
    if selected_macro != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["MACRO_SISTEMA"] == selected_macro]

    sistema_opzioni = sorted(df_filtrato["SISTEMA"].dropna().unique())
    selected_sistema = st.sidebar.selectbox("🧩 Codice Sistema", ["Tutti"] + sistema_opzioni)
    if selected_sistema != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["SISTEMA"] == selected_sistema]

    c1_opzioni = sorted(df_filtrato["C1"].dropna().unique())
    selected_c1 = st.sidebar.selectbox("📁 C1", ["Tutti"] + c1_opzioni)
    if selected_c1 != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["C1"] == selected_c1]

    c2_opzioni = sorted(df_filtrato["C2"].dropna().unique())
    selected_c2 = st.sidebar.selectbox("📂 C2", ["Tutti"] + c2_opzioni)
    if selected_c2 != "Tutti":
        df_filtrato = df_filtrato[df_filtrato["C2"] == selected_c2]

    return df_filtrato.reset_index(drop=True)

def show():
    st.title("Listino Pareti")

    if 'df_listino_grouped' not in st.session_state:
        st.warning("⚠️ Carica prima il listino nella pagina Area tecnica.")
        return

    df_listino_originale = st.session_state['df_listino_grouped']
    df_filtrato = filtro_sidebar_listino(df_listino_originale)
    df_filtrato["SELEZIONA"] = False

    # Layout 2 colonne: sinistra filtri+tabella, destra immagine articolo selezionato
    col1, col2 = st.columns([3,2])

    with col1:
        edited_df = st.data_editor(
            df_filtrato,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            disabled=df_filtrato.columns.difference(["SELEZIONA"]).tolist(),
            key="editor_listino_pareti"
        )
    
    # Trova il primo articolo selezionato (o nessuno)
    selected_rows = edited_df[edited_df["SELEZIONA"] == True]
    if not selected_rows.empty:
        selected_row = selected_rows.iloc[0]
        img_path = selected_row["IMMAGINE_NOME_FILE"]
    else:
        selected_row = None
        img_path = None

    with col2:
        st.markdown("### Anteprima immagine articolo")
        if img_path:
            img_html = path_to_base64_img_html(img_path, width=300)
            if img_html:
                st.markdown(img_html, unsafe_allow_html=True)
            else:
                st.warning("Immagine non trovata.")
        else:
            st.info("Seleziona un articolo per vedere l'immagine.")

    # Pulsante per aggiungere selezionati all'offerta (facoltativo, lo puoi lasciare uguale)
    if st.button("➕ Aggiungi articoli selezionati all'offerta"):
        if 'df_quotazione' not in st.session_state:
            st.session_state['df_quotazione'] = {}

        if "sessione_1" not in st.session_state['df_quotazione']:
            st.session_state['df_quotazione']["sessione_1"] = pd.DataFrame()

        selezionati = edited_df[edited_df["SELEZIONA"] == True].drop(columns=["SELEZIONA"])

        if selezionati.empty:
            st.warning("Seleziona almeno un articolo per aggiungerlo all'offerta.")
        else:
            df_offerta = st.session_state['df_quotazione']["sessione_1"]
            df_offerta = pd.concat([df_offerta, selezionati])
            df_offerta = df_offerta.drop_duplicates(subset=["CONCAT_3"], keep='last').reset_index(drop=True)
            st.session_state['df_quotazione']["sessione_1"] = df_offerta
            st.success(f"Aggiunti {len(selezionati)} articoli all'offerta (sessione_1).")

if __name__ == "__main__":
    show()
