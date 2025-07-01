import streamlit as st
import pandas as pd
from PIL import Image
import os

# --- Imposta layout wide ---
st.set_page_config(layout="wide")

# --- Simulated load functions (replace with file uploads or DB queries in real app) ---
def load_distinta():
    return pd.DataFrame({
        "COD_SISTEMA": ["RB"] * 9,
        "SISTEMA": ["RPSG66"] * 9,
        "C1": ["H"] * 9,
        "C2": ["A"] * 4 + ["B"] * 5,
        "C3": ["A"] * 9,
        "CODICE_PADRE": ["5RBHAA"] * 4 + ["5RBHBA"] * 5,
        "UNIT": ["ML"] * 9,
        "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE": [
            "Parete RP singolo vetro 66 - HA: orizzontale superiore altezza 65mm"] * 4 +
            ["Parete RP singolo vetro 66 - HB orizzontale inferiore regolabile"] * 5,
        "ARTICOLO_FIGLIO_TIPO": ["GUARNIZIONI", "GUARNIZIONI", "PROFILO", "PROFILO"] + ["PROFILO"] * 5,
        "ARTICOLO_FIGLIO_COD_CONC": ["5RBHAA00GU2", "5RBHAA00GU3", "5RBHAA0000A", "5RBHAA0000B", 
                                      "5RBHBA0000A", "5RBHBA0000B", "5RBHBA0000C", "5RBHBA0000D", "5RBHBA0000E"],
        "COEFFICIENTE": [2, 1, 1, 1, 1, 1, 1, 1, 1],
        "ARTICOLO_FIGLIO": ["500000GU00002", "500000GU00003", "TB52443", "TB47393", 
                             "TB50582", "TB50585", "TB50584", "TB50583", "TB50583"]
    })

def load_barre():
    return pd.DataFrame({
        "ARTICOLO_FIGLIO": [
            "TB47393", "TB52443", "TB47393", "TB52443",
            "TB50582", "TB50585", "TB50584", "TB50583",
            "TB50582", "TB50585", "TB50584", "TB50583",
            "TB50582", "TB50585", "TB50584", "TB50583"
        ],
        "L_BARRA": [
            3100, 3100, 6100, 6100,
            3100, 3100, 3100, 3100,
            6100, 6100, 6100, 6100,
            3100, 3100, 3100, 3100
        ],
        "FINITURA": [
            "BA", "BA", "BA", "BA",
            "BA", "BA", "BA", "BA",
            "BA", "BA", "BA", "BA",
            "KS", "KS", "KS", "KS"
        ],
        "FINITURA_DESCRIZIONE": [
            "BRILLANTATO"] * 12 + ["ANODIZZATO NERO"] * 4,
        "CODICE_BARRA_FINITA": [
            "NTB47393310BA", "NTB52443310BA", "NTB47393610BA", "NTB52443610BA",
            "NTB50582310BA", "NTB50585310BA", "NTB50584310BA", "NTB50583310BA",
            "NTB50582610BA", "NTB50585610BA", "NTB50584610BA", "NTB50583610BA",
            "NTB50582310KS", "NTB50585310KS", "NTB50584310KS", "NTB50583310KS"
        ],
        "CODICE_BARRA_GREZZA": [
            "LTB47393310", "LTB52443310", "LTB47393610", "LTB52443610",
            "LTB50582310", "LTB50585310", "LTB50584310", "LTB50583310",
            "LTB50582610", "LTB50585610", "LTB50584610", "LTB50583610",
            "LTB50582310", "LTB50585310", "LTB50584310", "LTB50583310"
        ],
        "GR/ML": [
            2592, 5961, 2592, 5961,
            639, 1624, 465, 342,
            639, 1624, 465, 342,
            639, 1624, 465, 342
        ]
    })

def load_images():
    return pd.DataFrame({
        "CODICE_PADRE": ["5RBHAA", "5RBHBA"],
        "IMAGE_PATH": ["images/5RBHAA.png", "images/5RBHBA.png"]
    })

# --- UI Sidebar ---
st.sidebar.header("🎛️ Parametri barra")
df_distinta = load_distinta()
df_barre = load_barre()
df_images = load_images()

# Filtri dinamici per selezione articolo
selected_cod_sistema = st.sidebar.selectbox("Codice sistema", sorted(df_distinta["COD_SISTEMA"].unique()))
filtered_by_cod = df_distinta[df_distinta["COD_SISTEMA"] == selected_cod_sistema]

selected_c1 = st.sidebar.selectbox("C1", sorted(filtered_by_cod["C1"].unique()))
filtered_by_c1 = filtered_by_cod[filtered_by_cod["C1"] == selected_c1]

selected_c2 = st.sidebar.selectbox("C2", sorted(filtered_by_c1["C2"].unique()))
filtered_by_c2 = filtered_by_c1[filtered_by_c1["C2"] == selected_c2]

