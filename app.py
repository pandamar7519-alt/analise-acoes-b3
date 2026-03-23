"""
app.py - Interface Web para Analisador de Ações B3 (Streamlit)
Deploy: GitHub + Render.com
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from config import APP_CONFIG, DISCLAIMER, FUNDAMENTAL_THRESHOLDS
from data_fetcher import DataFetcher
from fundamental_analyzer import FundamentalAnalyzer
from technical_analyzer import TechnicalAnalyzer
from decision_engine import DecisionEngine

# Configuração da página
st.set_page_config(
    page_title="📊 Analisador de Ações B3",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cache para dados
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker: str, period: str, interval: str):
    fetcher = DataFetcher(ticker)
    return fetcher.get_historical_data(period, interval)

@st.cache_data(ttl=7200)
def fetch_fundamental_data(ticker: str):
    fetcher = DataFetcher(ticker)
    return fetcher.get_fundamental_data(), fetcher.get_quick_info()

# Sidebar
with st.sidebar:
    st.title("⚙️ Configurações")
    
    st.subheader("📋 Ações para Analisar")
    default_tickers = ", ".join([t.replace('.SA','') for t in APP_CONFIG['default_tickers']])
    tickers_input = st.text_input("Tickers (separados por vírgula)", value=default_tickers)
    
    period = st.selectbox("Período dos Dados", options=['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
    
    analyze_btn = st.button("🔍 Analisar Ações", type="primary", use_container_width=True)
    
    st.divider()
    st.info("💡 Dica: Use tickers no formato B3 (ex: PETR4)")

# Cabeçalho Principal
st.title("📊 Analisador de Ações B3")
st.markdown("*Identifique oportunidades de lucro com análise integrada*")
st.warning(DISCLAIMER)

# Área de resultados
if analyze_btn:
    tickers_list = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    tickers_list = [t if '.SA' in t else f"{t}.SA" for t in tickers_list]
    
    if not tickers_list:
        st.error("⚠️ Por favor, insira pelo menos um ticker.")
        st.stop()
    
    st.markdown(f"### 🔄 Analisando {len(tickers_list)} ativo(s)")
    
    for ticker in tickers_list:
        with st.expander(f"📈 {ticker.replace('.SA', '')}", expanded=True):
            with st.spinner(f"Buscando dados para {ticker.replace('.SA', '')}..."):
                try:
                    # Coleta de dados
                    historical_data = fetch_stock_data(ticker, period, '1d')
                    fundamental_data, company_info = fetch_fundamental_data(ticker)
                    
                    if historical_data is None or len(historical_data) < 200:
                        st.error(f"❌ Dados insuficientes para {ticker.replace('.SA', '')}")
                        continue
                    
                    # Análises
                    fund_analyzer = FundamentalAnalyzer(fundamental_data or {})
                    fund_result = fund_analyzer.analyze()
                    
                    tech_analyzer = TechnicalAnalyzer(historical_data)
                    tech_result = tech_analyzer.analyze()
                    support_resistance = tech_analyzer.calculate_support_resistance()
                    
                    engine = DecisionEngine(ticker, company_info)
                    engine.set_fundamental_analysis(fund_result)
                    engine.set_technical_analysis(tech_result)
                    verdict = engine.generate_verdict()
                    
                    # Métricas principais
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💰 Preço", f"R$ {verdict.get('current_price', 'N/A'):.2f}" if verdict.get('current_price') else "N/A")
                    with col2:
                        st.metric("🎯 Score", f"{verdict.get('combined_score', 0)}/100")
                    with col3:
                        st.metric("📊 Confiança", f"{verdict.get('confidence', 0)}%")
                    with col4:
                        st.metric("📅 Perfil", verdict.get('profile', 'N/A').split()[0])
                    
                    # Veredito
                    recommendation = verdict.get('recommendation', 'N/A')
                    if 'COMPRA FORTE' in recommendation:
                        st.success(f"### 🟢 {recommendation}")
                    elif 'COMPRA' in recommendation:
                        st.warning(f"### 🟡 {recommendation}")
                    elif 'VENDA' in recommendation:
                        st.error(f"### 🔴 {recommendation}")
                    else:
                        st.info(f"### ⚪ {recommendation}")
                    
                    # Preço-alvo e Stop
                    col_t1, col_t2 = st.columns(2)
                    with col_t1:
                        if verdict.get('target_price'):
                            target = verdict['target_price']
                            current = verdict.get('current_price', target)
                            upside = ((target - current) / current) * 100 if current else 0
                            st.metric("🎯 Preço-Alvo", f"R$ {target:.2f}", f"{upside:+.1f}%")
                    with col_t2:
                        if verdict.get('stop_loss'):
                            stop = verdict['stop_loss']
                            current = verdict.get('current_price', stop)
                            downside = ((stop - current) / current) * 100 if current else 0
                            st.metric("🛑 Stop Loss", f"R$ {stop:.2f}", f"{downside:+.1f}%", delta_color="inverse")
                    
                    # Tabs
                    tab1, tab2, tab3 = st.tabs(["📈 Fundamentalista", "📉 Técnico", "📋 Resumo"])
                    
                    with tab1:
                        st.subheader("Análise Fundamentalista")
                        col_f1, col_f2 = st.columns(2)
                        with col_f1:
                            st.progress(fund_result.get('score_percent', 0) / 100)
                            st.caption(f"Score: {fund_result.get('score', 0)}/{fund_result.get('max_score', 0)}")
                        with col_f2:
                            classification = fund_result.get('classification', 'N/A')
                            if classification == 'SUBVALORIZADA':
                                st.success(f"**{classification}**")
                            elif classification == 'JUSTA':
                                st.warning(f"**{classification}**")
                            else:
                                st.error(f"**{classification}**")
                        
                        details = fund_result.get('details', {})
                        if details:
                            df_fund = pd.DataFrame([
                                {"Indicador": "P/L", "Valor": f"{details.get('pl', 'N/A'):.2f}" if isinstance(details.get('pl'), (int, float)) else "N/A"},
                                {"Indicador": "P/VP", "Valor": f"{details.get('pvp', 'N/A'):.2f}" if isinstance(details.get('pvp'), (int, float)) else "N/A"},
                                {"Indicador": "ROE", "Valor": f"{details.get('roe', 'N/A'):.1f}%" if isinstance(details.get('roe'), (int, float)) else "N/A"},
                                {"Indicador": "Margem Líquida", "Valor": f"{details.get('margem_liquida', 'N/A'):.1f}%" if isinstance(details.get('margem_liquida'), (int, float)) else "N/A"},
                                {"Indicador": "Dívida/EBITDA", "Valor": f"{details.get('divida_ebitda', 'N/A'):.2f}x" if isinstance(details.get('divida_ebitda'), (int, float)) else "N/A"},
                            ])
                            st.dataframe(df_fund, use_container_width=True, hide_index=True)
                        
                        if fund_result.get('positives'):
                            st.markdown("##### ✅ Pontos Fortes")
                            for item in fund_result['positives'][:4]:
                                st.success(f"• {item}")
                        if fund_result.get('issues'):
                            st.markdown("##### ⚠️ Alertas")
                            for item in fund_result['issues'][:4]:
                                st.error(f"• {item}")
                    
                    with tab2:
                        st.subheader("Análise Técnica")
                        col_t1, col_t2 = st.columns(2)
                        with col_t1:
                            st.progress(tech_result.get('score_percent', 0) / 100)
                            st.caption(f"Score: {tech_result.get('score', 0)}/{tech_result.get('max_score', 0)}")
                        with col_t2:
                            signal = tech_result.get('signal', 'N/A')
                            if 'COMPRA' in signal:
                                st.success(f"**{signal}**")
                            elif 'VENDA' in signal:
                                st.error(f"**{signal}**")
                            else:
                                st.warning(f"**{signal}**")
                        
                        indicators = tech_result.get('indicators', {})
                        if indicators:
                            df_tech = pd.DataFrame([
                                {"Indicador": "RSI", "Valor": f"{indicators.get('rsi', 'N/A'):.1f}" if isinstance(indicators.get('rsi'), (int, float)) else "N/A"},
                                {"Indicador": "MM9", "Valor": f"R$ {indicators.get('mm9', 'N/A'):.2f}" if isinstance(indicators.get('mm9'), (int, float)) else "N/A"},
                                {"Indicador": "MM21", "Valor": f"R$ {indicators.get('mm21', 'N/A'):.2f}" if isinstance(indicators.get('mm21'), (int, float)) else "N/A"},
                                {"Indicador": "MM200", "Valor": f"R$ {indicators.get('mm200', 'N/A'):.2f}" if isinstance(indicators.get('mm200'), (int, float)) else "N/A"},
                            ])
                            st.dataframe(df_tech, use_container_width=True, hide_index=True)
                        
                        if support_resistance:
                            col_s1, col_s2, col_s3 = st.columns(3)
                            with col_s1:
                                st.metric("🔺 Resistência", f"R$ {support_resistance.get('resistencia', 'N/A'):.2f}")
                            with col_s2:
                                st.metric("📍 Médio", f"R$ {support_resistance.get('preco_medio', 'N/A'):.2f}")
                            with col_s3:
                                st.metric("🔻 Suporte", f"R$ {support_resistance.get('suporte', 'N/A'):.2f}")
                        
                        if tech_result.get('signals'):
                            st.markdown("##### 🔔 Sinais")
                            for signal in tech_result['signals'][:5]:
                                if '✅' in signal:
                                    st.success(signal)
                                elif '⚠️' in signal:
                                    st.warning(signal)
                                else:
                                    st.info(signal)
                    
                    with tab3:
                        st.subheader("📋 Resumo Executivo")
                        summary = verdict.get('summary', {})
                        if summary.get('fundamental_positives'):
                            with st.expander("✅ Pontos Fortes", expanded=True):
                                for item in summary['fundamental_positives']:
                                    st.write(f"• {item}")
                        if summary.get('fundamental_alerts'):
                            with st.expander("⚠️ Alertas", expanded=False):
                                for item in summary['fundamental_alerts']:
                                    st.write(f"• {item}")
                        if summary.get('technical_signals'):
                            with st.expander("🔔 Sinais Técnicos", expanded=True):
                                for item in summary['technical_signals']:
                                    st.write(item)
                        
                        st.markdown("##### 🏢 Empresa")
                        st.json({
                            "Ticker": ticker.replace('.SA', ''),
                            "Nome": company_info.get('name', 'N/A'),
                            "Setor": company_info.get('sector', 'N/A'),
                        }, expanded=False)
                    
                    st.caption(f"🕐 Atualizado: {verdict.get('timestamp', 'N/A')}")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao analisar {ticker.replace('.SA', '')}: {str(e)}")
        
        st.divider()
    
    st.markdown("---")
    st.caption("📊 Analisador de Ações B3 v1.0 | Dados via Yahoo Finance")

else:
    st.info("👈 Use a barra lateral para selecionar ações e clicar em **Analisar Ações**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📈 Fundamentalista")
        st.markdown("P/L, P/VP, ROE, margens e endividamento para identificar valor.")
    with col2:
        st.markdown("### 📉 Técnica")
        st.markdown("RSI, médias móveis e Bollinger para timing de entrada.")
    with col3:
        st.markdown("### 🎯 Decisão")
        st.markdown("Veredito integrado com preço-alvo e stop loss sugeridos.")
