"""
config.py - Configurações globais do aplicativo de análise de ações B3
"""

# === PARÂMETROS FUNDAMENTALISTAS (Longo Prazo) ===
FUNDAMENTAL_THRESHOLDS = {
    'pl_ideal': 15,
    'pl_alerta': 25,
    'pvp_ideal': 1.5,
    'pvp_alerta': 3.0,
    'roe_minimo': 15,
    'margem_liquida_minima': 5,
    'divida_ebitda_max': 2.5,
    'dividend_yield_minimo': 6,
    'crescimento_receita_minimo': 0
}

# === PARÂMETROS TÉCNICOS (Curto Prazo) ===
TECHNICAL_THRESHOLDS = {
    'rsi_sobrevenda': 30,
    'rsi_sobrecompra': 70,
    'mm_curta': 9,
    'mm_media': 21,
    'mm_longa': 200,
    'bollinger_std': 2,
    'volume_min_increase': 20
}

# === CONFIGURAÇÕES GERAIS ===
APP_CONFIG = {
    'default_tickers': ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'MGLU3.SA'],
    'period': '1y',
    'interval': '1d',
    'timeout_requests': 10,
    'cache_hours': 24
}

# === MENSAGENS LEGAIS ===
DISCLAIMER = """
⚠️ AVISO LEGAL IMPORTANTE ⚠️
Esta ferramenta não constitui recomendação de investimento.
Rentabilidade passada não garante resultados futuros.
Análises são baseadas em dados públicos e podem conter erros.
Consulte sempre um assessor de investimentos credenciado na CVM
antes de tomar decisões financeiras.
"""
