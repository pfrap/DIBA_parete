import streamlit as st
import pandas as pd
from io import BytesIO

def show():
    st.title("Gestione quotazioni")

    # Inizializza dizionario se non esiste
    if 'df_quotazione' not in st.session_state:
        st.session_state['df_quotazione'] = {}

    df_quotazione = st.session_state['df_quotazione']

    # Sidebar per Import/Export
    with st.sidebar:
        st.header("📁 Import/Export")

        uploaded_file = st.file_uploader("📤 Importa quotazione (Excel)", type=["xlsx"])
        if uploaded_file:
            xls = pd.read_excel(uploaded_file, sheet_name=None)
            st.session_state["df_quotazione"] = xls
            st.success("✅ Quotazione importata correttamente.")
            st.rerun()

        if df_quotazione and st.button("📥 Esporta quotazione corrente"):
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                for key, df in df_quotazione.items():
                    df.to_excel(writer, sheet_name=key, index=False)
            st.download_button(
                label="⬇️ Scarica file Excel",
                data=buffer.getvalue(),
                file_name="quotazione_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Visualizzazione e gestione sezioni
    for nome_sezione, df_sezione in df_quotazione.items():
        st.subheader(f"Sezione:`{nome_sezione}`")

        # Colonne visibili e modificabili
        col_vis = ['SISTEMA', 'C1_DESCRIZIONE', 'CONCAT_3', 'ID_COMPONENTE_ARTICOLO_PADRE_DESCRIZIONE', 'UNIT_ARTICOLO_PADRE', 'LISTINO']
        col_agg = ['Q_TA', 'TOTALE', 'SELEZIONA']
        tutte_colonne = col_vis + col_agg

        # Aggiungi colonne mancanti se non presenti
        for col in col_agg:
            if col not in df_sezione.columns:
                if col == 'Q_TA':
                    df_sezione[col] = 1.0
                elif col == 'TOTALE':
                    df_sezione[col] = df_sezione.get("LISTINO", 0.0)
                else:
                    df_sezione[col] = False

        # Layout a due colonne per editor e totali
        col_editor, col_totale = st.columns([10, 1])

        with col_editor:
            # Editor senza la colonna TOTALE
            edited_df = st.data_editor(
                df_sezione[[c for c in tutte_colonne if c != 'TOTALE']],  # Esclude TOTALE
                key=f"editor_{nome_sezione}",
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                disabled=[c for c in tutte_colonne if c not in ['Q_TA', 'SELEZIONA']]
            )

        # Ricalcola colonna TOTALE in tempo reale
        edited_df["TOTALE"] = edited_df["LISTINO"] * edited_df["Q_TA"]

        # Aggiorna df_quotazione con modifiche su Q_TA e SELEZIONA
        df_quotazione[nome_sezione].update(edited_df)

        with col_totale:
            # Mostra solo la colonna TOTALE come anteprima aggiornata
            st.data_editor(
                edited_df[["TOTALE"]],
                key=f"totali_{nome_sezione}",
                use_container_width=True,
                hide_index=True,
                disabled=True
            )

        # Selezionati
        selezionati = edited_df[edited_df['SELEZIONA'] == True]

        # Azioni: Elimina o Duplica
        az1, az2 = st.columns(2)
        with az1:
            if st.button(f"🗑 Elimina selezionati ({nome_sezione})"):
                df_filtrato = df_sezione[~edited_df['SELEZIONA']].reset_index(drop=True)
                df_quotazione[nome_sezione] = df_filtrato
                st.rerun()
        with az2:
            if st.button(f"➕ Duplica selezionati ({nome_sezione})"):
                duplicati = df_sezione[edited_df['SELEZIONA']].copy()
                duplicati['SELEZIONA'] = False
                df_quotazione[nome_sezione] = pd.concat([df_sezione, duplicati], ignore_index=True)
                st.rerun()

        # Totale della sezione
        totale_sezione = edited_df["TOTALE"].sum()
        st.markdown(f"Totale sezione {nome_sezione}: `{totale_sezione:,.2f} €`")

    # Aggiorna lo stato
    st.session_state['df_quotazione'] = df_quotazione
