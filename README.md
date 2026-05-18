# 📊 Alpha Terminal Pro

Une plateforme d'analyse financière professionnelle construite avec **Streamlit**, **yfinance** et **Plotly**.

## 🚀 Démarrage Rapide

### 1. Cloner le Repository

```bash
git clone https://github.com/lassenza29/alpha-terminal-pro.git
cd alpha-terminal-pro
```

### 2. Créer un Environnement Virtuel

```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

### 3. Installer les Dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer l'Application

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à `http://localhost:8501`.

---

## 📋 Fonctionnalités

### 🔍 Module 1: Analyse Action/ETF
- Calcul automatique de **21 ratios financiers**
- Score fondamental sur 100 points
- Graphiques techniques (SMA 50/200, RSI)
- Simulation DCA intégrée
- Actualités en temps réel

### 📊 Module 2: Comparateur Multi-Actifs
- Comparez plusieurs tickers simultanément
- Tri automatique par score
- Export CSV

### 💰 Module 3: Simulateur DCA
- Investissement programmé précis
- Historique réel des prix
- Rendement et plus-value détaillés

### 📰 Module 4: Actualités
- Flux d'actualités par ticker
- Liens directs vers les sources

---

## 🌍 Couverture Géographique

Actifs supportés dans le monde entier :
- 🇺🇸 **USA**: AAPL, MSFT, GOOGL, NVDA (USD)
- 🇫🇷 **France**: LVMH.PA, AF.PA, SAF.PA (EUR)
- 🇳🇱 **Pays-Bas**: ASML.AS (EUR)
- 🇬🇧 **Royaume-Uni**: GSK.L, SHELL.L (GBp)
- 🇪🇹 **ETF Monde**: CW8.PA, ESE.PA, SPY

---

## 💱 Conversion de Devises

L'application convertit automatiquement en EUR :
- USD, GBP, CHF, CAD, JPY, CNY, INR
- Fallbacks automatiques en cas d'erreur API
- Taux de change en temps réel

---

## 📊 Les 21 Ratios Financiers

### A. Valorisation & Prix (8 ratios)
1. PER Actuel (P/E Trailing)
2. PER Futur (Forward P/E)
3. Price to Sales (P/S)
4. Price to Book (P/B)
5. EV/EBITDA
6. Bénéfice par Action (EPS)
7. Valeur Comptable par Action
8. Prix de Graham

### B. Rentabilité & Performance (5 ratios)
9. Marge Brute
10. Marge Opérationnelle
11. Marge Nette
12. ROE (Return on Equity)
13. ROA (Return on Assets)

### C. Santé Financière (6 ratios)
14. Dette Nette
15. EBITDA
16. Dette Nette / EBITDA
17. Ratio Liquidité Générale
18. Ratio Liquidité Immédiate
19. Dette / Capitaux Propres

### D. Croissance & Dividendes (2 ratios)
20. Croissance du Chiffre d'Affaires
21. Taux de Distribution du Dividende

---

## 🛠️ Architecture Technique

```
alpha-terminal-pro/
├── app.py              # Application principale (800+ lignes)
├── requirements.txt    # Dépendances Python
├── .gitignore         # Fichiers à ignorer
└── README.md          # Ce fichier
```

### Stack Technologique
- **Frontend**: Streamlit (Interface web)
- **Data**: yfinance (Récupération données Yahoo Finance)
- **Graphiques**: Plotly (Visualisations interactives)
- **Calculs**: Pandas + NumPy
- **Cache**: Streamlit Cache

---

## 🔒 Robustesse & Gestion d'Erreurs

✅ **Safe Functions**
- `safe_float()` - Conversion défensive en float
- `safe_pct()` - Conversion défensive en pourcentage
- `safe_str()` - Conversion défensive en string

✅ **Fallbacks**
- Taux de change fallback en cas d'erreur API
- Messages d'erreur clairs
- Try/except systématiques

✅ **Cache & Performance**
- Cache des données (TTL 1 heure)
- Fetch optimisé
- Spinner d'attente utilisateur

---

## 📝 Exemples d'Utilisation

### Analyser une action
```
1. Sélectionner "🔍 Analyse Action/ETF"
2. Entrer: AAPL
3. Cliquer "🔎 Analyser"
4. Consulter les 21 ratios, graphiques, DCA, actualités
```

### Comparer plusieurs titres
```
1. Sélectionner "📊 Comparateur Multi-Actifs"
2. Entrer: AAPL, MSFT, GOOGL, NVDA
3. Tableau trié par score automatiquement généré
4. Télécharger en CSV
```

### Simuler un investissement DCA
```
1. Sélectionner "💰 Simulateur DCA"
2. Entrer: AAPL, 150€/mois, 5 ans
3. Consulter: capital investi, valeur finale, rendement
```

---

## ⚠️ Disclaimer

Cette application fournit des données **à titre informatif uniquement**.
Les analyses ne constituent pas des conseils d'investissement.
Consultez un conseiller financier professionnel avant toute décision.

---

## 📄 Licence

MIT License - Libre d'utilisation

---

## 🤝 Contribution

Les contributions sont bienvenues ! Créez un fork, une branche, et soumettez une pull request.

---

## 📧 Contact

**Créateur**: lassenza29  
**GitHub**: [github.com/lassenza29/alpha-terminal-pro](https://github.com/lassenza29/alpha-terminal-pro)

---

## 🎯 Roadmap v2.0

- [ ] Backtesting de stratégies
- [ ] Analyse de corrélation
- [ ] Screener d'actions (filtres multiples)
- [ ] Portfolio tracker
- [ ] Alertes prix
- [ ] API personnalisée

---

**Version**: 1.0.0  
**Date**: 2026-05-18
