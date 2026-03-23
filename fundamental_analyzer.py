"""
fundamental_analyzer.py - Motor de análise fundamentalista para longo prazo
"""

from typing import Dict
from config import FUNDAMENTAL_THRESHOLDS
import logging

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """Analisa indicadores fundamentalistas e gera score de valor"""
    
    def __init__(self, fundamental_data: Dict):
        self.data = fundamental_data
        self.score = 0
        self.max_score = 7
        self.issues = []
        self.positives = []
    
    def analyze(self) -> Dict:
        """Executa todas as análises fundamentalistas"""
        if not self.data or not self.data.get('current_price'):
            return {
                'score': 0,
                'max_score': self.max_score,
                'classification': 'DADOS_INSUFICIENTES',
                'issues': ['Dados fundamentalistas não disponíveis'],
                'positives': []
            }
        
        self._analyze_pe()
        self._analyze_pvp()
        self._analyze_roe()
        self._analyze_net_margin()
        self._analyze_debt_ebitda()
        self._analyze_dividend_yield()
        self._analyze_revenue_growth()
        
        score_ratio = self.score / self.max_score
        
        if score_ratio >= 0.7:
            classification = 'SUBVALORIZADA'
        elif score_ratio >= 0.4:
            classification = 'JUSTA'
        else:
            classification = 'SUPERVALORIZADA'
        
        return {
            'score': self.score,
            'max_score': self.max_score,
            'score_percent': round(score_ratio * 100),
            'classification': classification,
            'issues': self.issues,
            'positives': self.positives,
            'details': self._generate_details()
        }
    
    def _analyze_pe(self):
        pe = self.data.get('trailing_pe')
        if pe is None:
            self.issues.append('P/L não disponível')
            return
        if pe <= FUNDAMENTAL_THRESHOLDS['pl_ideal']:
            self.score += 1
            self.positives.append(f'P/L atrativo: {pe:.2f}')
        elif pe <= FUNDAMENTAL_THRESHOLDS['pl_alerta']:
            self.positives.append(f'P/L aceitável: {pe:.2f}')
        else:
            self.issues.append(f'P/L elevado: {pe:.2f}')
    
    def _analyze_pvp(self):
        pvp = self.data.get('price_to_book')
        if pvp is None:
            self.issues.append('P/VP não disponível')
            return
        if pvp <= FUNDAMENTAL_THRESHOLDS['pvp_ideal']:
            self.score += 1
            self.positives.append(f'P/VP atrativo: {pvp:.2f}')
        elif pvp <= FUNDAMENTAL_THRESHOLDS['pvp_alerta']:
            self.positives.append(f'P/VP aceitável: {pvp:.2f}')
        else:
            self.issues.append(f'P/VP elevado: {pvp:.2f}')
    
    def _analyze_roe(self):
        roe = self.data.get('roe_percent')
        if roe is None:
            self.issues.append('ROE não disponível')
            return
        if roe >= FUNDAMENTAL_THRESHOLDS['roe_minimo']:
            self.score += 1
            self.positives.append(f'ROE excelente: {roe:.1f}%')
        elif roe >= FUNDAMENTAL_THRESHOLDS['roe_minimo'] * 0.7:
            self.positives.append(f'ROE aceitável: {roe:.1f}%')
        else:
            self.issues.append(f'ROE baixo: {roe:.1f}%')
    
    def _analyze_net_margin(self):
        margin = self.data.get('net_margin_percent')
        if margin is None:
            self.issues.append('Margem líquida não disponível')
            return
        if margin >= FUNDAMENTAL_THRESHOLDS['margem_liquida_minima']:
            self.score += 1
            self.positives.append(f'Margem líquida saudável: {margin:.1f}%')
        else:
            self.issues.append(f'Margem líquida baixa: {margin:.1f}%')
    
    def _analyze_debt_ebitda(self):
        debt_ebitda = self.data.get('debt_to_ebitda')
        if debt_ebitda is None:
            self.issues.append('Dívida/EBITDA não disponível')
            return
        if debt_ebitda <= FUNDAMENTAL_THRESHOLDS['divida_ebitda_max']:
            self.score += 1
            self.positives.append(f'Endividamento controlado: {debt_ebitda:.2f}x')
        else:
            self.issues.append(f'Endividamento elevado: {debt_ebitda:.2f}x')
    
    def _analyze_dividend_yield(self):
        dy = self.data.get('dividend_yield_percent')
        if dy is None:
            return
        if dy >= FUNDAMENTAL_THRESHOLDS['dividend_yield_minimo']:
            self.score += 1
            self.positives.append(f'Dividend Yield atrativo: {dy:.2f}%')
        elif dy > 0:
            self.positives.append(f'Paga dividendos: {dy:.2f}%')
    
    def _analyze_revenue_growth(self):
        growth = self.data.get('revenue_growth_percent')
        if growth is None:
            return
        if growth >= FUNDAMENTAL_THRESHOLDS['crescimento_receita_minimo']:
            self.score += 1
            self.positives.append(f'Crescimento de receita: {growth:.1f}%')
        else:
            self.issues.append(f'Receita em queda: {growth:.1f}%')
    
    def _generate_details(self) -> Dict:
        return {
            'preco_atual': self.data.get('current_price'),
            'pl': self.data.get('trailing_pe'),
            'pvp': self.data.get('price_to_book'),
            'roe': self.data.get('roe_percent'),
            'margem_liquida': self.data.get('net_margin_percent'),
            'divida_ebitda': self.data.get('debt_to_ebitda'),
            'dividend_yield': self.data.get('dividend_yield_percent'),
            'crescimento_receita': self.data.get('revenue_growth_percent')
        }
