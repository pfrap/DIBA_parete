import streamlit as st
import pandas as pd
import io
from datetime import datetime

def show():
    st.title("Offerta commerciale")

    # 📥 Importazione di un'offerta salvata
    st.subheader("📥 Importa offerta esistente")
    offerte_disponibili = list(st.session_state.get("offerte_salvate", {}).keys())
    with st.expander("🔽 Seleziona offerta salvata da importare"):
        if offerte_disponibili:
            offerta_scelta = st.selectbox("Offerte salvate disponibili", offerte_disponibili)
            if st.button("📤 Importa offerta selezionata"):
                st.session_state["df_quotazione"] = st.session_state["offerte_salvate"][offerta_scelta].copy()
                st.success(f"✅ Offerta '{offerta_scelta}' importata con successo.")
        else:
            st.info("🔒 Nessuna offerta salvata trovata.")

    # 🚫 Nessuna offerta ancora creata
    if 'df_quotazione' not in st.session_state or not st.session_state['df_quotazione']:
        st.warning("⚠️ Nessuna offerta disponibile. Aggiungi articoli dal listino.")
        return

    # 💼 Visualizza e modifica le sessioni dell’offerta
    for nome_sessione, df_sessione in st.session_state['df_quotazione'].items():
        st.markdown(f"## 🗂 {nome_sessione}")

        with st.expander("📋 Articoli in offerta", expanded=False):
            st.dataframe(df_sessione, use_container_width=True)

        col1, col2 = st.columns([2, 2])
        with col1:
            sconto_perc = st.number_input(
                f"Sconto su {nome_sessione} (%)", min_value=0, max_value=100, value=0, step=1, key=f"sconto_{nome_sessione}"
            )
        with col2:
            if st.button(f"💸 Applica sconto a {nome_sessione}", key=f"sconto_btn_{nome_sessione}"):
                if "LISTINO" in df_sessione.columns:
                    df_mod = df_sessione.copy()
                    df_mod["PREZZO_SCONTATO"] = df_mod["LISTINO"] * (1 - sconto_perc / 100)
                    st.session_state["df_quotazione"][nome_sessione] = df_mod
                    st.success(f"Sconto del {sconto_perc}% applicato.")
                else:
                    st.error("❌ Colonna 'LISTINO' non presente.")

        # Rimuovi articoli
        with st.expander("🗑 Rimuovi articoli"):
            df_mod = df_sessione.copy()
            df_mod["RIMUOVI"] = False
            df_editor = st.data_editor(
                df_mod,
                key=f"rimuovi_editor_{nome_sessione}",
                use_container_width=True,
                disabled=df_mod.columns.difference(["RIMUOVI"]).tolist()
            )
            if st.button(f"✂️ Conferma rimozione da {nome_sessione}", key=f"rimuovi_btn_{nome_sessione}"):
                df_filtrato = df_editor[df_editor["RIMUOVI"] == False].drop(columns=["RIMUOVI"])
                st.session_state["df_quotazione"][nome_sessione] = df_filtrato
                st.success("✅ Articoli rimossi.")

    st.divider()

    # ➕ Aggiungi articolo custom
    st.subheader("➕ Aggiungi articolo custom")
    with st.form("aggiungi_custom"):
        col1, col2 = st.columns(2)
        with col1:
            codice = st.text_input("Codice", value="CUSTOM001")
            c1 = st.text_input("Categoria 1", value="Custom")
            c2 = st.text_input("Categoria 2", value="Manuale")
        with col2:
            descrizione = st.text_input("Descrizione", value="Articolo custom")
            prezzo = st.number_input("Prezzo (€)", min_value=0.0, value=100.0, step=1.0)

        sessioni_possibili = list(st.session_state['df_quotazione'].keys())
        sessione_target = st.selectbox("Sessione di destinazione", sessioni_possibili)

        if st.form_submit_button("➕ Aggiungi articolo"):
            nuovo_articolo = pd.DataFrame([{
                "CONCAT_3": codice,
                "C1": c1,
                "C2": c2,
                "DESCRIZIONE": descrizione,
                "LISTINO": prezzo
            }])
            st.session_state['df_quotazione'][sessione_target] = pd.concat(
                [st.session_state['df_quotazione'][sessione_target], nuovo_articolo],
                ignore_index=True
            )
            st.success(f"✅ Articolo custom aggiunto a {sessione_target}")

    st.divider()

    # 💾 Salva - Duplica - Esporta
    st.subheader("📦 Gestione offerta")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Salva offerta"):
            if "offerte_salvate" not in st.session_state:
                st.session_state["offerte_salvate"] = {}
            nome_offerta = f"Offerta_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.session_state["offerte_salvate"][nome_offerta] = st.session_state["df_quotazione"].copy()
            st.success(f"✅ Offerta salvata come: {nome_offerta}")

    with col2:
        if offerte_disponibili:
            dup_scelta = st.selectbox("🗂 Duplica offerta", offerte_disponibili, key="dup_select")
            if st.button("📑 Duplica selezionata"):
                nuova_offerta = {
                    k + "_copy": v.copy() for k, v in st.session_state["offerte_salvate"][dup_scelta].items()
                }
                st.session_state["df_quotazione"].update(nuova_offerta)
                st.success(f"📄 Offerta '{dup_scelta}' duplicata.")

    with col3:
        if st.button("📤 Esporta in Excel"):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                for nome, df in st.session_state["df_quotazione"].items():
                    df.to_excel(writer, sheet_name=nome[:31], index=False)
                writer.close()
            buffer.seek(0)
            st.download_button(
                "⬇️ Scarica Excel",
                data=buffer,
                file_name=f"offerta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
