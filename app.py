name=app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
import io
import traceback
from typing import Tuple, Dict, Optional, List

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION STREAMLIT
# ============================================================================
st.set_page_config(
    page_title="Alpha Terminal Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS PERSONNALISÉ - THÈME SOMBRE PROFESSIONNEL
# ============================================================================
DARK_CSS = """
<style>
    :root {
        --primary-bg: #0e1117;
        --secondary-bg: #161b22;
        --tertiary-bg: #21262d;
        --border-color: #30363d;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --accent-green: #238636;
        --accent-red: #da3633;
        --accent-blue: #58a6ff;
        --accent-yellow: #d29922;
    }
    
    body {
        background-color: var(--primary-bg);
        color: var(--text-primary);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .metric-card {
        background: linear-gradient(135deg, var(--secondary-bg) 0%, var(--tertiary-bg) 100%);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.2);
    }
    
    .metric-label {
        font-size: 12px;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    .metric-value.positive {
        color: var(--accent-green);
    }
    
    .metric-value.negative {
        color: var(--accent-red);
    }
    
    .metric-value.neutral {
        color: var(--accent-blue);
    }
    
    .section-header {
        border-bottom: 2px solid var(--accent-blue);
        padding-bottom: 12px;
        margin-bottom: 20px;
        font-size: 18px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .alert-info {
        background-color: rgba(88, 166, 255, 0.1);
        border-left: 4px solid var(--accent-blue);
        padding: 12px;
        border-radius: 4px;
        color: var(--text-primary);
        margin: 12px 0;
        font-size: 13px;
    }
    
    .alert-warning {
        background-color: rgba(210, 153, 34, 0.1);
        border-left: 4px solid var(--accent-yellow);
        padding: 12px;
        border-radius: 4px;
        color: var(--text-primary);
        margin: 12px 0;
        font-size: 13px;
    }
    
    .alert-success {
        background-color: rgba(35, 134, 54, 0.1);
        border-left: 4px solid var(--accent-green);
        padding: 12px;
        border-radius: 4px;
        color: var(--text-primary);
        margin: 12px 0;
        font-size: 13px;
    }
    
    .alert-danger {
        background-color: rgba(218, 54, 51, 0.1);
        border-left: 4px solid var(--accent-red);
        padding: 12px;
        border-radius: 4px;
        color: var(--text-primary);
        margin: 12px 0;
        font-size: 13px;
    }
    
    .score-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 14px;
        text-align: center;
    }
    
    .score-excellent { background-color: rgba(35, 134, 54, 0.3); color: var(--accent-green); }
    .score-good { background-color: rgba(88, 166, 255, 0.3); color: var(--accent-blue); }
    .score-average { background-color: rgba(210, 153, 34, 0.3); color: var(--accent-yellow); }
    .score-poor { background-color: rgba(218, 54, 51, 0.3); color: var(--accent-red); }
    
    table {
        border-collapse: collapse;
        width: 100%;
    }
    
    table th {
        background-color: var(--tertiary-bg);
        border: 1px solid var(--border-color);
        padding: 12px;
        text-align: left;
        font-weight: 700;
        color: var(--accent-blue);
        font-size: 12px;
        text-transform: uppercase;
    }
    
    table td {
        border: 1px solid var(--border-color);
        padding: 12px;
        color: var(--text-primary);
    }
    
    table tr:hover {
        background-color: var(--tertiary-bg);
    }
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

# ============================================================================
# CACHE ET SESSION STATE
# ============================================================================
@st.cache_data(ttl=3600)
def fetch_ticker_data(ticker_str: str) -> Tuple[Optional[yf.Ticker], Optional[str]]:
    """Récupère les données d'un ticker avec gestion d'erreurs."""
    try:
        ticker = yf.Ticker(ticker_str)
        # Vérifier que le ticker est valide en récupérant les infos de base
        info = ticker.info
        if not info or info.get('regularMarketPrice') is None:
            return None, f"❌ Ticker '{ticker_str}' non trouvé ou invalide."
        return ticker, None
    except Exception as e:
        return None, f"❌ Erreur lors de la récupération du ticker '{ticker_str}': {str(e)}"

# ============================================================================
# FONCTION DE CONVERSION DE DEVISES
# ============================================================================
CURRENCY_FALLBACKS = {
    'USD': 0.92,
    'GBp': 0.0115,  # Pence en EUR
    'GBX': 0.0115,
    'GBP': 0.92,
    'CHF': 1.02,
    'CAD': 0.68,
    'JPY': 0.0068,
    'CNY': 0.128,
    'INR': 0.011,
}

@st.cache_data(ttl=3600)
def get_exchange_rate(from_currency: str, to_currency: str = 'EUR') -> float:
    """Récupère le taux de change avec fallback."""
    if from_currency == to_currency:
        return 1.0
    
    try:
        pair = f"{from_currency}{to_currency}=X"
        rate_ticker = yf.Ticker(pair)
        rate = rate_ticker.info.get('regularMarketPrice')
        if rate and rate > 0:
            return float(rate)
    except:
        pass
    
    return CURRENCY_FALLBACKS.get(from_currency, 1.0)

# ============================================================================
# FONCTIONS DE NETTOYAGE DÉFENSIF
# ============================================================================
def safe_float(value: any, default: float = 0.0) -> float:
    """Convertit une valeur en float de manière sécurisée."""
    try:
        if value is None or value == 'N/A':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_pct(value: any, default: str = 'N/A') -> str:
    """Convertit une valeur en pourcentage de manière sécurisée."""
    try:
        if value is None or value == 'N/A':
            return default
        val = float(value)
        return f"{val:.2f}%"
    except (ValueError, TypeError):
        return default

def safe_str(value: any, default: str = 'N/A') -> str:
    """Convertit une valeur en string de manière sécurisée."""
    try:
        if value is None or value == '':
            return default
        return str(value)
    except:
        return default

def format_currency(value: any, currency: str = '€') -> str:
    """Formate une valeur en devise."""
    try:
        val = float(value)
        if abs(val) >= 1_000_000_000:
            return f"{val / 1_000_000_000:.2f}B {currency}"
        elif abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.2f}M {currency}"
        elif abs(val) >= 1_000:
            return f"{val / 1_000:.2f}K {currency}"
        else:
            return f"{val:.2f} {currency}"
    except:
        return 'N/A'

# ============================================================================
# DÉTECTION DE TYPE D'ACTIF (STOCK vs ETF)
# ============================================================================
def detect_asset_type(ticker: yf.Ticker) -> str:
    """Détecte si l'actif est une Action, un ETF, ou un Indice."""
    try:
        quote_type = ticker.info.get('quoteType', '').upper()
        if quote_type in ['ETF', 'FUND']:
            return 'ETF'
        elif quote_type == 'INDEX':
            return 'INDEX'
        elif quote_type in ['EQUITY', 'STOCK']:
            return 'STOCK'
        
        # Fallback basé sur le nom
        name = ticker.info.get('longName', '').lower()
        if 'fund' in name or 'etf' in name:
            return 'ETF'
        return 'STOCK'
    except:
        return 'STOCK'

# ============================================================================
# MODULE 1 : CALCUL DES 21 RATIOS FINANCIERS
# ============================================================================
def calculate_financial_ratios(ticker: yf.Ticker, currency: str = 'EUR') -> Dict:
    """Calcule les 21 ratios financiers + score."""
    info = ticker.info
    exchange_rate = get_exchange_rate(currency)
    
    ratios = {}
    
    # --- VALORISATION & PRIX (8 ratios) ---
    ratios['per_trailing'] = safe_float(info.get('trailingPE'), None)
    ratios['per_forward'] = safe_float(info.get('forwardPE'), None)
    ratios['price_to_sales'] = safe_float(info.get('priceToSalesTrailing12Months'), None)
    ratios['price_to_book'] = safe_float(info.get('priceToBook'), None)
    ratios['ev_to_ebitda'] = safe_float(info.get('enterpriseToEbitda'), None)
    
    # BPA en EUR
    eps = safe_float(info.get('trailingEps'), None)
    if eps:
        ratios['eps'] = eps * exchange_rate
    else:
        ratios['eps'] = None
    
    # Valeur Comptable par Action en EUR
    book_value = safe_float(info.get('bookValue'), None)
    if book_value:
        ratios['book_value'] = book_value * exchange_rate
    else:
        ratios['book_value'] = None
    
    # Prix de Graham
    current_price = safe_float(info.get('currentPrice'), None)
    if eps and book_value and eps > 0 and book_value > 0:
        graham_price = np.sqrt(22.5 * eps * book_value)
        ratios['graham_price'] = graham_price * exchange_rate
    else:
        ratios['graham_price'] = None
    
    # --- RENTABILITÉ & PERFORMANCE (5 ratios) ---
    ratios['gross_margins'] = safe_float(info.get('grossMargins'), None)
    ratios['operating_margins'] = safe_float(info.get('operatingMargins'), None)
    ratios['profit_margins'] = safe_float(info.get('profitMargins'), None)
    ratios['roe'] = safe_float(info.get('returnOnEquity'), None)
    ratios['roa'] = safe_float(info.get('returnOnAssets'), None)
    
    # --- SANTÉ FINANCIÈRE, BILAN & RISQUE (6 ratios) ---
    total_debt = safe_float(info.get('totalDebt'), 0)
    cash = safe_float(info.get('totalCash'), 0)
    net_debt = (total_debt - cash) / 1_000_000 * exchange_rate  # En millions d'EUR
    ratios['net_debt'] = net_debt
    
    ebitda = safe_float(info.get('ebitda'), 0) / 1_000_000 * exchange_rate  # En millions d'EUR
    ratios['ebitda'] = ebitda
    
    if ebitda > 0:
        ratios['net_debt_to_ebitda'] = net_debt / ebitda
    else:
        ratios['net_debt_to_ebitda'] = None
    
    ratios['current_ratio'] = safe_float(info.get('currentRatio'), None)
    ratios['quick_ratio'] = safe_float(info.get('quickRatio'), None)
    
    equity = safe_float(info.get('totalStockholderEquity'), 1)
    if equity > 0:
        ratios['debt_to_equity'] = (total_debt / equity) * 100
    else:
        ratios['debt_to_equity'] = None
    
    # --- CROISSANCE & DIVIDENDES (2 ratios) ---
    ratios['revenue_growth'] = safe_float(info.get('revenueGrowth'), None)
    ratios['payout_ratio'] = safe_float(info.get('payoutRatio'), None)
    
    # --- INFORMATIONS SUPPLÉMENTAIRES ---
    ratios['target_price'] = safe_float(info.get('targetPrice'), None)
    ratios['number_of_analysts'] = safe_float(info.get('numberOfAnalystOpinions'), None)
    ratios['recommendation'] = safe_str(info.get('recommendationKey'), 'N/A')
    
    return ratios

# ============================================================================
# CALCUL DU SCORE FONDAMENTAL GLOBAL
# ============================================================================
def calculate_fundamental_score(ratios: Dict) -> int:
    """Calcule un score fondamental sur 100."""
    score = 50  # Base neutre
    
    # Valorisation (0-20 points)
    per = ratios.get('per_trailing')
    if per and per > 0:
        if per < 15:
            score += 20
        elif per < 20:
            score += 15
        elif per < 30:
            score += 10
        elif per > 40:
            score -= 10
    
    # Marge nette (0-15 points)
    margin = ratios.get('profit_margins')
    if margin:
        margin = safe_float(margin, 0)
        if margin > 0.15:
            score += 15
        elif margin > 0.10:
            score += 12
        elif margin > 0.05:
            score += 8
        elif margin < 0:
            score -= 10
    
    # ROE (0-15 points)
    roe = ratios.get('roe')
    if roe:
        roe = safe_float(roe, 0)
        if roe > 0.20:
            score += 15
        elif roe > 0.15:
            score += 12
        elif roe > 0.10:
            score += 8
        elif roe < 0:
            score -= 10
    
    # Levier (0-15 points)
    net_debt_to_ebitda = ratios.get('net_debt_to_ebitda')
    if net_debt_to_ebitda is not None:
        if net_debt_to_ebitda < 1:
            score += 15
        elif net_debt_to_ebitda < 2:
            score += 12
        elif net_debt_to_ebitda < 3:
            score += 8
        else:
            score -= 5
    elif ratios.get('net_debt', 0) < 0:  # Cash positif
        score += 15
    
    # Prix de Graham (0-15 points)
    graham = ratios.get('graham_price')
    current_price = safe_float(ratios.get('current_price'), 1)
    if graham and current_price and graham > current_price:
        ratio = graham / current_price
        if ratio > 1.5:
            score += 15
        elif ratio > 1.2:
            score += 12
        elif ratio > 1.0:
            score += 8
    
    # Croissance (0-10 points)
    growth = ratios.get('revenue_growth')
    if growth:
        growth = safe_float(growth, 0)
        if growth > 0.20:
            score += 10
        elif growth > 0.10:
            score += 7
        elif growth > 0:
            score += 4
    
    # Dividende (0-5 points)
    payout = ratios.get('payout_ratio')
    if payout:
        payout = safe_float(payout, 0)
        if 0.20 <= payout <= 0.60:
            score += 5
    
    # Liquidité (0-5 points)
    current_ratio = ratios.get('current_ratio')
    if current_ratio:
        current_ratio = safe_float(current_ratio, 0)
        if current_ratio > 1.5:
            score += 5
        elif current_ratio > 1.0:
            score += 3
    
    return max(0, min(100, score))

# ============================================================================
# MODULE 2 : ANALYSE DES ETF
# ============================================================================
def analyze_etf(ticker: yf.Ticker) -> Dict:
    """Analyse spécifique pour les ETF."""
    info = ticker.info
    
    analysis = {
        'ter': safe_float(info.get('fundFamilyName'), None),  # Fallback
        'ter_value': safe_float(info.get('expenseRatio'), None),
        'aum': safe_float(info.get('fundSize'), None),  # En USD généralement
        'fund_type': safe_str(info.get('fundType'), 'Non spécifié'),
        'index_tracked': safe_str(info.get('fundFamily'), 'N/A'),
        'inception_date': safe_str(info.get('inceptionDate'), 'N/A'),
    }
    
    # Déterminer si Acc ou Dist
    name = info.get('longName', '').lower()
    if 'acc' in name or 'cap' in name:
        analysis['distribution'] = '📈 Capitalisation (Acc)'
    elif 'dist' in name:
        analysis['distribution'] = '💵 Distribution (Dist)'
    else:
        analysis['distribution'] = 'Non déterminé'
    
    return analysis

# ============================================================================
# MODULE 4 : SIMULATEUR DCA (DOLLAR COST AVERAGING)
# ============================================================================
def simulate_dca(ticker: yf.Ticker, monthly_amount: float, years_back: int) -> Dict:
    """Simule un investissement DCA sur une période donnée."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years_back)
        
        # Récupérer l'historique
        history = ticker.history(start=start_date, end=end_date)
        
        if history.empty:
            return {
                'error': 'Aucune donnée historique disponible pour cet actif.'
            }
        
        # Initialiser les listes de résultats
        dates = []
        invested_amounts = []
        portfolio_values = []
        shares = []
        
        total_invested = 0
        total_shares = 0
        
        # Simuler l'achat le premier jour ouvré de chaque mois
        current_date = start_date
        while current_date <= end_date:
            # Trouver le premier jour ouvré du mois
            first_of_month = current_date.replace(day=1)
            
            # Chercher le premier jour avec des données
            month_data = history[history.index.month == first_of_month.month]
            month_data = month_data[month_data.index.year == first_of_month.year]
            
            if not month_data.empty:
                purchase_date = month_data.index[0]
                purchase_price = float(month_data['Close'].iloc[0])
                
                if purchase_price > 0:
                    # Acheter des actions
                    shares_bought = monthly_amount / purchase_price
                    total_shares += shares_bought
                    total_invested += monthly_amount
                    
                    # Valeur du portefeuille au prix d'achat
                    portfolio_value = total_shares * purchase_price
                    
                    dates.append(purchase_date)
                    invested_amounts.append(total_invested)
                    portfolio_values.append(portfolio_value)
                    shares.append(total_shares)
            
            # Passer au mois suivant
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1, day=1)
        
        # Valeur finale au dernier prix connu
        last_price = float(history['Close'].iloc[-1])
        final_value = total_shares * last_price
        
        # Rendement
        if total_invested > 0:
            gain = final_value - total_invested
            roi = (gain / total_invested) * 100
        else:
            gain = 0
            roi = 0
        
        return {
            'dates': dates,
            'invested': invested_amounts,
            'portfolio_values': portfolio_values,
            'total_invested': total_invested,
            'final_value': final_value,
            'gain': gain,
            'roi': roi,
            'total_shares': total_shares,
            'last_price': last_price,
            'error': None
        }
    
    except Exception as e:
        return {
            'error': f'Erreur lors de la simulation DCA: {str(e)}'
        }

# ============================================================================
# MODULE 5 : FLUX D'ACTUALITÉS
# ============================================================================
def get_news(ticker: yf.Ticker) -> List[Dict]:
    """Récupère les actualités avec gestion d'erreurs."""
    try:
        news = ticker.news
        if not news:
            return []
        
        parsed_news = []
        for article in news[:10]:  # Limiter à 10 articles
            parsed_news.append({
                'title': article.get('title', 'Sans titre'),
                'link': article.get('link', '#'),
                'source': article.get('source', 'Source inconnue'),
                'timestamp': article.get('providerPublishTime', 0),
            })
        return parsed_news
    except:
        return []

# ============================================================================
# GRAPHIQUES PLOTLY
# ============================================================================
def plot_price_history_with_ma(ticker: yf.Ticker, years: int = 5) -> go.Figure:
    """Graphique du prix avec moyennes mobiles et RSI."""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        history = ticker.history(start=start_date, end=end_date)
        
        if history.empty:
            return go.Figure().add_annotation(text="Pas de données disponibles")
        
        # Calculer les moyennes mobiles
        history['SMA_50'] = history['Close'].rolling(window=50).mean()
        history['SMA_200'] = history['Close'].rolling(window=200).mean()
        
        # Calculer le RSI
        def calculate_rsi(data, period=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        history['RSI'] = calculate_rsi(history['Close'])
        
        # Créer la figure avec deux axes Y
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )
        
        # Graphique du prix
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history['Close'],
                name='Prix de clôture',
                line=dict(color='#58a6ff', width=2),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # SMA 50
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history['SMA_50'],
                name='SMA 50',
                line=dict(color='#238636', width=1, dash='dash'),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # SMA 200
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history['SMA_200'],
                name='SMA 200',
                line=dict(color='#d29922', width=1, dash='dash'),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # RSI
        fig.add_trace(
            go.Scatter(
                x=history.index,
                y=history['RSI'],
                name='RSI (14)',
                line=dict(color='#da3633', width=2),
                mode='lines'
            ),
            row=2, col=1
        )
        
        # Lignes de référence RSI
        fig.add_hline(y=70, line_dash="dash", line_color="#da3633", opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#238636", opacity=0.5, row=2, col=1)
        
        # Mise en forme
        fig.update_layout(
            title=f'Analyse Technique - {ticker.ticker} (5 ans)',
            hovermode='x unified',
            template='plotly_dark',
            height=700,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Prix (€)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        
        return fig
    except Exception as e:
        fig = go.Figure()
        fig.add_annotation(text=f"Erreur: {str(e)}")
        return fig

def plot_dca_simulation(dca_results: Dict) -> go.Figure:
    """Graphique de la simulation DCA."""
    if 'error' in dca_results and dca_results['error']:
        fig = go.Figure()
        fig.add_annotation(text=dca_results['error'])
        return fig
    
    dates = dca_results['dates']
    invested = dca_results['invested']
    portfolio = dca_results['portfolio_values']
    
    fig = go.Figure()
    
    # Zone entre investissement et portefeuille
    fig.add_trace(go.Scatter(
        x=dates + dates[::-1],
        y=invested + portfolio[::-1],
        fill='toself',
        fillcolor='rgba(88, 166, 255, 0.2)',
        line=dict(color='rgba(88, 166, 255, 0)'),
        showlegend=False
    ))
    
    # Courbe du capital investi
    fig.add_trace(go.Scatter(
        x=dates,
        y=invested,
        name='Capital Investi',
        line=dict(color='#d29922', width=3, dash='dash'),
        mode='lines'
    ))
    
    # Courbe de la valeur du portefeuille
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio,
        name='Valeur du Portefeuille',
        line=dict(color='#58a6ff', width=3),
        mode='lines'
    ))
    
    fig.update_layout(
        title='Simulation DCA (Dollar Cost Averaging)',
        hovermode='x unified',
        template='plotly_dark',
        height=500,
        xaxis_title='Date',
        yaxis_title='Valeur (€)',
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

# ============================================================================
# INTERFACE PRINCIPALE STREAMLIT
# ============================================================================
st.markdown("# 📊 Alpha Terminal Pro")
st.markdown("*Plateforme d'Analyse Financière Professionnelle - Optimisée pour Actions, ETF et Indices*")

# --- Barre latérale ---
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.divider()
    
    app_mode = st.radio(
        "Sélectionner le module :",
        options=[
            "🔍 Analyse Action/ETF",
            "📊 Comparateur Multi-Actifs",
            "💰 Simulateur DCA",
            "📰 Actualités",
            "ℹ️ À Propos"
        ],
        index=0
    )

# ============================================================================
# MODULE 1 : ANALYSE SIMPLE ACTION/ETF
# ============================================================================
if app_mode == "🔍 Analyse Action/ETF":
    st.markdown('<div class="section-header">📈 Analyse Détaillée d\'un Actif</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        ticker_input = st.text_input(
            "Entrer le code ticker (ex: AAPL, LVMH.PA, CW8.PA) :",
            placeholder="AAPL",
            help="Saisissez le symbole du titre à analyser"
        )
    
    with col2:
        search_button = st.button("🔎 Analyser", use_container_width=True)
    
    if search_button and ticker_input:
        ticker_input = ticker_input.strip().upper()
        
        with st.spinner(f"⏳ Chargement des données pour {ticker_input}..."):
            ticker_obj, error_msg = fetch_ticker_data(ticker_input)
        
        if error_msg:
            st.error(error_msg)
        else:
            try:
                info = ticker_obj.info
                asset_type = detect_asset_type(ticker_obj)
                currency = info.get('currency', 'USD')
                exchange_rate = get_exchange_rate(currency)
                
                # --- EN-TÊTE AVEC INFOS PRINCIPALES ---
                col1, col2, col3, col4, col5 = st.columns(5)
                
                current_price = safe_float(info.get('currentPrice'), 0)
                current_price_eur = current_price * exchange_rate
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">💰 Prix Actuel</div>
                        <div class="metric-value">{format_currency(current_price_eur, '€')}</div>
                        <div class="metric-label" style="font-size: 10px; margin-top: 8px;">{currency}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                market_cap = safe_float(info.get('marketCap'), 0) * exchange_rate / 1_000_000_000
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🏢 Capitalisation</div>
                        <div class="metric-value">{format_currency(market_cap * 1_000_000_000, '€')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Calculer le score
                ratios = calculate_financial_ratios(ticker_obj, currency)
                ratios['current_price'] = current_price
                score = calculate_fundamental_score(ratios)
                
                score_class = "score-excellent" if score >= 75 else "score-good" if score >= 60 else "score-average" if score >= 40 else "score-poor"
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📊 Score Fondamental</div>
                        <div class="score-badge {score_class}" style="width: 100%; text-align: center; font-size: 28px;">{score}/100</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                change_pct = safe_float(info.get('regularMarketChangePercent'), 0)
                change_color = "positive" if change_pct >= 0 else "negative"
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">📈 Variation (24h)</div>
                        <div class="metric-value {change_color}">{change_pct:+.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col5:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">🏷️ Type d'Actif</div>
                        <div class="metric-value neutral" style="font-size: 16px;">{asset_type}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # --- ONGLETS POUR LES DIFFÉRENTES ANALYSES ---
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📋 21 Ratios",
                    "📊 Graphiques",
                    f"💼 {asset_type}",
                    "💹 DCA",
                    "📰 Actualités"
                ])
                
                # --- TAB 1 : 21 RATIOS ---
                with tab1:
                    st.markdown('<div class="section-header">A. Valorisation & Prix (8 ratios)</div>', unsafe_allow_html=True)
                    
                    cols_a = st.columns(4)
                    col_idx = 0
                    
                    # 1. PER Trailing
                    per_t = ratios.get('per_trailing')
                    per_t_str = f"{per_t:.2f}x" if per_t else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣ PER Actuel</div>
                            <div class="metric-value">{per_t_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 2. PER Forward
                    per_f = ratios.get('per_forward')
                    per_f_str = f"{per_f:.2f}x" if per_f else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">2️⃣ PER Futur</div>
                            <div class="metric-value">{per_f_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 3. P/S
                    ps = ratios.get('price_to_sales')
                    ps_str = f"{ps:.2f}x" if ps else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">3️⃣ Price to Sales</div>
                            <div class="metric-value">{ps_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 4. P/B
                    pb = ratios.get('price_to_book')
                    pb_str = f"{pb:.2f}x" if pb else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">4️⃣ Price to Book</div>
                            <div class="metric-value">{pb_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 5. EV/EBITDA
                    ev_ebitda = ratios.get('ev_to_ebitda')
                    ev_ebitda_str = f"{ev_ebitda:.2f}x" if ev_ebitda else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">5️⃣ EV/EBITDA</div>
                            <div class="metric-value">{ev_ebitda_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 6. BPA
                    eps = ratios.get('eps')
                    eps_str = f"{eps:.2f} €" if eps else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">6️⃣ BPA (EPS)</div>
                            <div class="metric-value">{eps_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 7. Valeur Comptable
                    bv = ratios.get('book_value')
                    bv_str = f"{bv:.2f} €" if bv else "N/A"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">7️⃣ Valeur Comptable/Action</div>
                            <div class="metric-value">{bv_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    col_idx += 1
                    
                    # 8. Prix de Graham
                    graham = ratios.get('graham_price')
                    graham_str = f"{graham:.2f} €" if graham else "N/A"
                    graham_eval = "✅ Sous-évalué" if (graham and current_price_eur and graham > current_price_eur) else "⚠️ Surévalué" if graham else "❓"
                    with cols_a[col_idx % 4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">8️⃣ Prix de Graham</div>
                            <div class="metric-value">{graham_str}</div>
                            <div class="metric-label" style="font-size: 10px; margin-top: 8px;">{graham_eval}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown('<div class="section-header">B. Rentabilité & Performance (5 ratios)</div>', unsafe_allow_html=True)
                    
                    cols_b = st.columns(5)
                    
                    gm = ratios.get('gross_margins')
                    gm_str = f"{gm*100:.2f}%" if gm else "N/A"
                    with cols_b[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">9️⃣ Marge Brute</div>
                            <div class="metric-value">{gm_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    om = ratios.get('operating_margins')
                    om_str = f"{om*100:.2f}%" if om else "N/A"
                    with cols_b[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">🔟 Marge Opérationnelle</div>
                            <div class="metric-value">{om_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    pm = ratios.get('profit_margins')
                    pm_str = f"{pm*100:.2f}%" if pm else "N/A"
                    with cols_b[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣1️⃣ Marge Nette</div>
                            <div class="metric-value">{pm_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    roe = ratios.get('roe')
                    roe_str = f"{roe*100:.2f}%" if roe else "N/A"
                    with cols_b[3]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣2️⃣ ROE</div>
                            <div class="metric-value">{roe_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    roa = ratios.get('roa')
                    roa_str = f"{roa*100:.2f}%" if roa else "N/A"
                    with cols_b[4]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣3️⃣ ROA</div>
                            <div class="metric-value">{roa_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown('<div class="section-header">C. Santé Financière, Bilan & Risque (6 ratios)</div>', unsafe_allow_html=True)
                    
                    cols_c = st.columns(3)
                    
                    net_debt = ratios.get('net_debt', 0)
                    net_debt_str = format_currency(net_debt * 1_000_000, '€') if net_debt else "N/A"
                    with cols_c[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣4️⃣ Dette Nette</div>
                            <div class="metric-value">{net_debt_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    ebitda = ratios.get('ebitda', 0)
                    ebitda_str = format_currency(ebitda * 1_000_000, '€') if ebitda else "N/A"
                    with cols_c[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣5️⃣ EBITDA</div>
                            <div class="metric-value">{ebitda_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    net_debt_ebitda = ratios.get('net_debt_to_ebitda')
                    if net_debt_ebitda is not None:
                        net_debt_ebitda_str = f"{net_debt_ebitda:.2f}x"
                    elif net_debt and net_debt < 0:
                        net_debt_ebitda_str = "💵 Cash Positif"
                    else:
                        net_debt_ebitda_str = "N/A"
                    with cols_c[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣6️⃣ Dette Nette/EBITDA</div>
                            <div class="metric-value">{net_debt_ebitda_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    cols_c2 = st.columns(3)
                    
                    cr = ratios.get('current_ratio')
                    cr_str = f"{cr:.2f}x" if cr else "N/A"
                    with cols_c2[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣7️⃣ Ratio Liquidité Générale</div>
                            <div class="metric-value">{cr_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    qr = ratios.get('quick_ratio')
                    qr_str = f"{qr:.2f}x" if qr else "N/A"
                    with cols_c2[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣8️⃣ Ratio Liquidité Immédiate</div>
                            <div class="metric-value">{qr_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    dte = ratios.get('debt_to_equity')
                    dte_str = f"{dte:.2f}%" if dte else "N/A"
                    with cols_c2[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">1️⃣9️⃣ Dette/Capitaux Propres</div>
                            <div class="metric-value">{dte_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown('<div class="section-header">D. Croissance & Dividendes (2 ratios)</div>', unsafe_allow_html=True)
                    
                    cols_d = st.columns(2)
                    
                    rg = ratios.get('revenue_growth')
                    rg_str = f"{rg*100:.2f}%" if rg else "N/A"
                    with cols_d[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">2️⃣0️⃣ Croissance Chiffre d'Affaires</div>
                            <div class="metric-value">{rg_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    pr = ratios.get('payout_ratio')
                    pr_str = f"{pr*100:.2f}%" if pr else "N/A"
                    with cols_d[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">2️⃣1️⃣ Taux Distribution Dividende</div>
                            <div class="metric-value">{pr_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown('<div class="section-header">E. Consensus & Analystes</div>', unsafe_allow_html=True)
                    
                    cols_e = st.columns(3)
                    
                    target_price = ratios.get('target_price')
                    target_price_eur = target_price * exchange_rate if target_price else None
                    target_str = f"{format_currency(target_price_eur, '€')}" if target_price_eur else "N/A"
                    potential = "N/A"
                    if target_price_eur and current_price_eur:
                        potential = f"{((target_price_eur / current_price_eur - 1) * 100):.2f}%"
                    
                    with cols_e[0]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">🎯 Objectif de Cours</div>
                            <div class="metric-value">{target_str}</div>
                            <div class="metric-label" style="font-size: 10px; margin-top: 8px;">Potentiel: {potential}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    num_analysts = ratios.get('number_of_analysts')
                    num_analysts_str = f"{int(num_analysts)}" if num_analysts else "N/A"
                    with cols_e[1]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">👥 Nombre d'Analystes</div>
                            <div class="metric-value">{num_analysts_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    recommendation = ratios.get('recommendation', 'N/A').upper()
                    rec_emoji = "📈" if "BUY" in recommendation else "➡️" if "HOLD" in recommendation else "📉" if "SELL" in recommendation else "❓"
                    
                    with cols_e[2]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">🎯 Recommandation</div>
                            <div class="metric-value">{rec_emoji} {recommendation}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # --- TAB 2 : GRAPHIQUES ---
                with tab2:
                    st.markdown('<div class="section-header">📊 Analyse Technique (5 ans)</div>', unsafe_allow_html=True)
                    
                    fig_price = plot_price_history_with_ma(ticker_obj, years=5)
                    st.plotly_chart(fig_price, use_container_width=True)
                
                # --- TAB 3 : ANALYSE SPÉCIFIQUE (STOCK vs ETF) ---
                with tab3:
                    if asset_type == 'ETF':
                        st.markdown('<div class="section-header">💼 Analyse ETF</div>', unsafe_allow_html=True)
                        
                        etf_data = analyze_etf(ticker_obj)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">💸 Frais de Gestion (TER)</div>
                                <div class="metric-value">{etf_data['ter_value'] if etf_data['ter_value'] else 'N/A'}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">📊 Politique de Distribution</div>
                                <div class="metric-value" style="font-size: 16px;">{etf_data['distribution']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">💰 Encours (AUM)</div>
                                <div class="metric-value">{format_currency(etf_data['aum'], '€') if etf_data['aum'] else 'N/A'}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if etf_data['aum'] and etf_data['aum'] < 100_000_000:
                                st.markdown('<div class="alert-warning">⚠️ Encours faible: risque de clôture</div>', unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">🏷️ Type de Fonds</div>
                                <div class="metric-value" style="font-size: 16px;">{etf_data['fund_type']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.divider()
                        st.markdown("### 📋 Informations Supplémentaires")
                        info_col1, info_col2 = st.columns(2)
                        with info_col1:
                            st.write(f"**Indice suivi:** {etf_data['index_tracked']}")
                        with info_col2:
                            st.write(f"**Date de création:** {etf_data['inception_date']}")
                        
                        st.markdown(f"""
                        <div class="alert-info">
                        💡 **Conseil PEA:** Cette analyse ne détermine pas automatiquement l'éligibilité PEA.
                        Vérifiez auprès de votre courtier pour confirmer si cet ETF est éligible au PEA.
                        </div>
                        """, unsafe_allow_html=True)
                    
                    else:
                        st.markdown('<div class="section-header">📈 Analyse Action</div>', unsafe_allow_html=True)
                        
                        dividend_yield = safe_float(info.get('dividendYield'), None)
                        dy_str = f"{dividend_yield*100:.2f}%" if dividend_yield else "N/A"
                        
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">💵 Rendement du Dividende</div>
                            <div class="metric-value">{dy_str}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.divider()
                        st.markdown("### 📊 Autres Informations")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Secteur", safe_str(info.get('sector'), 'N/A'))
                        with col2:
                            st.metric("Industrie", safe_str(info.get('industry'), 'N/A'))
                        with col3:
                            st.metric("Pays", safe_str(info.get('country'), 'N/A'))
                        
                        st.divider()
                        st.markdown("### 📝 Description de l'Entreprise")
                        description = safe_str(info.get('longBusinessSummary'), 'Pas de description disponible')
                        st.write(description[:500] + "..." if len(description) > 500 else description)
                
                # --- TAB 4 : SIMULATEUR DCA ---
                with tab4:
                    st.markdown('<div class="section-header">💰 Simulateur DCA (Dollar Cost Averaging)</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        monthly_amount = st.number_input(
                            "Montant mensuel (€):",
                            min_value=10.0,
                            value=150.0,
                            step=10.0
                        )
                    
                    with col2:
                        years = st.selectbox(
                            "Recul historique:",
                            options=[1, 3, 5, 10],
                            index=2
                        )
                    
                    if st.button("🚀 Lancer la Simulation", use_container_width=True):
                        with st.spinner("⏳ Simulation en cours..."):
                            dca_results = simulate_dca(ticker_obj, monthly_amount, years)
                        
                        if 'error' in dca_results and dca_results['error']:
                            st.error(dca_results['error'])
                        else:
                            # Graphique
                            fig_dca = plot_dca_simulation(dca_results)
                            st.plotly_chart(fig_dca, use_container_width=True)
                            
                            # Métriques
                            st.divider()
                            st.markdown("### 📊 Résultats de la Simulation")
                            
                            metric_cols = st.columns(2)
                            with metric_cols[0]:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric(
                                        "Capital Total Investi",
                                        f"{format_currency(dca_results['total_invested'], '€')}"
                                    )
                                with col_b:
                                    st.metric(
                                        "Valeur Finale",
                                        f"{format_currency(dca_results['final_value'], '€')}"
                                    )
                            
                            with metric_cols[1]:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    gain_color = "🟢" if dca_results['gain'] >= 0 else "🔴"
                                    st.metric(
                                        "Plus-value Nette",
                                        f"{gain_color} {format_currency(dca_results['gain'], '€')}"
                                    )
                                with col_b:
                                    roi_color = "🟢" if dca_results['roi'] >= 0 else "🔴"
                                    st.metric(
                                        "Rendement (%)",
                                        f"{roi_color} {dca_results['roi']:+.2f}%"
                                    )
                            
                            st.divider()
                            st.markdown("### 📈 Détails Additionnels")
                            detail_cols = st.columns(3)
                            with detail_cols[0]:
                                st.info(f"🪙 **Nombre d'actions achetées:** {dca_results['total_shares']:.4f}")
                            with detail_cols[1]:
                                st.info(f"💹 **Dernier prix:** {format_currency(dca_results['last_price'] * exchange_rate, '€')}")
                            with detail_cols[2]:
                                st.info(f"📅 **Période:** {years} an(s)")
                
                # --- TAB 5 : ACTUALITÉS ---
                with tab5:
                    st.markdown('<div class="section-header">📰 Actualités Récentes</div>', unsafe_allow_html=True)
                    
                    with st.spinner("⏳ Chargement des actualités..."):
                        news_list = get_news(ticker_obj)
                    
                    if not news_list:
                        st.info("📭 Aucune actualité disponible pour cet actif.")
                    else:
                        for idx, article in enumerate(news_list, 1):
                            with st.container():
                                col1, col2 = st.columns([4, 1])
                                
                                with col1:
                                    st.markdown(f"**{idx}. [{article['title']}]({article['link']})**")
                                    st.caption(f"📰 {article['source']}")
                                
                                with col2:
                                    timestamp = article['timestamp']
                                    if timestamp:
                                        date_str = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y")
                                        st.caption(date_str)
                                
                                st.divider()
            
            except Exception as e:
                st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
                st.error(traceback.format_exc())

# ============================================================================
# MODULE 2 : COMPARATEUR MULTI-ACTIFS
# ============================================================================
elif app_mode == "📊 Comparateur Multi-Actifs":
    st.markdown('<div class="section-header">📊 Comparateur Multi-Actifs</div>', unsafe_allow_html=True)
    
    ticker_list_input = st.text_area(
        "Entrer les codes tickers séparés par des virgules (ex: AAPL, MSFT, LVMH.PA, NVDA) :",
        placeholder="AAPL, MSFT, GOOGL, NVDA",
        height=100,
        help="Saisissez les tickers à comparer"
    )
    
    if st.button("🔍 Générer le Comparateur", use_container_width=True):
        if ticker_list_input.strip():
            tickers = [t.strip().upper() for t in ticker_list_input.split(',')]
            
            comparison_data = []
            
            with st.spinner(f"⏳ Analyse de {len(tickers)} actif(s)..."):
                for ticker_str in tickers:
                    ticker_obj, error = fetch_ticker_data(ticker_str)
                    
                    if error:
                        st.warning(error)
                        continue
                    
                    try:
                        info = ticker_obj.info
                        currency = info.get('currency', 'USD')
                        exchange_rate = get_exchange_rate(currency)
                        
                        ratios = calculate_financial_ratios(ticker_obj, currency)
                        ratios['current_price'] = safe_float(info.get('currentPrice'), 0)
                        score = calculate_fundamental_score(ratios)
                        
                        current_price_eur = ratios['current_price'] * exchange_rate
                        market_cap = safe_float(info.get('marketCap'), 0) * exchange_rate
                        
                        comparison_data.append({
                            'Ticker': ticker_str,
                            'Prix (€)': f"{current_price_eur:.2f}",
                            'Capitalisation (Mds €)': f"{market_cap / 1_000_000_000:.2f}",
                            'Score': score,
                            'PER': f"{ratios.get('per_trailing', 0):.2f}" if ratios.get('per_trailing') else "N/A",
                            'P/S': f"{ratios.get('price_to_sales', 0):.2f}" if ratios.get('price_to_sales') else "N/A",
                            'Marge Nette (%)': f"{ratios.get('profit_margins', 0) * 100:.2f}" if ratios.get('profit_margins') else "N/A",
                            'ROE (%)': f"{ratios.get('roe', 0) * 100:.2f}" if ratios.get('roe') else "N/A",
                            'Dette Nette/EBITDA': f"{ratios.get('net_debt_to_ebitda', 0):.2f}" if ratios.get('net_debt_to_ebitda') else "N/A",
                            'Rendement (%)': f"{(safe_float(info.get('regularMarketChangePercent'), 0)):.2f}"
                        })
                    
                    except Exception as e:
                        st.warning(f"Erreur pour {ticker_str}: {str(e)}")
            
            if comparison_data:
                # Trier par score décroissant
                df_comparison = pd.DataFrame(comparison_data)
                df_comparison = df_comparison.sort_values('Score', ascending=False)
                
                st.divider()
                st.markdown('<div class="section-header">📋 Tableau Comparatif</div>', unsafe_allow_html=True)
                
                st.dataframe(
                    df_comparison,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'Score': st.column_config.NumberColumn(format='%d'),
                    }
                )
                
                # Bouton de téléchargement CSV
                st.divider()
                csv_buffer = io.StringIO()
                df_comparison.to_csv(csv_buffer, index=False, sep=';')
                csv_string = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 Télécharger en CSV",
                    data=csv_string,
                    file_name=f"comparateur_actifs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.error("❌ Aucun actif valide trouvé.")
        else:
            st.info("📝 Veuillez entrer au moins un ticker.")

# ============================================================================
# MODULE 3 : SIMULATEUR DCA
# ============================================================================
elif app_mode == "💰 Simulateur DCA":
    st.markdown('<div class="section-header">💰 Simulateur DCA Avancé</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        dca_ticker = st.text_input(
            "Ticker de l'actif :",
            placeholder="AAPL",
            help="Entrez le code ticker de l'actif à simuler"
        )
    
    with col2:
        dca_monthly = st.number_input(
            "Montant mensuel (€) :",
            min_value=10.0,
            value=200.0,
            step=10.0
        )
    
    col3, col4 = st.columns(2)
    
    with col3:
        dca_years = st.selectbox(
            "Recul historique (années) :",
            options=[1, 2, 3, 5, 10],
            index=2
        )
    
    with col4:
        st.write("")
        st.write("")
        if st.button("🚀 Lancer Simulation Complète", use_container_width=True):
            dca_ticker = dca_ticker.strip().upper()
            
            with st.spinner(f"⏳ Chargement de {dca_ticker}..."):
                ticker_obj, error = fetch_ticker_data(dca_ticker)
            
            if error:
                st.error(error)
            else:
                with st.spinner("⏳ Simulation en cours..."):
                    dca_results = simulate_dca(ticker_obj, dca_monthly, dca_years)
                
                if 'error' in dca_results and dca_results['error']:
                    st.error(dca_results['error'])
                else:
                    fig_dca = plot_dca_simulation(dca_results)
                    st.plotly_chart(fig_dca, use_container_width=True)
                    
                    st.divider()
                    
                    # Résumé
                    summary_cols = st.columns(4)
                    
                    with summary_cols[0]:
                        st.metric(
                            "💰 Capital Investi",
                            f"{format_currency(dca_results['total_invested'], '€')}"
                        )
                    
                    with summary_cols[1]:
                        st.metric(
                            "📈 Valeur Finale",
                            f"{format_currency(dca_results['final_value'], '€')}"
                        )
                    
                    with summary_cols[2]:
                        gain_indicator = "📈" if dca_results['gain'] >= 0 else "📉"
                        st.metric(
                            "💵 Plus-value Nette",
                            f"{gain_indicator} {format_currency(dca_results['gain'], '€')}"
                        )
                    
                    with summary_cols[3]:
                        roi_indicator = "🟢" if dca_results['roi'] >= 0 else "🔴"
                        st.metric(
                            "📊 Rendement",
                            f"{roi_indicator} {dca_results['roi']:+.2f}%"
                        )
                    
                    st.divider()
                    
                    st.markdown("### 📊 Analyse Détaillée")
                    
                    analysis_cols = st.columns(3)
                    with analysis_cols[0]:
                        st.info(f"🪙 **Actions achetées:** {dca_results['total_shares']:.6f}")
                    with analysis_cols[1]:
                        st.info(f"💹 **Cotation actuelle:** {format_currency(dca_results['last_price'], currency)}")
                    with analysis_cols[2]:
                        st.info(f"📅 **Période:** {dca_years} an(s) ({len(dca_results['dates'])} achats)")

# ============================================================================
# MODULE 5 : ACTUALITÉS
# ============================================================================
elif app_mode == "📰 Actualités":
    st.markdown('<div class="section-header">📰 Flux d\'Actualités Financières</div>', unsafe_allow_html=True)
    
    news_ticker = st.text_input(
        "Entrer le ticker pour voir les actualités :",
        placeholder="AAPL",
        help="Saisissez le code ticker"
    )
    
    if news_ticker.strip():
        news_ticker = news_ticker.strip().upper()
        
        with st.spinner(f"⏳ Chargement de {news_ticker}..."):
            ticker_obj, error = fetch_ticker_data(news_ticker)
        
        if error:
            st.error(error)
        else:
            with st.spinner("📰 Récupération des actualités..."):
                news_articles = get_news(ticker_obj)
            
            if not news_articles:
                st.info(f"📭 Aucune actualité disponible pour {news_ticker}.")
            else:
                st.success(f"✅ {len(news_articles)} actualité(s) trouvée(s) pour {news_ticker}")
                st.divider()
                
                for idx, article in enumerate(news_articles, 1):
                    with st.container():
                        header_col1, header_col2 = st.columns([4, 1])
                        
                        with header_col1:
                            st.markdown(f"### {idx}. [{article['title']}]({article['link']})")
                        
                        with header_col2:
                            if article['timestamp']:
                                date_obj = datetime.fromtimestamp(article['timestamp'])
                                date_str = date_obj.strftime("%d/%m/%Y %H:%M")
                                st.caption(f"🕐 {date_str}")
                        
                        st.caption(f"📰 **Source:** {article['source']}")
                        st.divider()

# ============================================================================
# PAGE À PROPOS
# ============================================================================
elif app_mode == "ℹ️ À Propos":
    st.markdown('<div class="section-header">ℹ️ À Propos d\'Alpha Terminal Pro</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 🚀 Une Plateforme Financière Professionnelle
    
    **Alpha Terminal Pro** est une application Streamlit advanced d'analyse financière conçue pour les investisseurs,
    traders et analystes financiers professionnels.
    
    ---
    
    ### 📊 Fonctionnalités Principales
    
    #### 1️⃣ **Analyse Détaillée (21 Ratios)**
    - Évaluation complète des actions et ETF
    - 21 ratios financiers calculés automatiquement
    - Score fondamental sur 100 points
    - Analyse comparative avec consensus d'analystes
    
    #### 2️⃣ **Comparateur Multi-Actifs**
    - Comparez jusqu'à N actifs simultanément
    - Tableau comparatif avec tri dynamique
    - Export CSV instantané
    
    #### 3️⃣ **Simulateur DCA Professionnel**
    - Simulation précise de l'investissement programmé
    - Historique réel des prix
    - Rendement et plus-value détaillés
    
    #### 4️⃣ **Analyse Technique Avancée**
    - Graphiques 5 ans avec SMA 50/200
    - Indicateur RSI (14 jours)
    - Tendance et signaux techniques
    
    #### 5️⃣ **Actualités Intégrées**
    - Flux en temps réel
    - Liens directs vers les sources
    - Filtrage par ticker
    
    ---
    
    ### 💱 Conversion de Devises
    
    L'application gère automatiquement la conversion en EUR pour les actifs du monde entier :
    - 🇺🇸 USD → EUR
    - 🇬🇧 GBP et GBp (pence) → EUR
    - 🇨🇭 CHF → EUR
    - 🇨🇦 CAD → EUR
    - Et bien d'autres...
    
    ---
    
    ### 🔐 Robustesse & Sécurité
    
    - ✅ Gestion défensive des données (safe_float, safe_str, etc.)
    - ✅ Fallbacks automatiques en cas d'erreur API
    - ✅ Cache intelligent pour optimiser les performances
    - ✅ Messages d'erreur clairs et informatifs
    
    ---
    
    ### 📚 Technologies Utilisées
    
    - **Streamlit** - Interface web interactive
    - **yfinance** - Données financières Yahoo Finance
    - **Plotly** - Graphiques professionnels
    - **Pandas** - Manipulation de données
    - **NumPy** - Calculs numériques
    
    ---
    
    ### 🎯 Cas d'Usage
    
    1. **Investisseurs Particuliers** - Analyser vos titres avant d'investir
    2. **Traders** - Identifier les opportunités avec les 21 ratios
    3. **Analystes Financiers** - Générer rapidement des comparateurs multi-actifs
    4. **Advisors** - Justifier vos recommandations avec données en temps réel
    5. **Étudiants en Finance** - Apprendre l'analyse financière
    
    ---
    
    ### ⚠️ Disclaimer
    
    Cette application fournit des données à titre informatif uniquement.
    Les analyses présentées ne constituent pas des conseils d'investissement.
    Veuillez consulter un conseiller financier professionnel avant toute décision d'investissement.
    
    ---
    
    ### 📧 Support & Feedback
    
    Pour toute question, suggestion ou bug report, veuillez créer un issue sur GitHub.
    
    **Version:** 1.0.0  
    **Dernière mise à jour:** 2026-05-18
    """)
    
    st.divider()
    
    st.markdown("""
    <div class="alert-info">
    💡 **Astuce Utilisateur:** Utilisez les onglets en haut pour naviguer entre les modules.
    Copiez-collez les tickers Yahoo Finance (ex: AAPL, MSFT, LVMH.PA, CW8.PA).
    </div>
    """, unsafe_allow_html=True)
