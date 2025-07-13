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

    # Filtro per FINITURA
    if "FINITURA" in df_filtrato.columns:
        opzioni_finitura = sorted(df_filtrato["FINITURA"].dropna().unique())
        scelta_finitura = st.sidebar.selectbox("Finitura", opzioni_finitura)

        # Estrai la descrizione finitura, prendendo la prima se ci sono più righe
        descr_series = df_filtrato[df_filtrato["FINITURA"] == scelta_finitura]["DESCRIZIONE_FINITURA"].dropna()
        scelta_descrizione = descr_series.iloc[0] if not descr_series.empty else "N/A"

        # Aggiungi al dizionario filtri
        filtri_attivi["Finitura selezionata"] = f"{scelta_finitura} - {scelta_descrizione}"

        # Filtra il dataframe
        df_filtrato = df_filtrato[df_filtrato["FINITURA"] == scelta_finitura]


    return df_filtrato.reset_index(drop=True), filtri_attivi


def show():
    if 'df_listino_grouped' not in st.session_state:
        st.warning("⚠️ Listino non caricato a sistema.")
        return
    
    # Colonne principali
    col_listino_it = [
        'MACRO_SISTEMA', 'SISTEMA', 'CONCAT_3', 'C1', 'C1_DESCRIZIONE',
        'C2', 'C2_DESCRIZIONE', 
        'UNIT_ARTICOLO_PADRE', 'FINITURA','DESCRIZIONE_FINITURA', 'LISTINO','ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE', 'IMMAGINE_NOME_FILE'
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
    st.title("Listino pareti")
    
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
                st.markdown(f"***Prezzo listino:*** {df_filtrato.loc[selected_index, "LISTINO"]:.2f} €/unit")
        st.divider()
    #st.dataframe(st.session_state["df_listino_vendita"])
    #st.write(st.session_state["df_listino_vendita"].columns.tolist())


    # Aggiungi all'offerta
    if st.sidebar.button("➕ Aggiungi articoli selezionati alla quotazione"):
        selezionati = edited_df[edited_df[colrename_diz.get("SELEZIONA", "SELEZIONA")] == True].copy()

        if selezionati.empty:
            st.warning("Seleziona almeno un articolo per aggiungerlo all'offerta.")
        else:
            # Rimuove la colonna selezione e torna ai nomi originali
            selezionati = selezionati.drop(columns=[colrename_diz.get("SELEZIONA", "SELEZIONA")])
            reverse_colrename_diz = {v: k for k, v in colrename_diz.items()}
            selezionati.rename(columns=reverse_colrename_diz, inplace=True)

            # Colonne necessarie per la quotazione
            col_sezione_quotazione = ['SISTEMA', 'C1_DESCRIZIONE', 'CONCAT_3', 'ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE', 'UNIT_ARTICOLO_PADRE', 'LISTINO']
            selezionati = selezionati[col_sezione_quotazione]

            # Aggiunge colonne Q_TA e TOTALE
            selezionati["Q_TA"] = 1.0
            selezionati["TOTALE"] = selezionati["LISTINO"] * selezionati["Q_TA"]

            # Inizializza df_quotazione se non esiste
            if "df_quotazione" not in st.session_state:
                st.session_state["df_quotazione"] = {}

            # Nome sezione di default
            sezione_corrente = "Sezione_1"

            # Inizializza sezione se non esiste
            if sezione_corrente not in st.session_state["df_quotazione"]:
                st.session_state["df_quotazione"][sezione_corrente] = pd.DataFrame(columns=col_sezione_quotazione + ["Q_TA", "TOTALE"])

            # Aggiunge gli articoli evitando duplicati
            df_corrente = st.session_state["df_quotazione"][sezione_corrente]
            df_aggiornato = pd.concat([df_corrente, selezionati], ignore_index=True)
            df_aggiornato = df_aggiornato.drop_duplicates(subset=["CONCAT_3"], keep='last')

            st.session_state["df_quotazione"][sezione_corrente] = df_aggiornato

            st.sidebar.success(f"Aggiunti {len(selezionati)} articoli alla quotazione ({sezione_corrente}).")

if __name__ == "__main__":
    show()


