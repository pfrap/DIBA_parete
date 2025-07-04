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
    st.set_page_config(layout="wide")

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

    # --- UI Sidebar ---
    st.sidebar.header("🎛️ Filtri Distinta")

    # Filtri dinamici
    selected_macro = st.sidebar.selectbox("Macro sistema", sorted(df_distinta["MACRO_SISTEMA"].unique()))
    filtered_macro = df_distinta[df_distinta["MACRO_SISTEMA"] == selected_macro]

    selected_cod_sistema = st.sidebar.selectbox("Codice sistema", sorted(filtered_macro["SISTEMA"].unique()))
    filtered_cod = filtered_macro[filtered_macro["SISTEMA"] == selected_cod_sistema]

    selected_c1 = st.sidebar.selectbox("C1_DESCRIZIONE", sorted(filtered_cod["C1_DESCRIZIONE"].unique()))
    filtered_c1 = filtered_cod[filtered_cod["C1_DESCRIZIONE"] == selected_c1]


    selected_c2 = st.sidebar.selectbox("C2_DESCRIZIONE", sorted(filtered_c1["C2_DESCRIZIONE"].unique()))
    filtered_c2 = filtered_c1[filtered_c1["C2_DESCRIZIONE"] == selected_c2]


    # Selezione gruppo
    selected_padre = st.sidebar.selectbox("Codice articolo", sorted(filtered_c2["CONCAT_3"].unique()))
    df_filtered_distinta = df_distinta[df_distinta["CONCAT_3"] == selected_padre] ############ Questo è il df della distinta filtrata #############

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
