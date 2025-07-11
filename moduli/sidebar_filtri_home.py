import streamlit as st
import pandas as pd

def sidebar_filtri_distinta(df_distinta):
    st.sidebar.header("Filtri distinta")

    # --- Ricerca diretta avanzata ---
    search_text = st.sidebar.text_input("🔍 Ricerca libera (codice, descrizione, categoria...)")
    matching_rows = pd.DataFrame()
    selected_padre_input = None

    if search_text:
        # ⬅️ Elenco delle colonne da usare per la ricerca
        colonne_da_cercare = [
            "MACRO_SISTEMA",
            "COD_SISTEMA",
            "SISTEMA",
            "C1",
            "C1_DESCRIZIONE",
            "C2",
            "C2_DESCRIZIONE",
            "CONCAT_3",
            "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE",
            "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE_BREVE",
            "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE_EN_BREVE"
        ]

        search_words = search_text.lower().split()

        def row_matches_all_words(row):
            testo_riga = ' '.join(
                row[col].lower() if pd.notna(row[col]) else '' 
                for col in colonne_da_cercare
                if col in row
            )
            return all(word in testo_riga for word in search_words)

        mask = df_distinta.apply(row_matches_all_words, axis=1)
        matching_rows = df_distinta[mask]

        if not matching_rows.empty:
            # Crea opzioni leggibili come: "CODICE - Descrizione"
            matching_rows["LABEL"] = matching_rows.apply(
                lambda x: f"{x['CONCAT_3']} - {x['ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE_BREVE']}", axis=1
            )
            # Tieni solo i primi 10 risultati unici
            dropdown_options = matching_rows[["CONCAT_3", "LABEL"]].drop_duplicates().head(10)

            selected_label = st.sidebar.selectbox("🔍 Risultati trovati:", dropdown_options["LABEL"].tolist())
            selected_padre_input = dropdown_options[dropdown_options["LABEL"] == selected_label]["CONCAT_3"].values[0]
        else:
            st.sidebar.info("Nessun risultato trovato.")
        
        # Quando uso la ricerca libera, disabilito i filtri dropdown
        selected_macro = None
        selected_cod_sistema = None
        selected_c1 = None
        selected_c2 = None

    else:
        selected_padre_input = None
        
        # Default per i filtri automatici
        default_macro = None
        default_sistema = None
        default_c1 = None
        default_c2 = None
        selected_padre = None

        if selected_padre_input and selected_padre_input in df_distinta["CONCAT_3"].values:
            riga = df_distinta[df_distinta["CONCAT_3"] == selected_padre_input].iloc[0]
            default_macro = riga["MACRO_SISTEMA"]
            default_sistema = riga["SISTEMA"]
            default_c1 = riga["C1_DESCRIZIONE"]
            default_c2 = riga["C2_DESCRIZIONE"]
            selected_padre = selected_padre_input

        # Filtro 1: MACRO SISTEMA
        macro_opzioni = sorted(df_distinta["MACRO_SISTEMA"].dropna().unique())
        selected_macro = st.sidebar.selectbox(
            "Macro sistema",
            macro_opzioni,
            index=macro_opzioni.index(default_macro) if default_macro in macro_opzioni else 0
        )
        filtered_macro = df_distinta[df_distinta["MACRO_SISTEMA"] == selected_macro]

        # Filtro 2: SISTEMA
        sistema_opzioni = sorted(filtered_macro["SISTEMA"].dropna().unique())
        selected_cod_sistema = st.sidebar.selectbox(
            "Codice sistema",
            sistema_opzioni,
            index=sistema_opzioni.index(default_sistema) if default_sistema in sistema_opzioni else 0
        )
        filtered_cod = filtered_macro[filtered_macro["SISTEMA"] == selected_cod_sistema]

        # Filtro 3: C1_DESCRIZIONE
        c1_opzioni = sorted(filtered_cod["C1_DESCRIZIONE"].dropna().unique())
        selected_c1 = st.sidebar.selectbox(
            "C1 Descrizione",
            c1_opzioni,
            index=c1_opzioni.index(default_c1) if default_c1 in c1_opzioni else 0
        )
        filtered_c1 = filtered_cod[filtered_cod["C1_DESCRIZIONE"] == selected_c1]

        # Filtro 4: C2_DESCRIZIONE
        c2_opzioni = sorted(filtered_c1["C2_DESCRIZIONE"].dropna().unique())
        selected_c2 = st.sidebar.selectbox(
            "C2 Descrizione",
            c2_opzioni,
            index=c2_opzioni.index(default_c2) if default_c2 in c2_opzioni else 0
        )
        filtered_c2 = filtered_c1[filtered_c1["C2_DESCRIZIONE"] == selected_c2]

    # Scelta finale dell’articolo
    if selected_padre_input is not None:
        df_filtered_distinta = df_distinta[df_distinta["CONCAT_3"] == selected_padre_input]
        selected_padre = selected_padre_input
    else:
        if 'filtered_c2' in locals():
            codici_possibili = sorted(filtered_c2["CONCAT_3"].dropna().unique())
        else:
            codici_possibili = sorted(df_distinta["CONCAT_3"].dropna().unique())  # fallback se ricerca libera non ha dato nulla

        selected_padre = st.sidebar.selectbox("Codice articolo", codici_possibili)
        df_filtered_distinta = df_distinta[df_distinta["CONCAT_3"] == selected_padre]


    return df_filtered_distinta, selected_padre, selected_macro, selected_cod_sistema, selected_c1, selected_c2