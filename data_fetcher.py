"""
data_fetcher.py - Módulo para coleta de dados de ações da B3
"""

import yfinance as yf
import pandas as pd
import requests
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Classe responsável por buscar dados de ações de múltiplas fontes"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.yahoo_ticker = ticker if '.SA' in ticker else f"{ticker}.SA"
        self.brapi_ticker = ticker.replace('.SA', '')
        
    def get_historical_data(self, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
        """Busca dados históricos de preço via Yahoo Finance"""
        try:
            stock = yf.Ticker(self.yahoo_ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"Nenhum dado histórico encontrado para {self.ticker}")
                return None
                
            logger.info(f"Dados históricos obtidos: {len(df)} registros para {self.ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos para {self.ticker}: {str(e)}")
            return None
    
    def get_fundamental_data(self) -> Optional[Dict]:
        """Busca dados fundamentalistas via Yahoo Finance"""
        try:
            stock = yf.Ticker(self.yahoo_ticker)
            info = stock.info
            
            fundamental_data = {
                'current_price': info.get('currentPrice'),
                'market_cap': info.get('marketCap'),
                'trailing_pe': info.get('trailingPE'),
                'price_to_book': info.get('priceToBook'),
                'return_on_equity': info.get('returnOnEquity'),
                'profit_margins': info.get('profitMargins'),
                'total_debt': info.get('totalDebt'),
                'ebitda': info.get('ebitda'),
                'dividend_yield': info.get('dividendYield'),
                'revenue_growth': info.get('revenueGrowth'),
                'currency': info.get('currency', 'BRL')
            }
            
            # Converter decimals para porcentagem
            if fundamental_data.get('return_on_equity'):
                fundamental_data['roe_percent'] = fundamental_data['return_on_equity'] * 100
            if fundamental_data.get('profit_margins'):
                fundamental_data['net_margin_percent'] = fundamental_data['profit_margins'] * 100
            if fundamental_data.get('dividend_yield'):
                fundamental_data['dividend_yield_percent'] = fundamental_data['dividend_yield'] * 100
            if fundamental_data.get('revenue_growth'):
                fundamental_data['revenue_growth_percent'] = fundamental_data['revenue_growth'] * 100
                
            # Calcular Dívida/EBITDA
            if fundamental_data.get('total_debt') and fundamental_data.get('ebitda'):
                if fundamental_data['ebitda'] > 0:
                    fundamental_data['debt_to_ebitda'] = fundamental_data['total_debt'] / fundamental_data['ebitda']
                else:
                    fundamental_data['debt_to_ebitda'] = None
                    
            return fundamental_data
            
        except Exception as e:
            logger.warning(f"Yahoo Finance falhou para {self.ticker}: {str(e)}")
            return None
    
    def get_quick_info(self) -> Dict:
        """Obtém informações básicas da ação"""
        try:
            stock = yf.Ticker(self.yahoo_ticker)
            info = stock.info
            return {
                'name': info.get('longName', self.ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'exchange': info.get('exchange', 'B3')
            }
        except:
            return {'name': self.ticker, 'sector': 'N/A', 'industry': 'N/A', 'exchange': 'B3'}
