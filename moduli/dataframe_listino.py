import pandas as pd
import numpy as np

def dataframe_listino(df_distinta, df_profili, df_costi_pareti):
    # Unione base con info peso per metro lineare
    df_listino = pd.merge(
        df_distinta,
        df_profili[["ARTICOLO_FIGLIO", "KG/ML"]],
        how="left",
        on="ARTICOLO_FIGLIO"
    )

    # Parametri base
    k_listino = 3.24
    costo_alluminio = 5
    costo_finitura = 4
    costo_guar_fer_ml=4
    costo_guar_fer_ml_tr=2
    costo_imballo_cad=2
    riferimento_barra_porte = 3100  # in mm
    riferimento_barra_ml = 1000     # in mm

    # --- Calcoli comuni per PORTE e VERTICALI ---
    # Lista di condizioni: (campo da controllare, valore da confrontare)
    condizioni_comuni = [
        ("C1", "P"),   # PORTE
        ("C2", "AP"),  # PORTE (AP)
        ("C2", "IP"),  # PORTE (IP)
        ("C1", "V")    # VERTICALI
    ]

    # Tracciamo le maschere per uso successivo
    maschere_calcolate = []

    for campo, valore in condizioni_comuni:
        mask = (df_listino["ARTICOLO_FIGLIO_TIPO"] == "PROFILO") & (df_listino[campo] == valore)
        maschere_calcolate.append(mask)
        
        df_listino.loc[mask, "IMPEGNO_ALLUMINIO"] = (
            (riferimento_barra_porte / 1000) * df_listino["KG/ML"] * df_listino["COEFFICIENTE"]
        )
        df_listino.loc[mask, "COSTO_ALLUMINIO"] = (
            df_listino.loc[mask, "IMPEGNO_ALLUMINIO"] * costo_alluminio
        )
        df_listino.loc[mask, "COSTO_FINITURA"] = (
            (riferimento_barra_porte / 1000) * df_listino["COEFFICIENTE"] * costo_finitura
        )

    # --- ORIZZONTALI (tutti gli altri PROFILI non ancora calcolati) ---
    # Combina tutte le maschere già applicate
    mask_orizz = (df_listino["ARTICOLO_FIGLIO_TIPO"] == "PROFILO") & ~np.logical_or.reduce(maschere_calcolate)

    df_listino.loc[mask_orizz, "IMPEGNO_ALLUMINIO"] = (
        (riferimento_barra_ml / 1000) * df_listino["KG/ML"] * df_listino["COEFFICIENTE"]
    )
    df_listino.loc[mask_orizz, "COSTO_ALLUMINIO"] = (
        df_listino.loc[mask_orizz, "IMPEGNO_ALLUMINIO"] * costo_alluminio
    )
    df_listino.loc[mask_orizz, "COSTO_FINITURA"] = (
        (riferimento_barra_ml / 1000) * df_listino["COEFFICIENTE"] * costo_finitura
    )

    # Colonne finali
    df_listino = df_listino[[
        "CONCAT_3","C1","C2", "ARTICOLO_FIGLIO_TIPO", "ARTICOLO_FIGLIO_COD_CONC",
        "ARTICOLO_FIGLIO", "COEFFICIENTE", "KG/ML",
        "IMPEGNO_ALLUMINIO", "COSTO_ALLUMINIO", "COSTO_FINITURA"
    ]]

    # Raggruppamento per codice articolo
    df_listino_grouped = (
    df_listino.groupby("CONCAT_3").agg({
        "C1": "first",
        "C2": "first",
        "KG/ML": "sum",
        "IMPEGNO_ALLUMINIO": "sum",
        "COSTO_ALLUMINIO": "sum",
        "COSTO_FINITURA": "sum"
    }).reset_index()
    )
    df_listino_grouped["COSTO_GUAR_FER"]=0
    df_listino_grouped["COSTO_IMBALLO"]=0

    #Altri costi spalmati già sui padri
    # --- VERTICALI (C1 == V) ---
    mask_vert_grouped = (df_listino_grouped["C1"] == "V")
    df_listino_grouped.loc[mask_vert_grouped, "COSTO_GUAR_FER"] = costo_guar_fer_ml*riferimento_barra_porte/1000
    df_listino_grouped.loc[mask_vert_grouped, "COSTO_IMBALLO"] = costo_imballo_cad
    
    # --- ORIZZONTALI (C1 == H) ---
    mask_horiz_grouped = (df_listino_grouped["C1"] == "H") & ((df_listino_grouped["C2"] == "A") |(df_listino_grouped["C2"] == "B"))
    df_listino_grouped.loc[mask_horiz_grouped, "COSTO_GUAR_FER"] = costo_guar_fer_ml*riferimento_barra_ml/1000
    df_listino_grouped.loc[mask_horiz_grouped, "COSTO_IMBALLO"] = costo_imballo_cad

    # --- VERTICALI (C1 == TR) ---
    mask_tr_grouped = (df_listino_grouped["C1"] == "TR")
    df_listino_grouped.loc[mask_tr_grouped, "COSTO_GUAR_FER"] = costo_guar_fer_ml_tr*riferimento_barra_ml/1000
    df_listino_grouped.loc[mask_tr_grouped, "COSTO_IMBALLO"] = costo_imballo_cad

    df_listino_grouped = df_listino_grouped.merge(
        df_costi_pareti[["CONCAT_3", "COSTO_LAV", "ALTRI_COSTI"]],
        on="CONCAT_3",
        how="left"
    )

    columns_to_sum = [
        "COSTO_GUAR_FER", "COSTO_IMBALLO", "COSTO_LAV",
        "ALTRI_COSTI", "COSTO_ALLUMINIO", "COSTO_FINITURA"
    ]

    df_listino_grouped["COSTO_TOT"] = df_listino_grouped[columns_to_sum].fillna(0).sum(axis=1)

    df_listino_grouped["LISTINO"]= df_listino_grouped["COSTO_TOT"]*k_listino


    return df_listino, df_listino_grouped, df_costi_pareti,riferimento_barra_porte,riferimento_barra_ml,costo_alluminio,costo_finitura
