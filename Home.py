import streamlit as st
import pandas as pd
from PIL import Image
import os
from moduli.login import login
from moduli.sidebar_filtri_home import sidebar_filtri_distinta
from moduli.formule_preordine import formula_ml, formula_cad
from moduli.dataframe_listino import dataframe_listino

def show():
    st.title("Analisi articoli")

    # Caricamento dati
    df_distinta = pd.read_excel("dati/Tabella_articoli.xlsx", dtype=str)
    df_barre = pd.read_excel("dati/Tabella_barre.xlsx", dtype=str)
    df_profili = pd.read_excel("dati/Profili_r00.xlsx", dtype=str)
    df_costi_pareti = pd.read_excel("dati/Costi_pareti_r00.xlsx", dtype=str)
    df_costi_finiture = pd.read_excel("dati/Costi_finiture.xlsx", dtype=str)

    df_distinta_vendita = pd.read_excel("dati/Tabella_vendita.xlsx", dtype=str)

    # Calcoli e formattazione
    df_distinta["COEFFICIENTE"] = pd.to_numeric(df_distinta["COEFFICIENTE"], errors='coerce').fillna(0)
    df_barre["GR/ML"] = pd.to_numeric(df_barre["GR/ML"], errors='coerce').fillna(0)
    df_barre["L_BARRA"] = pd.to_numeric(df_barre["L_BARRA"], errors='coerce')
    df_barre["KG/ML"] = df_barre["GR/ML"] / 1000
    df_profili["PESO_(gr/ml)"] = pd.to_numeric(df_profili["PESO_(gr/ml)"], errors="coerce")
    df_profili["KG/ML"] = df_profili["PESO_(gr/ml)"] / 1000
    df_costi_pareti["COSTO_LAV"] = pd.to_numeric(df_costi_pareti["COSTO_LAV"], errors="coerce")
    df_costi_pareti["ALTRI_COSTI"] = pd.to_numeric(df_costi_pareti["ALTRI_COSTI"], errors="coerce")


    # Distinta merged per barre e diba AS400 (non viene più utilizzato in seguito)
    df_merged_complete = pd.merge(
        df_distinta,
        df_barre,
        how="left",
        on="ARTICOLO_FIGLIO"
    )

    df_merged_complete["PESO_GREZZO_KG"] = (df_merged_complete["COEFFICIENTE"] * df_merged_complete["GR/ML"] * df_merged_complete["L_BARRA"]) / 1000000
    df_merged_complete_grouped_peso = df_merged_complete.groupby("CONCAT_3")[["PESO_GREZZO_KG", "KG/ML"]].sum()

    # Creazione dataframe listino
    df_listino, df_listino_grouped,df_listino_vendita,df_costi_pareti,riferimento_barra_porte,riferimento_barra_ml,costo_alluminio=dataframe_listino(df_distinta, 
                                                                                                                                                 df_profili,
                                                                                                                                                 df_costi_pareti, 
                                                                                                                                                 df_distinta_vendita,
                                                                                                                                                 df_costi_finiture)
    st.session_state["df_listino_vendita"] = df_listino_vendita

    df_listino_grouped["LISTINO"] = pd.to_numeric(df_listino_grouped["LISTINO"], errors="coerce")
    st.session_state["df_listino_grouped"] = df_listino_grouped

    # Selezione multipla articoli in sidebar
    df_filtered_distinta, selected_padre, selected_macro, selected_cod_sistema, selected_c1, selected_c2 = sidebar_filtri_distinta(df_distinta)

    # Questo è il df della distinta filtrata unito alla tabella delle barre disponibili in base al codice articolo
    df_merged_filtered = pd.merge(
        df_filtered_distinta,
        df_barre,
        how="left",
        on="ARTICOLO_FIGLIO"
    )

    #######################################################################################
    #######################################################################################
    #######################################################################################

    # --- Layout ---
    if not df_merged_filtered.empty:
        #Diz per visualizzazione in rinomina non modificante il dataframe, utilizzato in seguito
        colrename_diz={"MACRO_SISTEMA": "FAMIGLIA",
        "CONCAT_3": "ARTICOLO",
        "C1": "CATEGORIA",
        "C1_DESCRIZIONE": "CAT_DESCRIZIONE",
        "C2": "SOTTOCATEGORIA",
        "C2_DESCRIZIONE": "SUBCAT_DESCRIZIONE",
        "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE_EN": "DESCRIZIONE EN",
        "ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE": "DESCRIZIONE",
        "UNIT_ARTICOLO_PADRE": "UNIT",
        "ARTICOLO_FIGLIO_TIPO": "TIPO_FIGLIO",
        "ARTICOLO_FIGLIO_COD_CONC": "CODICE_ARTICOLO_FIGLIO",
        "COEFFICIENTE": "COEF",
        "CODICE": "SEMILAV",
        "PESO_GREZZO_KG": "KG_BARRA",
        "PESO_TOTALE_KG": "KG_TOT",
        }
        st.session_state["colrename_diz"] = colrename_diz

        st.subheader(df_merged_filtered["CONCAT_3"].iloc[0])
        st.markdown(f"{df_merged_filtered["ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE"].iloc[0]}")
        col0a, col0b,col0c = st.columns([2,1,1])
        tab_diba, tab_listino = st.tabs(["Distinta base", "Formazione listino"])
        with col0a:
            st.markdown(f"***Codice sistema:*** {df_merged_filtered["COD_SISTEMA"].iloc[0]} - {df_merged_filtered["SISTEMA"].iloc[0]}")
            st.markdown(f"***Categoria:*** {df_merged_filtered["C1"].iloc[0]} {df_merged_filtered["C2"].iloc[0]} - {df_merged_filtered["C2_DESCRIZIONE"].iloc[0]}")
            st.markdown(f"***Unit:*** {df_merged_filtered["UNIT_ARTICOLO_PADRE"].iloc[0]} ")
            st.metric("Prezzo listino", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['LISTINO'].iloc[0]:.2f} €/unit")

        with col0b:
            if df_merged_filtered["C1"].iloc[0]=="P":
                st.metric("Impegno alluminio", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['IMPEGNO_ALLUMINIO'].iloc[0]:.2f} kg/cad")
            elif df_merged_filtered["C1"].iloc[0]=="V":
                st.metric("Impegno alluminio", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['IMPEGNO_ALLUMINIO'].iloc[0]:.2f} kg/cad")
                st.metric("Peso specifico gruppo", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['KG/ML'].iloc[0]:.2f} kg/ml")
            elif (df_merged_filtered["C1"].iloc[0]=="H") & ((df_merged_filtered["C2"].iloc[0]=="AP")|(df_merged_filtered["C2"].iloc[0]=="IP")):
                st.metric("Impegno alluminio", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['IMPEGNO_ALLUMINIO'].iloc[0]:.2f} kg/cad")
                st.metric("Peso specifico gruppo", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['KG/ML'].iloc[0]:.2f} kg/ml")
            else:
                st.metric("Peso specifico gruppo", f"{df_listino_grouped[df_listino_grouped["CONCAT_3"]==selected_padre]['KG/ML'].iloc[0]:.2f} kg/ml")
        
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
        with tab_diba:
            dibacolsel_1, dibacolsel_2 = st.columns([1,1])
            with dibacolsel_2:
                
                ###############################################################################################
                # Filtro barre disponibili e finiture
                articoli_filtrati = df_filtered_distinta["ARTICOLO_FIGLIO"].unique()
                df_barre_filtrato = df_barre[df_barre["ARTICOLO_FIGLIO"].isin(articoli_filtrati)]
                
                lunghezze_disponibili = sorted(df_barre_filtrato["L_BARRA"].dropna().unique())
                selected_length = st.selectbox("Lunghezza barra da AS400", lunghezze_disponibili)

                df_barre_lunghezza = df_barre_filtrato[df_barre_filtrato["L_BARRA"] == selected_length]
                finiture_disponibili = sorted(df_barre_lunghezza["FINITURA"].dropna().unique())
                selected_finitura = st.selectbox("Finiture da AS400", finiture_disponibili)
                df_desc = df_barre[df_barre["FINITURA"] == selected_finitura]
                if not df_desc.empty:
                    descrizione_finitura = df_desc["DESCRIZIONE FINITURA"].iloc[0]
                else:
                    descrizione_finitura = "Descrizione non disponibile"

                # Lo stesso dataframe viene poi filtrato in base a lunghezza barra e finitura, AND condition
                df_merged_filtered_diba = df_merged_filtered[
                    (df_merged_filtered["L_BARRA"] == selected_length) &
                    (df_merged_filtered["FINITURA"] == selected_finitura)
                ]
            with dibacolsel_1:
                st.subheader(f"Visualizzazione per:")
                st.markdown(f"Lunghezza barra `{selected_length} mm`")
                st.markdown(f"Finitura `{selected_finitura}, {descrizione_finitura}`")

                # Calcolo peso grezzo con conversioni numeriche corrette
                if not df_merged_filtered_diba.empty:
                    df_merged_filtered_diba["PESO_GREZZO_KG"] = (df_merged_filtered_diba["COEFFICIENTE"] * df_merged_filtered_diba["GR/ML"] * df_merged_filtered_diba["L_BARRA"]) / 1000000
                    # Calcolo peso raggruppato per articolo
                    df_grouped_peso_articoli = df_merged_filtered_diba.groupby("CONCAT_3")[["PESO_GREZZO_KG", "KG/ML"]].sum()

            tab_diba_1, tab_diba_2 = st.tabs(["Verifica diba", "Simulazione preordine"])
            with tab_diba_1:
                    dibacol1, dibacol2 = st.columns([3,1])
                    # Dataframe distinta base
                    if not df_merged_filtered_diba.empty:
                        with dibacol1:
                            st.subheader("Distinta base componente")
                            df_merged_filtered_diba = df_merged_filtered_diba.rename(columns={'ARTICOLO_FIGLIO_COD_CONC': 'CODICE_FIGLIO'})

                        num_codici_univoci = df_filtered_distinta["ARTICOLO_FIGLIO_COD_CONC"].nunique()
                        num_codici_univoci_filtrati = df_merged_filtered_diba["CODICE_FIGLIO"].nunique()

                        st.markdown(f"Codici presenti in distinta: **{num_codici_univoci_filtrati} di {num_codici_univoci}**")
                        
                        st.dataframe(df_merged_filtered_diba[[
                            "CODICE_FIGLIO", "ARTICOLO_FIGLIO", "COEFFICIENTE","ARTICOLO_FIGLIO_DESCRIZIONE",
                            "CODICE", "CODICE_GREZZO",
                            "L_BARRA", "PESO_LORDO","GR/ML", "PESO_GREZZO_KG"
                        ]], use_container_width=True)

                        with dibacol2:
                            csv_df_merged_filtered_diba = df_merged_filtered_diba.to_csv(index=False)
                            st.download_button("Scarica csv distinta componente", data=csv_df_merged_filtered_diba, file_name="distinta_filtrata.csv", mime="text/csv")
                    else:
                        with tab_diba_1:
                            st.error("Nessuna combinazione trovata per i filtri selezionati.")
                            st.info("Prova a cambiare lunghezza o finitura.")
                        with tab_diba_2:
                            st.error("Nessuna combinazione trovata per i filtri selezionati.")
                            st.info("Prova a cambiare lunghezza o finitura.")
                ###############################################################################################

            with tab_diba_2:
                if not df_merged_filtered_diba.empty:
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
                        df_simulazione=df_merged_filtered_diba
                        df_simulazione["PESO_TOTALE_KG"] = df_simulazione["PESO_GREZZO_KG"] * Qta_ordine
                    
                        if df_simulazione["UNIT_ARTICOLO_PADRE"].iloc[0]=="ML":
                            df_simulazione["QTA_BARRE"] = formula_ml(Qta_ordine,df_simulazione["L_BARRA"])
                            st.markdown(f"Formula q.tà barre:`(Qta_ordine/(L_barra/1000))*1.1`")
                        elif df_simulazione["UNIT_ARTICOLO_PADRE"].iloc[0]=="N.":
                            st.markdown(f"Formula q.tà barre:`Qta_barre = Qta_ordine*Coefficiente`")
                            df_simulazione["QTA_BARRE"] = formula_cad(Qta_ordine,df_simulazione["COEFFICIENTE"])

                        st.dataframe(df_simulazione[[
                            "ARTICOLO_FIGLIO",
                            "COEFFICIENTE",
                            "GR/ML",
                            "L_BARRA" ,
                            "CODICE",
                            "PESO_GREZZO_KG",
                            "PESO_TOTALE_KG",
                            "QTA_BARRE"
                        ]].rename(columns=colrename_diz))                
    else:
        st.warning("Nessun dato disponibile con i filtri selezionati.")

    with tab_listino:
        subcollist1, subcollist2 = st.columns([1,1])
        # Formazione listino
        if not df_merged_filtered.empty:
            with subcollist1:
                st.subheader("Formazione listino")
                if df_merged_filtered["C1"].iloc[0]=="P":
                    st.markdown(f"L. barra di riferimento per calcolo impegno alluminio: `{riferimento_barra_porte}`")

            # Estrazione finiture disponibili per il selected_padre
            finiture_listino = df_listino[df_listino["CONCAT_3"] == selected_padre]["FINITURA"].dropna().unique()
            finiture_listino = sorted(finiture_listino)
            with subcollist2:
                # Dropdown filtro finitura
                selected_finitura_listino = st.selectbox("Finiture da listino", options= finiture_listino)

            lista_col_listino = [
                "CONCAT_3",
                "ARTICOLO_FIGLIO_TIPO",
                "ARTICOLO_FIGLIO_COD_CONC",
                "ARTICOLO_FIGLIO",
                "COEFFICIENTE",
                "KG/ML",
                "IMPEGNO_ALLUMINIO",
                "COSTO_ALLUMINIO",
                "FINITURA",
                "COSTO_FINITURA_UNIT",
                "COSTO_FINITURA"
            ]
            lista_col_listino_grouped = [
                "CONCAT_3",
                "UNIT_ARTICOLO_PADRE",
                "FINITURA",
                "COSTO_FINITURA",
                "IMPEGNO_ALLUMINIO",
                "COSTO_ALLUMINIO",
                "COSTO_GUAR_FER",
                "COSTO_IMBALLO",
                "COSTO_LAV",
                "ALTRI_COSTI",
                "COSTO_TOT",
                "LISTINO"
            ]

            # Filtra direttamente in base alla finitura selezionata
            df_listino_filtered = df_listino[
                (df_listino["CONCAT_3"] == selected_padre) &
                (df_listino["FINITURA"] == selected_finitura_listino)
            ]
            df_listino_grouped_filtered = df_listino_grouped[
                (df_listino_grouped["CONCAT_3"] == selected_padre) &
                (df_listino_grouped["FINITURA"] == selected_finitura_listino)
            ]
            
            # Recupera la descrizione e il costo unitario della finitura selezionata
            if not df_listino_filtered.empty:
                descrizione_finitura = df_listino_filtered["DESCRIZIONE_FINITURA"].iloc[0] if "DESCRIZIONE_FINITURA" in df_listino_filtered.columns else ""
                costo_finitura_unitario = df_listino_filtered["COSTO_FINITURA_UNIT"].iloc[0]
            else:
                descrizione_finitura = ""
                costo_finitura_unitario = 0.0

            with subcollist1:
                st.markdown(f"Costo alluminio: `{costo_alluminio} €/kg`")
                st.markdown(f"Finitura: `{selected_finitura_listino} - {descrizione_finitura}` Costo finitura: `{costo_finitura_unitario} €/ml/profilo`")

            st.dataframe(df_listino_grouped_filtered[lista_col_listino_grouped].rename(columns=colrename_diz))
            st.dataframe(df_listino_filtered[lista_col_listino].rename(columns=colrename_diz))

    # Download CSV distinta completa
    csv_df_merged_complete=df_merged_complete.to_csv(index=False)
    st.sidebar.download_button("Distinta completa", data=csv_df_merged_complete, file_name="distinta_completa.csv", mime="text/csv")
