# ── app.py ───────────────────────────────────────────────────────────────
# WSC — Generador de Informes de Rentabilidad
# Streamlit app — deploy en streamlit.io
# ─────────────────────────────────────────────────────────────────────────
import streamlit as st
import json, os
from datetime import date
from extractor import extract_from_pdf, extract_from_excel, merge_extracted_data
from pdf_generator import generate_pdf

st.set_page_config(
    page_title="WSC — Informes de Rentabilidad",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── STYLES ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { background: #1A2744; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stSelectbox label { color: #C8A84B !important; font-weight: 700; }
h1, h2, h3 { color: #1A2744; }
.metric-card { background: #F2F4F8; border-radius: 10px; padding: 16px; border-left: 4px solid #2E5FE8; }
.stButton > button { background: #1A2744; color: white; border-radius: 8px; font-weight: 700; }
.stButton > button:hover { background: #2E5FE8; }
.upload-section { background: #F8F9FC; border-radius: 10px; padding: 20px; border: 2px dashed #D1D5E0; }
.success-box { background: #DCFCE7; border-radius: 8px; padding: 12px; border-left: 4px solid #16A34A; }
.warning-box { background: #FEF3C7; border-radius: 8px; padding: 12px; border-left: 4px solid #C8A84B; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────
if 'clients' not in st.session_state:
    st.session_state.clients = {}       # {name: {history, positions_by_custodian}}
if 'active_client' not in st.session_state:
    st.session_state.active_client = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.environ.get('ANTHROPIC_API_KEY', '')

# ── SIDEBAR ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 WSC")
    st.markdown("**Generador de Informes**")
    st.markdown("---")

    # API Key
    if not st.session_state.api_key:
        st.markdown("### 🔑 API Key")
        api_key_input = st.text_input("Anthropic API Key", type="password",
                                       placeholder="sk-ant-...")
        if st.button("Guardar Key"):
            if api_key_input.startswith('sk-'):
                st.session_state.api_key = api_key_input
                st.success("✓ Key guardada")
            else:
                st.error("Key inválida")
    else:
        st.markdown("### ✓ API Key configurada")
        if st.button("Cambiar Key"):
            st.session_state.api_key = ''
            st.rerun()

    st.markdown("---")
    st.markdown("### 👥 Clientes")

    # New client
    with st.expander("➕ Nuevo cliente"):
        new_name = st.text_input("Nombre")
        new_custodians = st.multiselect("Custodios", ['pershing','ibkr','stonex'],
                                         default=['pershing'])
        if st.button("Crear"):
            if new_name and new_name not in st.session_state.clients:
                st.session_state.clients[new_name] = {
                    'history': {},
                    'positions_by_custodian': {c: [] for c in new_custodians},
                    'custodians': new_custodians,
                    'report_date': date.today().strftime('%d.%m.%Y')
                }
                st.session_state.active_client = new_name
                st.rerun()

    # Client list
    for name in st.session_state.clients:
        c = st.session_state.clients[name]
        has_data = bool(c['history'])
        icon = "✓ " if has_data else "○ "
        if st.button(f"{icon}{name}", key=f"btn_{name}", use_container_width=True):
            st.session_state.active_client = name
            st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────────────
st.title("📊 WSC — Generador de Informes de Rentabilidad")

if not st.session_state.active_client:
    st.info("👈 Creá o seleccioná un cliente en el panel izquierdo para comenzar.")
    st.markdown("""
    ### ¿Cómo funciona?
    1. **Creás el cliente** con su nombre y custodios (Pershing, IBKR, StoneX)
    2. **Subís los archivos** — PDFs de statements históricos + Excel de posiciones
    3. **La IA extrae** los datos automáticamente
    4. **Generás y descargás** el PDF del informe
    """)
    st.stop()

client_name = st.session_state.active_client
client = st.session_state.clients[client_name]

st.markdown(f"## {client_name}")
st.markdown(f"Custodios: **{' + '.join(c.upper() for c in client.get('custodians', ['pershing']))}**")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📂 Cargar Archivos", "👁️ Vista Previa", "📄 Generar PDF"])

# ── TAB 1: UPLOAD ─────────────────────────────────────────────────────────
with tab1:
    if not st.session_state.api_key:
        st.warning("⚠️ Configurá tu API Key de Anthropic en el panel izquierdo primero.")
        st.stop()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📋 Statements de Rentabilidad")
        st.markdown("Subí los PDFs de **Pershing, IBKR o StoneX** — anuales o mensuales.")
        uploaded_pdfs = st.file_uploader(
            "Arrastrá o seleccioná PDFs",
            type=['pdf'],
            accept_multiple_files=True,
            key="pdf_uploader"
        )

        if uploaded_pdfs:
            st.markdown(f"**{len(uploaded_pdfs)} archivo(s) seleccionado(s)**")
            for f in uploaded_pdfs:
                st.markdown(f"- {f.name} ({f.size//1024} KB)")

            if st.button("🤖 Extraer datos con IA", type="primary"):
                progress = st.progress(0)
                status   = st.empty()
                log      = st.container()

                for i, pdf_file in enumerate(uploaded_pdfs):
                    status.markdown(f"**Procesando:** {pdf_file.name}...")
                    try:
                        data = extract_from_pdf(
                            st.session_state.api_key,
                            pdf_file.read(),
                            pdf_file.name
                        )
                        client['history'] = merge_extracted_data(
                            client['history'], data
                        )
                        # Merge positions if present
                        if 'positions' in data and data.get('custodian'):
                            cust = data['custodian']
                            if cust not in client['positions_by_custodian']:
                                client['positions_by_custodian'][cust] = []
                            if data['positions']:
                                client['positions_by_custodian'][cust] = data['positions']
                        log.success(f"✓ {pdf_file.name} — extraído correctamente")
                    except Exception as e:
                        log.error(f"✗ {pdf_file.name} — Error: {str(e)}")

                    progress.progress((i+1) / len(uploaded_pdfs))

                status.markdown("**✅ Procesamiento completado**")
                st.rerun()

    with col2:
        st.markdown("### 📊 Posiciones Actuales (Excel)")
        st.markdown("Subí el Excel de **Unrealized Gain/Loss** de Pershing (y/o posiciones de otros custodios).")
        uploaded_excel = st.file_uploader(
            "Arrastrá o seleccioná el Excel",
            type=['xlsx','xls'],
            accept_multiple_files=False,
            key="excel_uploader"
        )

        if uploaded_excel:
            st.markdown(f"**Archivo:** {uploaded_excel.name}")
            if st.button("📊 Procesar Excel", type="primary"):
                with st.spinner("Procesando posiciones..."):
                    try:
                        positions = extract_from_excel(uploaded_excel.read())
                        client['positions_by_custodian']['pershing'] = [
                            {
                                'symbol':        p['symbol'],
                                'description':   p['description'],
                                'secType':       p['secType'],
                                'assetCategory': p['assetCategory'],
                                'geo':           p['geo'],
                                'sector':        p['sector'],
                                'quantity':      p['quantity'],
                                'price':         p['price'],
                                'marketValue':   p['marketValue'],
                                'costBasis':     p['costBasis'],
                            }
                            for p in positions
                        ]
                        st.success(f"✓ {len(positions)} posiciones extraídas de Pershing")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Status summary
    if client['history']:
        st.markdown("---")
        st.markdown("### ✅ Datos disponibles")
        years_loaded = sorted(client['history'].keys(), key=str)
        st.markdown(f"**Períodos cargados ({len(years_loaded)}):** {', '.join(str(y) for y in years_loaded)}")
        total_pos = sum(len(v) for v in client['positions_by_custodian'].values())
        if total_pos:
            st.markdown(f"**Posiciones:** {total_pos} instrumentos cargados")

# ── TAB 2: PREVIEW ────────────────────────────────────────────────────────
with tab2:
    if not client['history']:
        st.info("Cargá los archivos en la pestaña anterior primero.")
        st.stop()

    import math
    history = client['history']
    all_keys = sorted(history.keys(), key=str)
    display_keys = all_keys[-5:]

    total_dep  = sum(v['dep'] for v in history.values())
    total_ret  = sum(v['ret'] for v in history.values())
    latest_val = history[all_keys[-1]]['vf']
    total_res  = sum(v['res'] for v in history.values())
    chain_keys = [k for k in all_keys if 'YTD' not in str(k)]
    cumul_ret  = math.prod([(1+history[y]['r']) for y in chain_keys]) - 1 if chain_keys else 0

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valor Actual", f"U$S {latest_val:,.0f}")
    with col2:
        st.metric("Retorno Acumulado", f"{cumul_ret*100:+.1f}%")
    with col3:
        st.metric("Resultado Total", f"U$S {total_res:,.0f}")
    with col4:
        last_r = history[all_keys[-1]]['r']
        st.metric(f"Retorno {all_keys[-1]}", f"{last_r*100:+.1f}%")

    st.markdown("---")

    # History table
    st.markdown("### Histórico últimos 5 períodos")
    import pandas as pd
    rows = []
    for y in display_keys:
        h = history[y]
        adj = h['vi'] + h['dep']*0.5 - h['ret']*0.5
        rows.append({
            'Período':     str(y),
            'Val. Inicio': f"U$S {h['vi']:,.0f}",
            'Depósitos':   f"U$S {h['dep']:,.0f}" if h['dep'] else '-',
            'Retiros':     f"U$S {h['ret']:,.0f}" if h['ret'] else '-',
            'Val. Ajust.': f"U$S {adj:,.0f}",
            'Val. Final':  f"U$S {h['vf']:,.0f}",
            'Resultado':   f"U$S {h['res']:,.0f}",
            'Retorno MWR': f"{h['r']*100:+.1f}%",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Positions
    total_pos = sum(len(v) for v in client['positions_by_custodian'].values())
    if total_pos:
        st.markdown("---")
        st.markdown("### Posiciones")
        all_pos = []
        for cust, positions in client['positions_by_custodian'].items():
            for pos in positions:
                all_pos.append({
                    'Símbolo':    pos['symbol'],
                    'Descripción':pos['description'][:30],
                    'Custodio':   cust.upper(),
                    'Cantidad':   pos['quantity'],
                    'Precio':     pos['price'],
                    'Valor Mkt':  f"U$S {pos['marketValue']:,.0f}",
                    'Cost Basis': f"U$S {pos['costBasis']:,.0f}",
                    'G/P':        f"U$S {pos['marketValue']-pos['costBasis']:,.0f}",
                })
        st.dataframe(pd.DataFrame(all_pos), use_container_width=True, hide_index=True)

# ── TAB 3: GENERATE PDF ───────────────────────────────────────────────────
with tab3:
    if not client['history']:
        st.info("Cargá los archivos en la primera pestaña primero.")
        st.stop()

    st.markdown("### Configuración del Informe")
    col1, col2 = st.columns(2)
    with col1:
        report_date = st.text_input("Fecha del informe",
                                     value=date.today().strftime('%d.%m.%Y'))
    with col2:
        st.markdown("**Custodios incluidos:**")
        for c in client.get('custodians', ['pershing']):
            st.markdown(f"- {c.upper()}")

    st.markdown("---")

    if st.button("📄 Generar PDF", type="primary", use_container_width=True):
        with st.spinner("Generando informe PDF..."):
            try:
                pdf_bytes = generate_pdf(
                    client_name=client_name,
                    report_date=report_date,
                    history_all=client['history'],
                    positions_by_custodian=client['positions_by_custodian']
                )
                filename = f"Informe_{client_name.replace(' ','_')}_{report_date.replace('.','')}.pdf"
                st.success("✅ Informe generado correctamente")
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Error generando PDF: {str(e)}")
                st.exception(e)

    st.markdown("---")
    st.markdown("""
    **El PDF incluye:**
    - Retorno acumulado y métricas clave
    - Gráficos: valor de cartera, flujos y rentabilidad anual (últimos 5 períodos)
    - Tabla histórica con MWR por período
    - Posiciones consolidadas con cost basis, precio actual y G/P
    - Análisis por sector, geografía y tipo de activo
    """)
