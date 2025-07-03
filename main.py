import streamlit as st
import pandas as pd
from PIL import Image
import os

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

selected_cod_sistema = st.sidebar.selectbox("Codice sistema", sorted(filtered_macro["COD_SISTEMA"].unique()))
filtered_cod = filtered_macro[filtered_macro["COD_SISTEMA"] == selected_cod_sistema]

selected_c1 = st.sidebar.selectbox("C1", sorted(filtered_cod["C1"].unique()))
filtered_c1 = filtered_cod[filtered_cod["C1"] == selected_c1]

selected_c2 = st.sidebar.selectbox("C2", sorted(filtered_c1["C2"].unique()))
filtered_c2 = filtered_c1[filtered_c1["C2"] == selected_c2]

# Selezione gruppo
selected_padre = st.sidebar.selectbox("Codice articolo", sorted(filtered_c2["CONCAT_3"].unique()))
df_filtered_distinta = df_distinta[df_distinta["CONCAT_3"] == selected_padre]

# --- Filtro barre ---
articoli_filtrati = df_filtered_distinta["ARTICOLO_FIGLIO"].unique()
df_barre_filtrato = df_barre[df_barre["ARTICOLO_FIGLIO"].isin(articoli_filtrati)]

lunghezze_disponibili = sorted(df_barre_filtrato["L_BARRA"].dropna().unique())
selected_length = st.sidebar.selectbox("Lunghezza barra", lunghezze_disponibili)

df_barre_lunghezza = df_barre_filtrato[df_barre_filtrato["L_BARRA"] == selected_length]
finiture_disponibili = sorted(df_barre_lunghezza["FINITURA"].dropna().unique())
selected_finitura = st.sidebar.selectbox("Finitura", finiture_disponibili)

# --- Merge tabelle ---
df_merged = pd.merge(
    df_filtered_distinta,
    df_barre,
    how="left",
    on="ARTICOLO_FIGLIO"
)

df_merged = df_merged[
    (df_merged["L_BARRA"] == selected_length) &
    (df_merged["FINITURA"] == selected_finitura)
]

# Calcolo peso grezzo con conversioni numeriche corrette
if not df_merged.empty:
    df_merged["COEFFICIENTE"] = pd.to_numeric(df_merged["COEFFICIENTE"], errors='coerce').fillna(0)
    df_merged["GR/ML"] = pd.to_numeric(df_merged["GR/ML"], errors='coerce').fillna(0)
    df_merged["L_BARRA"] = pd.to_numeric(df_merged["L_BARRA"], errors='coerce').fillna(0)

    df_merged["PESO_GREZZO_KG"] = (df_merged["COEFFICIENTE"] * df_merged["GR/ML"] * df_merged["L_BARRA"]) / 1000000
    df_merged["KG/ML"] = df_merged["GR/ML"] / 1000

# --- Layout ---
st.title("Distinta base parete Unifor")
descrizione_finitura = df_barre[df_barre["FINITURA"] == selected_finitura]["DESCRIZIONE FINITURA"].iloc[0]
st.markdown(f"Visualizzazione per finitura `{selected_finitura}, {descrizione_finitura}` e lunghezza `{selected_length} mm`")



if not df_merged.empty:
    df_summary = df_merged.groupby("CONCAT_3").agg({
        "COD_SISTEMA": "first",
        "SISTEMA": "first",
        "C1": "first",
        "C2": "first",
        "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE_BREVE": "first",
        "UNIT_ARTICOLO_PADRE": "first",
        "PESO_GREZZO_KG": "sum",
        "KG/ML": "sum"
    }).reset_index()
    st.dataframe(df_summary, use_container_width=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        col3, col4 = st.columns([1, 1])
        #st.markdown(f"Peso barre grezze per gruppo: `{df_summary['PESO_GREZZO_KG'].iloc[0]:.2f}kg`")
        #st.markdown(f"Peso specifico gruppo: `{df_summary['KG/ML'].iloc[0]:.2f} kg/ml`")
        with col3:
            st.metric("Peso barre grezze per gruppo", f"{df_summary['PESO_GREZZO_KG'].iloc[0]:.2f} kg")
        with col4:
            st.metric("Peso specifico gruppo", f"{df_summary['KG/ML'].iloc[0]:.2f} kg/ml")

else:
    with col1: # type: ignore
        st.warning("Nessun dato disponibile con i filtri selezionati.")

# --- Immagine gruppo ---
img_row = df_filtered_distinta[df_filtered_distinta["CONCAT_3"] == selected_padre]
img_path = None
if not img_row.empty:
    raw_img_path = img_row["IMMAGINE_NOME_FILE"].iloc[0]
    filename = os.path.basename(raw_img_path)
    image_path = os.path.join("images", filename)
    
    st.text(f"Path immagine: {image_path}")
    st.text(f"File esiste? {os.path.exists(image_path)}")

    if os.path.exists(image_path):
        img = Image.open(image_path)
        fixed_height = 260
        width_percent = fixed_height / float(img.size[1])
        new_width = int((float(img.size[0]) * float(width_percent)))
        img_resized = img.resize((new_width, fixed_height), Image.LANCZOS)
        with col2:
            st.image(img_resized, use_container_width=False)
    else:
        with col2:
            st.warning("🖼️ Immagine non trovata nella cartella `images`")

st.markdown("---")

# --- Tabella componenti dettagliati ---
if not df_merged.empty:
    df_merged = df_merged.rename(columns={'ARTICOLO_FIGLIO_COD_CONC': 'CODICE_FIGLIO'})
    st.dataframe(df_merged[[
        "CODICE_FIGLIO", "ARTICOLO_FIGLIO", "ARTICOLO_FIGLIO_DESCRIZIONE",
        "CODICE", "CODICE_GREZZO", "COEFFICIENTE",
        "L_BARRA", "GR/ML", "PESO_GREZZO_KG"
    ]], use_container_width=True)

    # Download CSV
    with col2:
        csv_df_merged = df_merged.to_csv(index=False)
        st.download_button("Scarica distinta componente", data=csv_df_merged, file_name="distinta_filtrata.csv", mime="text/csv")
        csv_df_merged_complete=df_merged_complete.to_csv(index=False)
        st.download_button("Scarica distinta completa", data=csv_df_merged_complete, file_name="distinta_completa.csv", mime="text/csv")

else:
    st.error("Nessuna combinazione trovata per i filtri selezionati.")
    st.info("Prova a cambiare lunghezza o finitura.")
