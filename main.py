import streamlit as st
import pandas as pd
from PIL import Image
import os

# Accedi ai dati salvati
credenziali = st.secrets["auth"]

# Inizializza la variabile di sessione
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Login nella sidebar
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

# Contenuto riservato visibile solo se loggato
if st.session_state["logged_in"]:

    # 🔒 CONTENUTO RISERVATO QUI
    # --- Config layout ---
    st.set_page_config(layout="wide",
                       page_title="Progetto_pareti_2025",
                       )

    # --- Caricamento dati da file ---
    @st.cache_data
    def load_distinta():
        return pd.read_excel("dati/Tabella_1.xlsx", dtype=str)

    @st.cache_data
    def load_barre():
        df = pd.read_excel("dati/Tabella_2.xlsx", dtype=str)
        df["L_BARRA"] = pd.to_numeric(df["L_BARRA"], errors="coerce")  # forza numerico, mette NaN se non valido
        return df


    # --- Caricamento dati ---
    df_distinta = load_distinta()
    df_barre = load_barre()

    df_merged_complete = pd.merge(
        df_distinta,
        df_barre,
        how="left",
        on="ARTICOLO_FIGLIO"
    )

    def sidebar_filtri_distinta(df_distinta):
        st.sidebar.header("🎛️ Filtri distinta")

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
                    lambda x: f"{x['CONCAT_3']} - {x['ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE']}", axis=1
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
                "C1_DESCRIZIONE",
                c1_opzioni,
                index=c1_opzioni.index(default_c1) if default_c1 in c1_opzioni else 0
            )
            filtered_c1 = filtered_cod[filtered_cod["C1_DESCRIZIONE"] == selected_c1]

            # Filtro 4: C2_DESCRIZIONE
            c2_opzioni = sorted(filtered_c1["C2_DESCRIZIONE"].dropna().unique())
            selected_c2 = st.sidebar.selectbox(
                "C2_DESCRIZIONE",
                c2_opzioni,
                index=c2_opzioni.index(default_c2) if default_c2 in c2_opzioni else 0
            )
            filtered_c2 = filtered_c1[filtered_c1["C2_DESCRIZIONE"] == selected_c2]

        # Scelta finale dell’articolo
        if selected_padre_input is not None:
            df_filtered_distinta = df_distinta[df_distinta["CONCAT_3"] == selected_padre_input]
            selected_padre = selected_padre_input
        else:
            codici_possibili = sorted(filtered_c2["CONCAT_3"].dropna().unique())
            selected_padre = st.sidebar.selectbox("Codice articolo", codici_possibili)
            df_filtered_distinta = df_distinta[df_distinta["CONCAT_3"] == selected_padre]

        return df_filtered_distinta, selected_padre, selected_macro, selected_cod_sistema, selected_c1, selected_c2


    # --- Nel main script dopo aver caricato df_distinta ---
    df_filtered_distinta, selected_padre, selected_macro, selected_cod_sistema, selected_c1, selected_c2 = sidebar_filtri_distinta(df_distinta)


    # Da qui puoi proseguire usando df_filtered_distinta e i filtri per la visualizzazione e ulteriori operazioni

    # --- Filtro barre ---
    articoli_filtrati = df_filtered_distinta["ARTICOLO_FIGLIO"].unique()
    df_barre_filtrato = df_barre[df_barre["ARTICOLO_FIGLIO"].isin(articoli_filtrati)]

    lunghezze_disponibili = sorted(df_barre_filtrato["L_BARRA"].dropna().unique())
    selected_length = st.sidebar.selectbox("Lunghezza barra", lunghezze_disponibili)

    df_barre_lunghezza = df_barre_filtrato[df_barre_filtrato["L_BARRA"] == selected_length]
    finiture_disponibili = sorted(df_barre_lunghezza["FINITURA"].dropna().unique())
    selected_finitura = st.sidebar.selectbox("Finitura", finiture_disponibili)

    # --- Merge tabelle --- ############ Questo è il df della distinta filtrata unito alla tabella delle barre disponibili in base al codice articolo #############
    df_merged_filtered = pd.merge(
        df_filtered_distinta,
        df_barre,
        how="left",
        on="ARTICOLO_FIGLIO"
    )

    ############ Lo stesso dataframe viene poi filtrato in base a lunghezza barra e finitura, AND condition #############
    df_merged_filtered = df_merged_filtered[
        (df_merged_filtered["L_BARRA"] == selected_length) &
        (df_merged_filtered["FINITURA"] == selected_finitura)
    ]

    # Calcolo peso grezzo con conversioni numeriche corrette
    if not df_merged_filtered.empty:
        df_merged_filtered["COEFFICIENTE"] = pd.to_numeric(df_merged_filtered["COEFFICIENTE"], errors='coerce').fillna(0)
        df_merged_filtered["GR/ML"] = pd.to_numeric(df_merged_filtered["GR/ML"], errors='coerce').fillna(0)
        df_merged_filtered["L_BARRA"] = pd.to_numeric(df_merged_filtered["L_BARRA"], errors='coerce').fillna(0)

        df_merged_filtered["PESO_GREZZO_KG"] = (df_merged_filtered["COEFFICIENTE"] * df_merged_filtered["GR/ML"] * df_merged_filtered["L_BARRA"]) / 1000000
        df_merged_filtered["KG/ML"] = df_merged_filtered["GR/ML"] / 1000

    # --- Layout ---
    st.title("Distinta base parete Unifor")
    #descrizione_finitura = df_barre[df_barre["FINITURA"] == selected_finitura]["DESCRIZIONE FINITURA"].iloc[0]
    df_desc = df_barre[df_barre["FINITURA"] == selected_finitura]
    if not df_desc.empty:
        descrizione_finitura = df_desc["DESCRIZIONE FINITURA"].iloc[0]
    else:
        descrizione_finitura = "Descrizione non disponibile"

    st.markdown(f"Visualizzazione per finitura `{selected_finitura}, {descrizione_finitura}` e lunghezza `{selected_length} mm`")

    #st.dataframe(df_merged_filtered)

    # Info articolo e metriche
    col0a, col0b,col0c = st.columns([1,1,1])
    tab1, tab2 = st.tabs(["Distinta base","Simulazione preordine"])

    if not df_merged_filtered.empty:
        with col0a:
            st.subheader(df_merged_filtered["CONCAT_3"].iloc[0])
            st.markdown(f"{df_merged_filtered["ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE"].iloc[0]}")
            st.markdown(f"***Codice sistema:*** {df_merged_filtered["COD_SISTEMA"].iloc[0]} - {df_merged_filtered["SISTEMA"].iloc[0]}")
            st.markdown(f"***Categoria:*** {df_merged_filtered["C1"].iloc[0]} {df_merged_filtered["C2"].iloc[0]} - {df_merged_filtered["C2_DESCRIZIONE"].iloc[0]}")
            st.markdown(f"***Unit:*** {df_merged_filtered["UNIT_ARTICOLO_PADRE"].iloc[0]} ")
        with col0b:
            st.metric("Peso barre grezze per gruppo", f"{df_merged_filtered['PESO_GREZZO_KG'].iloc[0]:.2f} kg")
        with col0b:
            if df_merged_filtered["C1"].iloc[0]!="P":
                st.metric("Peso specifico gruppo", f"{df_merged_filtered['KG/ML'].iloc[0]:.2f} kg/ml")

        with tab2:
            # Simulazione preordine alluminio
            st.subheader("Simulazione preordine alluminio")
            col5, col6 = st.columns([3,1])
            with col5:
                Qta_ordine = st.number_input(
                    "Inserisci quantità di pezzi o metri lineari se si tratta di orizzontali.",
                    min_value=1,
                    value=1,
                    step=1
                    )
            
                # Ora moltiplichi il peso o le quantità dei materiali figli per questa quantità
                def formula_ml(Qta_ordine, L_barra):
                    Val=(Qta_ordine/(L_barra/1000))*1.1
                    return Val
                def formula_cad(Qta_ordine):
                    Val=(Qta_ordine)
                    return Val
                df_simulazione=df_merged_filtered
                df_simulazione["PESO_TOTALE_KG"] = df_simulazione["PESO_GREZZO_KG"] * Qta_ordine
                df_simulazione = df_simulazione.rename(columns={
                    "ARTICOLO_FIGLIO": "ARTICOLO",
                    "COEFFICIENTE": "COEF",
                    "CODICE": "SEMILAV",
                    "PESO_GREZZO_KG": "KG_BARRA",
                    "PESO_TOTALE_KG": "KG_TOT",
                    "QTA_BARRE": "QTA_BARRE"
                    })
                if df_simulazione["UNIT_ARTICOLO_PADRE"].iloc[0]=="ML":
                    df_simulazione["QTA_BARRE"] = formula_ml(Qta_ordine,df_simulazione["L_BARRA"])
                    st.markdown(f"Formula q.tà barre:`(Qta_ordine/(L_barra/1000))*1.1`")
                elif df_simulazione["UNIT_ARTICOLO_PADRE"].iloc[0]=="N.":
                    st.markdown(f"Formula q.tà barre:`Qta_barre = Qta_ordine`")
                    df_simulazione["QTA_BARRE"] = formula_cad(Qta_ordine)

                st.dataframe(df_simulazione[[
                    "ARTICOLO",
                    "COEF",
                    "GR/ML",
                    "L_BARRA" ,
                    "SEMILAV",
                    "KG_BARRA",
                    "KG_TOT",
                    "QTA_BARRE"
                ]])
                    
    else:
        st.warning("Nessun dato disponibile con i filtri selezionati.")

    # --- Immagine gruppo ---
    img_row = df_filtered_distinta[df_filtered_distinta["CONCAT_3"] == selected_padre]
    img_path = None
    if not img_row.empty:
        raw_img_path = img_row["IMMAGINE_NOME_FILE"].iloc[0]
        filename = os.path.basename(raw_img_path)
        image_path = os.path.join("images", filename)
        if os.path.exists(image_path):
            img = Image.open(image_path)
            fixed_height = 260
            width_percent = fixed_height / float(img.size[1])
            new_width = int((float(img.size[0]) * float(width_percent)))
            img_resized = img.resize((new_width, fixed_height), Image.LANCZOS)
            with col0c:
                st.image(img_resized, use_container_width=False)
        else:
            with col0c:
                st.warning("🖼️ Immagine non trovata nella cartella `images`")

    st.markdown("---")
    with tab1:
        # Dataframe distinta base
        if not df_merged_filtered.empty:
            st.subheader("Distinta base componente")
            df_merged_filtered = df_merged_filtered.rename(columns={'ARTICOLO_FIGLIO_COD_CONC': 'CODICE_FIGLIO'})

            num_codici_univoci = df_filtered_distinta["ARTICOLO_FIGLIO_COD_CONC"].nunique()
            num_codici_univoci_filtrati = df_merged_filtered["CODICE_FIGLIO"].nunique()

            st.markdown(f"Codici presenti in distinta: **{num_codici_univoci_filtrati} di {num_codici_univoci}**")
            
            st.dataframe(df_merged_filtered[[
                "CODICE_FIGLIO", "ARTICOLO_FIGLIO", "COEFFICIENTE","ARTICOLO_FIGLIO_DESCRIZIONE",
                "CODICE", "CODICE_GREZZO",
                "L_BARRA", "GR/ML", "PESO_GREZZO_KG"
            ]], use_container_width=True)

            # Download CSV
            csv_df_merged_filtered = df_merged_filtered.to_csv(index=False)
            st.sidebar.download_button("Distinta componente", data=csv_df_merged_filtered, file_name="distinta_filtrata.csv", mime="text/csv")
            csv_df_merged_complete=df_merged_complete.to_csv(index=False)
            st.sidebar.download_button("Distinta completa", data=csv_df_merged_complete, file_name="distinta_completa.csv", mime="text/csv")

        else:
            st.error("Nessuna combinazione trovata per i filtri selezionati.")
            st.info("Prova a cambiare lunghezza o finitura.")
