"""
technical_analyzer.py - Motor de análise técnica para curto prazo
"""

import pandas as pd
import numpy as np
from ta.trend import SMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
from typing import Dict
from config import TECHNICAL_THRESHOLDS
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Analisa indicadores técnicos e gera sinais de timing"""
    
    def __init__(self, historical_data: pd.DataFrame):
        self.df = historical_data.copy()
        self.signals = []
        self.score = 0
        self.max_score = 4
    
    def analyze(self) -> Dict:
        """Executa todas as análises técnicas"""
        if self.df is None or len(self.df) < TECHNICAL_THRESHOLDS['mm_longa']:
            return {
                'score': 0,
                'max_score': self.max_score,
                'classification': 'DADOS_INSUFICIENTES',
                'signals': ['Dados históricos insuficientes'],
                'current_price': None
            }
        
        current_price = self.df['Close'].iloc[-1]
        self._calculate_indicators()
        self._analyze_rsi()
        self._analyze_moving_averages()
        self._analyze_bollinger()
        self._analyze_volume()
        
        if self.score >= self.max_score * 0.7:
            signal = 'COMPRA_TECNICA'
        elif self.score <= self.max_score * 0.3:
            signal = 'VENDA_TECNICA'
        else:
            signal = 'NEUTRO_TECNICO'
        
        return {
            'score': self.score,
            'max_score': self.max_score,
            'score_percent': round(self.score / self.max_score * 100),
            'signal': signal,
            'current_price': round(current_price, 2),
            'indicators': self._get_indicator_values(),
            'signals': self.signals
        }
    
    def _calculate_indicators(self):
        rsi = RSIIndicator(close=self.df['Close'], window=14)
        self.df['RSI'] = rsi.rsi()
        
        self.df['MM9'] = SMAIndicator(close=self.df['Close'], window=TECHNICAL_THRESHOLDS['mm_curta']).sma_indicator()
        self.df['MM21'] = SMAIndicator(close=self.df['Close'], window=TECHNICAL_THRESHOLDS['mm_media']).sma_indicator()
        self.df['MM200'] = SMAIndicator(close=self.df['Close'], window=TECHNICAL_THRESHOLDS['mm_longa']).sma_indicator()
        
        bollinger = BollingerBands(close=self.df['Close'], window=20, window_dev=2)
        self.df['BB_upper'] = bollinger.bollinger_hband()
        self.df['BB_lower'] = bollinger.bollinger_lband()
        self.df['BB_middle'] = bollinger.bollinger_mavg()
        
        self.df['volume_ma20'] = self.df['Volume'].rolling(window=20).mean()
    
    def _analyze_rsi(self):
        current_rsi = self.df['RSI'].iloc[-1]
        if current_rsi < TECHNICAL_THRESHOLDS['rsi_sobrevenda']:
            self.score += 1
            self.signals.append(f'✅ RSI em sobrevenda: {current_rsi:.1f} (compra)')
        elif current_rsi > TECHNICAL_THRESHOLDS['rsi_sobrecompra']:
            self.signals.append(f'⚠️ RSI em sobrecompra: {current_rsi:.1f} (venda)')
        else:
            self.signals.append(f'➡️ RSI neutro: {current_rsi:.1f}')
    
    def _analyze_moving_averages(self):
        current = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        if current['Close'] > current['MM200']:
            self.score += 0.5
            self.signals.append('✅ Preço acima da MM200 (tendência de alta)')
        else:
            self.signals.append('⚠️ Preço abaixo da MM200 (tendência de baixa)')
        
        if prev['MM9'] <= prev['MM21'] and current['MM9'] > current['MM21']:
            self.score += 1
            self.signals.append('✅ Cruzamento de alta MM9 > MM21')
        elif prev['MM9'] >= prev['MM21'] and current['MM9'] < current['MM21']:
            self.signals.append('⚠️ Cruzamento de baixa MM9 < MM21')
        elif current['MM9'] > current['MM21']:
            self.score += 0.5
            self.signals.append('➡️ MM9 acima da MM21 (viés de alta)')
    
    def _analyze_bollinger(self):
        current = self.df.iloc[-1]
        price = current['Close']
        upper = current['BB_upper']
        lower = current['BB_lower']
        
        if price <= lower * 1.01:
            self.score += 1
            self.signals.append('✅ Preço na banda inferior de Bollinger')
        elif price >= upper * 0.99:
            self.signals.append('⚠️ Preço na banda superior de Bollinger')
        else:
            position = (price - lower) / (upper - lower) * 100 if (upper - lower) > 0 else 50
            self.signals.append(f'➡️ Preço no meio das bandas ({position:.1f}%)')
    
    def _analyze_volume(self):
        current_volume = self.df['Volume'].iloc[-1]
        avg_volume = self.df['volume_ma20'].iloc[-1]
        
        if pd.isna(avg_volume) or avg_volume == 0:
            self.signals.append('⚪ Volume: dados insuficientes')
            return
            
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        
        if volume_change >= TECHNICAL_THRESHOLDS['volume_min_increase']:
            self.signals.append(f'✅ Volume {volume_change:.1f}% acima da média')
            if self.df['Close'].iloc[-1] > self.df['Close'].iloc[-2]:
                self.score += 0.5
        elif volume_change <= -TECHNICAL_THRESHOLDS['volume_min_increase']:
            self.signals.append(f'⚠️ Volume {abs(volume_change):.1f}% abaixo da média')
        else:
            self.signals.append(f'➡️ Volume dentro da média ({volume_change:+.1f}%)')
    
    def _get_indicator_values(self) -> Dict:
        current = self.df.iloc[-1]
        return {
            'rsi': round(current['RSI'], 2) if not pd.isna(current['RSI']) else None,
            'mm9': round(current['MM9'], 2) if not pd.isna(current['MM9']) else None,
            'mm21': round(current['MM21'], 2) if not pd.isna(current['MM21']) else None,
            'mm200': round(current['MM200'], 2) if not pd.isna(current['MM200']) else None,
            'bb_upper': round(current['BB_upper'], 2) if not pd.isna(current['BB_upper']) else None,
            'bb_lower': round(current['BB_lower'], 2) if not pd.isna(current['BB_lower']) else None,
            'volume_atual': int(current['Volume']),
            'volume_media20': int(current['volume_ma20']) if not pd.isna(current['volume_ma20']) else None
        }
    
    def calculate_support_resistance(self) -> Dict:
        if len(self.df) < 20:
            return {}
        recent = self.df.tail(20)
        return {
            'resistencia': round(recent['High'].max(), 2),
            'suporte': round(recent['Low'].min(), 2),
            'preco_medio': round(recent['Close'].mean(), 2)
        }