# Rimuovo filtro su C3, passo direttamente a CODICE_PADRE
selected_codice_padre = st.sidebar.selectbox("Codice padre", sorted(filtered_by_c2["CODICE_PADRE"].unique()))
df_filtered_distinta = df_distinta[df_distinta["CODICE_PADRE"] == selected_codice_padre]

# Limita barre solo agli articoli filtrati
articoli_filtrati = df_filtered_distinta["ARTICOLO_FIGLIO"].unique()
df_barre_filtrato = df_barre[df_barre["ARTICOLO_FIGLIO"].isin(articoli_filtrati)]

# Filtra lunghezze disponibili per articoli filtrati
available_lunghezze = sorted(df_barre_filtrato["L_BARRA"].unique())
selected_length = st.sidebar.selectbox("Lunghezza barra", available_lunghezze)

# Filtra finiture disponibili per lunghezza selezionata e articoli filtrati
df_barre_filtrato_length = df_barre_filtrato[df_barre_filtrato["L_BARRA"] == selected_length]
available_finiture = sorted(df_barre_filtrato_length["FINITURA"].unique())
selected_finitura = st.sidebar.selectbox("Finitura", available_finiture)

# --- Merge con tabella barre ---
df_merged = pd.merge(
    df_filtered_distinta,
    df_barre,
    how="left",
    left_on=["ARTICOLO_FIGLIO"],
    right_on=["ARTICOLO_FIGLIO"]
)

# Filtro lunghezza e finitura
df_merged = df_merged[
    (df_merged["L_BARRA"] == selected_length) &
    (df_merged["FINITURA"] == selected_finitura)
]

if not df_merged.empty:
    df_merged["PESO_GREZZO_KG"] = (df_merged["COEFFICIENTE"] * df_merged["GR/ML"] * df_merged["L_BARRA"]) / 1000000
    df_merged["KG/ML"] = df_merged["GR/ML"] / 1000

# --- Layout Principale ---
st.title("Distinta base parete Unifor")
st.markdown(f"Visualizzazione per **finitura** `{selected_finitura}` e **lunghezza** `{selected_length} mm`")

col1, col2 = st.columns([2, 1])

if not df_merged.empty:
    df_summary = df_merged.groupby("CODICE_PADRE").agg({
        "COD_SISTEMA": "first",
        "SISTEMA": "first",
        "C1": "first",
        "C2": "first",
        "UNIT": "first",
        "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE": "first",
        "PESO_GREZZO_KG": "sum",
        "KG/ML": "sum"
    }).reset_index()

    df_summary_displayed = df_summary[[
        "CODICE_PADRE", "COD_SISTEMA", "SISTEMA", "C1", "C2",
        "UNIT", "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE"
    ]]

    with col1:
        peso = df_summary["PESO_GREZZO_KG"][0]
        peso_specifico = df_summary["KG/ML"][0]

        st.dataframe(df_summary_displayed, use_container_width=True)
        st.markdown(f"Peso barre grezze per gruppo`{peso:.2f} kg`, peso specifico gruppo`{peso_specifico:.2f} kg`")


else:
    with col1:
        st.info("Nessun dato da mostrare con i filtri selezionati.")

cod_padre = df_merged["CODICE_PADRE"].iloc[0] if not df_merged.empty else None
if cod_padre:
    img_row = df_images[df_images["CODICE_PADRE"] == cod_padre]
    if not img_row.empty:
        image_path = img_row.iloc[0]["IMAGE_PATH"]
        if os.path.exists(image_path):
            img = Image.open(image_path)
            fixed_height = 260
            width_percent = (fixed_height / float(img.size[1]))
            new_width = int((float(img.size[0]) * float(width_percent)))
            img_resized = img.resize((new_width, fixed_height), Image.ANTIALIAS)

            with col2:
                st.image(img_resized, use_container_width=False)
        else:
            with col2:
                st.warning(f"🖼️ Immagine non trovata per `{cod_padre}`")


st.markdown("---")

if df_merged.empty:
    st.error(f"Nessuna combinazione trovata per lunghezza {selected_length} mm e finitura {selected_finitura}.")
    st.info("Prova a modificare i filtri.")
else:
    st.dataframe(df_merged[[
        "CODICE_PADRE", "ARTICOLO_FIGLIO", "CODICE_BARRA_FINITA", "CODICE_BARRA_GREZZA",
        "COEFFICIENTE", "L_BARRA", "GR/ML", "PESO_GREZZO_KG"
    ]], use_container_width=True)

    #peso_totale = df_merged["PESO_GREZZO_KG"].sum()
    #st.markdown(f"### ⚖️ Peso grezzo totale: **{peso_totale:.2f} kg**")

    csv = df_merged.to_csv(index=False)
    st.download_button("📥 Scarica CSV", data=csv, file_name="distinta_filtrata.csv", mime="text/csv")
