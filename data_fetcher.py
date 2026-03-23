"""
data_fetcher.py - Módulo para coleta de dados de ações da B3
Fonte principal: Brapi.dev (melhor cobertura para Brasil)
Fallback: Yahoo Finance
"""

import yfinance as yf
import pandas as pd
import requests
import os
from typing import Optional, Dict
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """Classe responsável por buscar dados de ações de múltiplas fontes"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.yahoo_ticker = ticker if '.SA' in ticker else f"{ticker}.SA"
        self.brapi_ticker = ticker.replace('.SA', '')
        # Pega token do ambiente (Render Secrets) ou usa demo
        self.brapi_token = os.environ.get('BRAPI_TOKEN', 'demo')
        
    def get_historical_data(self, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
        """Busca dados históricos de preço via Yahoo Finance"""
        try:
            stock = yf.Ticker(self.yahoo_ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"Nenhum dado histórico encontrado para {self.ticker}")
                return None
            
            # Resetar índice para ter 'Date' como coluna
            df = df.reset_index()
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'Datetime'})
            if 'Datetime' in df.columns:
                df = df.set_index('Datetime')
                
            logger.info(f"Dados históricos obtidos: {len(df)} registros para {self.ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados históricos para {self.ticker}: {str(e)}")
            return None
    
    def get_fundamental_data(self) -> Optional[Dict]:
        """
        Busca dados fundamentalistas - PRIORIDADE: Brapi.dev para B3
        """
        fundamental_data = {}
        
        # === TENTATIVA 1: Brapi.dev (Melhor para B3) ===
        try:
            url = f"https://brapi.dev/api/quote/{self.brapi_ticker}?token={self.brapi_token}&fundamental=true"
            logger.info(f"Buscando dados fundamentalistas na Brapi.dev: {self.brapi_ticker}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar se há resultados
                if data.get('results') and len(data['results']) > 0:
                    stock_data = data['results'][0]
                    
                    # Mapear campos da Brapi.dev
                    fundamental_data = {
                        'current_price': stock_data.get('regularMarketPrice'),
                        'market_cap': stock_data.get('marketCap'),
                        'trailing_pe': stock_data.get('priceEarnings'),  # P/L
                        'price_to_book': stock_data.get('priceBook'),  # P/VP
                        'roe_percent': stock_data.get('ROE'),  # Já em %
                        'net_margin_percent': stock_data.get('netMargin'),  # Já em %
                        'debt_to_ebitda': stock_data.get('debtToEbitda'),
                        'dividend_yield_percent': stock_data.get('dividendYield'),  # Já em %
                        'revenue_growth_percent': stock_data.get('revenueGrowth'),  # Já em %
                        'currency': 'BRL',
                        'source': 'Brapi.dev'
                    }
                    
                    # Log de sucesso
                    logger.info(f"✅ Dados fundamentalistas obtidos via Brapi.dev para {self.ticker}")
                    logger.info(f"   P/L: {fundamental_data.get('trailing_pe')}, P/VP: {fundamental_data.get('price_to_book')}, ROE: {fundamental_data.get('roe_percent')}")
                    
                    # Verificar se temos dados mínimos
                    if fundamental_data.get('current_price'):
                        return fundamental_data
                    
        except Exception as e:
            logger.warning(f"Brapi.dev falhou para {self.ticker}: {str(e)}")
        
        # === TENTATIVA 2: Yahoo Finance (Fallback) ===
        try:
            logger.info(f"Tentando Yahoo Finance como fallback para {self.ticker}")
            stock = yf.Ticker(self.yahoo_ticker)
            info = stock.info
            
            if not info or not info.get('currentPrice'):
                logger.warning(f"Yahoo Finance retornou dados vazios para {self.ticker}")
                return None
            
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
                'currency': info.get('currency', 'BRL'),
                'source': 'Yahoo Finance'
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
            
            logger.info(f"✅ Dados fundamentalistas obtidos via Yahoo Finance para {self.ticker}")
            return fundamental_data
            
        except Exception as e:
            logger.error(f"Yahoo Finance falhou para {self.ticker}: {str(e)}")
        
        logger.error(f"❌ Todas as fontes falharam para dados fundamentalistas de {self.ticker}")
        return None
    
    def get_quick_info(self) -> Dict:
        """Obtém informações básicas da ação"""
        try:
            # Tentar Brapi primeiro
            url = f"https://brapi.dev/api/quote/{self.brapi_ticker}?token={self.brapi_token}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200 and response.json().get('results'):
                data = response.json()['results'][0]
                return {
                    'name': data.get('longName', data.get('shortName', self.ticker)),
                    'sector': data.get('sector', 'N/A'),
                    'industry': data.get('industry', 'N/A'),
                    'exchange': 'B3'
                }
        except:
            pass
        
        # Fallback Yahoo Finance
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
