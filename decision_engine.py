"""
decision_engine.py - Motor de decisão que integra análises e gera recomendações
"""

from typing import Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Integra análises fundamentalista e técnica para gerar veredito final"""
    
    def __init__(self, ticker: str, company_info: Dict):
        self.ticker = ticker
        self.company_info = company_info
        self.fundamental_result = None
        self.technical_result = None
    
    def set_fundamental_analysis(self, result: Dict):
        self.fundamental_result = result
    
    def set_technical_analysis(self, result: Dict):
        self.technical_result = result
    
    def generate_verdict(self) -> Dict:
        """Gera o veredito final combinando ambas as análises"""
        verdict = {
            'ticker': self.ticker,
            'company': self.company_info.get('name', self.ticker),
            'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'disclaimer': 'Esta ferramenta não constitui recomendação de investimento.'
        }
        
        if not self.fundamental_result or not self.technical_result:
            verdict['status'] = 'ANALISE_INCOMPLETA'
            verdict['recommendation'] = 'AGUARDAR_DADOS'
            verdict['confidence'] = 0
            return verdict
        
        fund_score = self.fundamental_result.get('score_percent', 0)
        tech_score = self.technical_result.get('score_percent', 0)
        
        combined_score = (fund_score * 0.6) + (tech_score * 0.4)
        verdict['combined_score'] = round(combined_score)
        
        profile = self._determine_profile(fund_score, tech_score)
        verdict['profile'] = profile
        
        recommendation, confidence = self._generate_recommendation(fund_score, tech_score, profile)
        verdict['recommendation'] = recommendation
        verdict['confidence'] = confidence
        
        current_price = self.technical_result.get('current_price')
        if current_price:
            verdict['current_price'] = current_price
            verdict['target_price'], verdict['stop_loss'] = self._calculate_targets(current_price, recommendation)
        
        verdict['summary'] = self._generate_summary()
        
        return verdict
    
    def _determine_profile(self, fund_score: int, tech_score: int) -> str:
        if fund_score >= 70 and tech_score >= 70:
            return 'AMBOS (Curto + Longo Prazo)'
        elif fund_score >= 60:
            return 'LONGO PRAZO (Buy & Hold)'
        elif tech_score >= 60:
            return 'CURTO PRAZO (Swing Trade)'
        else:
            return 'AGUARDAR MELHOR OPORTUNIDADE'
    
    def _generate_recommendation(self, fund_score: int, tech_score: int, profile: str) -> tuple:
        if fund_score >= 70 and tech_score >= 70:
            return '🟢 COMPRA FORTE', 90
        elif fund_score >= 70 and tech_score >= 40:
            return '🟢 COMPRA (Longo Prazo)', 75
        elif fund_score >= 40 and tech_score >= 70:
            return '🟡 COMPRA (Curto Prazo)', 65
        elif fund_score >= 40 and tech_score >= 40:
            return '⚪ NEUTRO - Aguardar', 50
        elif fund_score < 30 and tech_score < 30:
            return '🔴 VENDA / EVITAR', 80
        elif tech_score >= 70:
            return '🟡 COMPRA ESPECULATIVA (Alto Risco)', 40
        else:
            return '⚪ AGUARDAR - Sem sinal claro', 30
    
    def _calculate_targets(self, current_price: float, recommendation: str) -> tuple:
        if 'COMPRA' in recommendation:
            target = current_price * 1.20
            stop = current_price * 0.90
            return round(target, 2), round(stop, 2)
        elif 'VENDA' in recommendation:
            target = current_price * 0.95
            stop = current_price * 1.05
            return round(target, 2), round(stop, 2)
        else:
            return round(current_price * 1.10, 2), round(current_price * 0.92, 2)
    
    def _generate_summary(self) -> Dict:
        summary = {}
        if self.fundamental_result.get('positives'):
            summary['fundamental_positives'] = self.fundamental_result['positives'][:3]
        if self.fundamental_result.get('issues'):
            summary['fundamental_alerts'] = self.fundamental_result['issues'][:3]
        if self.technical_result.get('signals'):
            technical_highlights = [s for s in self.technical_result['signals'] if any(emoji in s for emoji in ['✅', '⚠️'])]
            summary['technical_signals'] = technical_highlights[:3]
        return summary
