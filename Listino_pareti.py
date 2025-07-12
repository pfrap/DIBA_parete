import streamlit as st
import pandas as pd

def filtro_sidebar_listino(df_listino: pd.DataFrame):
    st.sidebar.header("Filtri articoli")

    search_text = st.sidebar.text_input("🔍 Ricerca libera (codice, descrizione, C1, C2...)").strip().lower()

    df_filtrato = df_listino.copy()
    filtri_attivi = {"Ricerca libera": search_text}

    if search_text:
        colonne_ricerca = ['MACRO_SISTEMA', 'COD_SISTEMA', 'SISTEMA', 'CONCAT_3', 'C1', 'C1_DESCRIZIONE', 'C2', 'C2_DESCRIZIONE', 'ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE']
        parole = search_text.split()

        def match(row):
            testo = " ".join(str(row[col]).lower() for col in colonne_ricerca if col in row and pd.notna(row[col]))
            return all(p in testo for p in parole)

        df_filtrato = df_filtrato[df_filtrato.apply(match, axis=1)]

    for col, label in [("MACRO_SISTEMA", "Famiglia di prodotto"), ("SISTEMA", "Sistema"),
                       ("C1_DESCRIZIONE", "Categoria"), ("C2_DESCRIZIONE", "Sottocategoria")]:
        opzioni = sorted(df_filtrato[col].dropna().unique())
        scelta = st.sidebar.selectbox(label, ["Tutti"] + opzioni)
        filtri_attivi[label] = scelta
        if scelta != "Tutti":
            df_filtrato = df_filtrato[df_filtrato[col] == scelta]

    return df_filtrato.reset_index(drop=True), filtri_attivi


def show():
    if 'df_listino_grouped' not in st.session_state:
        st.warning("⚠️ Listino non caricato a sistema.")
        return
    
    # Colonne principali
    col_listino_it = [
        'MACRO_SISTEMA', 'SISTEMA', 'CONCAT_3', 'C1', 'C1_DESCRIZIONE',
        'C2', 'C2_DESCRIZIONE', 
        'UNIT_ARTICOLO_PADRE', 'LISTINO','ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE', 'IMMAGINE_NOME_FILE'
    ]

    df_listino_originale = st.session_state['df_listino_grouped'][col_listino_it]
    df_filtrato, filtri_attivi = filtro_sidebar_listino(df_listino_originale)


    # Aggiungiamo SELEZIONA solo se non esiste già
    if "SELEZIONA" not in df_filtrato.columns:
        df_filtrato["SELEZIONA"] = False

    # Rinomina colonne per visualizzazione
    colrename_diz = st.session_state.get('colrename_diz', {})
    df_vis = df_filtrato.rename(columns=colrename_diz)
    
    # Sposta la colonna "SELEZIONA" come prima colonna in df_vis
    seleziona_col = colrename_diz.get("SELEZIONA", "SELEZIONA")
    cols = [seleziona_col] + [c for c in df_vis.columns if c != seleziona_col]
    df_vis = df_vis[cols]
    
    ##################################### Layout
    st.title("Listino Pareti")
    
    Cont_dati=st.container()
    Cont_editor=st.container()
    with Cont_editor:
        
        edited_df = st.data_editor(
        df_vis,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        disabled=[colrename_diz.get(c, c) for c in df_filtrato.columns if c != "SELEZIONA"],
        key="editor_listino_pareti"
        )

    with Cont_dati:
        col1, col2, col3 = st.columns([1,1,1])            
        with col1:
            st.subheader(f"Visualizzazione listino per:")
            for chiave, valore in filtri_attivi.items():
                if valore and valore != "Tutti":
                    st.write(f"{chiave}: ***`{valore}`***")

        with col3:
            selected_rows = edited_df[edited_df[colrename_diz.get("SELEZIONA", "SELEZIONA")] == True]
            if not selected_rows.empty:
                
                # Recupera la riga originale con nomi originali
                selected_index = selected_rows.index[0]
                img_path = df_filtrato.loc[selected_index, "IMMAGINE_NOME_FILE"]

                if img_path and isinstance(img_path, str):
                    st.image(img_path, width=300, caption="Articolo selezionato")
                else:
                    st.warning("Immagine non trovata.")
            else:
                st.info("Seleziona un articolo per vedere l'immagine.")
        with col2:
            if not selected_rows.empty:
                st.subheader(f"{df_filtrato.loc[selected_index, "CONCAT_3"]}")
                st.markdown(f"***Famiglia:*** {df_filtrato.loc[selected_index, "MACRO_SISTEMA"]} - ***Sistema:*** {df_filtrato.loc[selected_index, "SISTEMA"]}  ")
                st.markdown(f"***Categoria:*** {df_filtrato.loc[selected_index, "C1"]} {df_filtrato.loc[selected_index, "C2"]} - {df_filtrato.loc[selected_index, "C2_DESCRIZIONE"]}")
                st.markdown(f"***Unit:*** {df_filtrato.loc[selected_index, "UNIT_ARTICOLO_PADRE"]} ")
                st.metric("Prezzo listino", f"{df_filtrato.loc[selected_index, "LISTINO"]:.2f} €/unit")
        st.divider()
    # Aggiungi all'offerta
    if st.button("➕ Aggiungi articoli selezionati all'offerta"):
        if 'df_quotazione' not in st.session_state:
            st.session_state['df_quotazione'] = {}

        if "sessione_1" not in st.session_state['df_quotazione']:
            st.session_state['df_quotazione']["sessione_1"] = pd.DataFrame()

        selezionati = edited_df[edited_df[colrename_diz.get("SELEZIONA", "SELEZIONA")] == True]
        if selezionati.empty:
            st.warning("Seleziona almeno un articolo per aggiungerlo all'offerta.")
        else:
            # Rimuovi la colonna SELEZIONA e ripristina i nomi originali
            selezionati = selezionati.drop(columns=[colrename_diz.get("SELEZIONA", "SELEZIONA")])
            selezionati.columns = [k for k, v in colrename_diz.items() if v in selezionati.columns]

            df_offerta = st.session_state['df_quotazione']["sessione_1"]
            df_offerta = pd.concat([df_offerta, selezionati])
            df_offerta = df_offerta.drop_duplicates(subset=["CONCAT_3"], keep='last').reset_index(drop=True)
            st.session_state['df_quotazione']["sessione_1"] = df_offerta

            st.success(f"Aggiunti {len(selezionati)} articoli all'offerta (sessione_1).")

if __name__ == "__main__":
    show()
