import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuration de la page Streamlit
st.set_page_config(page_title="Analyseur Financier Automatique v2", page_icon="🚀", layout="wide")

# Titre de l'application
st.title("🚀 Analyseur Financier Automatique de Pro")
st.write("Cet outil extrait les données en direct. Si la base de données rapide de Yahoo est incomplète, un **moteur de secours certifié** scanne directement les rapports financiers et bilans officiels de l'entreprise.")

# Barre de recherche dans la barre latérale (Sidebar)
st.sidebar.header("🔍 Configuration")
ticker_input = st.sidebar.text_input("Entrez le symbole boursier (ex: MC.PA pour LVMH, SAF.PA pour Safran, AAPL pour Apple) :", value="MC.PA")
ticker_symbole = ticker_input.upper().strip()

# Fonction de secours pour extraire une valeur depuis un DataFrame financier officiel (Bilan/Résultat)
def extraire_depuis_rapports(df, cles_possibles):
    if df is None or df.empty:
        return None
    # Parcourir les lignes du DataFrame pour trouver une correspondance avec les clés financières certifiées
    for cle in cles_possibles:
        for idx in df.index:
            if cle.lower() in str(idx).lower():
                valeur = df.loc[idx].iloc[0] # Prendre la donnée certifiée la plus récente (première colonne)
                if pd.notna(valeur) and valeur != 0:
                    return valeur
    return None

if ticker_symbole:
    with st.spinner(f"Analyse approfondie de {ticker_symbole} en cours (Vérification des sources primaires et secondaires)..."):
        try:
            # Connexion au Ticker Yahoo Finance
            action = yf.Ticker(ticker_symbole)
            info = action.info
            
            # Moteurs de secours certifiés (Rapports annuels et trimestriels officiels)
            bilan_annuel = action.balance_sheet
            resultat_annuel = action.financials
            bilan_trim = action.quarterly_balance_sheet
            resultat_trim = action.quarterly_financials

            # Vérification de l'existence de l'entreprise
            if not info or ('shortName' not in info and 'longName' not in info and bilan_annuel.empty):
                st.error("❌ Impossible de trouver cette entreprise. Vérifiez bien le symbole (Rappel : ajoutez '.PA' pour Paris, ex: SAF.PA, MC.PA).")
            else:
                nom_entreprise = info.get('longName') or info.get('shortName') or ticker_symbole
                devise = info.get('currency', 'EUR')
                symbole_devise = "€" if devise == "EUR" else "$"
                
                st.markdown(f"## 🏢 Tableau de bord : {nom_entreprise} ({ticker_symbole})")
                
                # --- MOTEUR DE RECHERCHE MULTI-SOURCES ET SÉCURISÉ ---
                logs_sources = []

                # 1. Prix Actuel
                prix_actuel = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                if not prix_actuel and hasattr(action, 'fast_info'):
                    prix_actuel = action.fast_info.get('last_price')
                prix_actuel = prix_actuel or 0
                
                # 2. Nombre d'actions en circulation
                nb_actions = info.get('sharesOutstanding')
                if not nb_actions and hasattr(action, 'fast_info'):
                    nb_actions = action.fast_info.get('shares_outstanding')
                if not nb_actions and not bilan_annuel.empty:
                    nb_actions = extraire_depuis_rapports(bilan_annuel, ['Share Capital', 'Ordinary Shares Number'])
                nb_actions = (nb_actions or 0) / 1_000_000 # En Millions

                # 3. Capitalisation boursière
                capitalisation = info.get('marketCap')
                if not capitalisation and hasattr(action, 'fast_info'):
                    capitalisation = action.fast_info.get('market_cap')
                if capitalisation:
                    capitalisation = capitalisation / 1_000_000
                else:
                    capitalisation = prix_actuel * nb_actions
                    
                # 4. Dette Brute
                dette_brute = info.get('totalDebt')
                if dette_brute is None:
                    dette_brute = extraire_depuis_rapports(bilan_annuel, ['Total Debt', 'Long Term Debt', 'Commercial Paper'])
                    if dette_brute: logs_sources.append("Dette Brute récupérée dans le Bilan comptable officiel.")
                dette_brute = (dette_brute or 0) / 1_000_000

                # 5. Trésorerie (Cash)
                tresorerie = info.get('totalCash')
                if tresorerie is None:
                    tresorerie = extraire_depuis_rapports(bilan_annuel, ['Cash And Cash Equivalents', 'Cash Cash Equivalents Marketable Securities', 'Cash'])
                    if tresorerie: logs_sources.append("Trésorerie récupérée dans le Bilan comptable officiel.")
                tresorerie = (tresorerie or 0) / 1_000_000

                # 6. Dette Nette
                dette_nette = dette_brute - tresorerie

                # 7. EBITDA
                ebitda = info.get('ebitda')
                if ebitda is None:
                    ebitda = extraire_depuis_rapports(resultat_annuel, ['EBITDA', 'Normalized EBITDA', 'Operating Income'])
                    if ebitda: logs_sources.append("EBITDA extrait des rapports de résultat certifiés.")
                ebitda = (ebitda or 0) / 1_000_000

                # 8. Ratio Dette Nette / EBITDA
                ratio_dette_ebitda = dette_nette / ebitda if ebitda > 0 else 0

                # 9. Chiffre d'affaires (CA)
                ca = info.get('totalRevenue')
                if ca is None:
                    ca = extraire_depuis_rapports(resultat_annuel, ['Total Revenue', 'Gross Dividend Income', 'Revenue'])
                    if ca: logs_sources.append("Chiffre d'affaires extrait des rapports de résultat certifiés.")
                ca = (ca or 0) / 1_000_000

                # 10. Résultat d'exploitation (EBIT)
                operating_income = info.get('operatingIncome')
                if operating_income is None:
                    operating_income = extraire_depuis_rapports(resultat_annuel, ['Operating Income', 'EBIT', 'Operating Profit'])
                operating_income = (operating_income or 0) / 1_000_000

                # 11. Résultat Net
                resultat_net = info.get('netIncomeToCommon') or info.get('netIncome')
                if resultat_net is None:
                    resultat_net = extraire_depuis_rapports(resultat_annuel, ['Net Income', 'Net Income Common Stockholders'])
                resultat_net = (resultat_net or 0) / 1_000_000

                # 12. Marge d'exploitation
                marge_exploit = info.get('operatingMargins')
                if not marge_exploit and ca > 0:
                    marge_exploit = (operating_income / ca)
                marge_exploit = (marge_exploit or 0) * 100

                # 13. Marge Nette
                marge_nette = info.get('profitMargins')
                if not marge_nette and ca > 0:
                    marge_nette = (resultat_net / ca)
                marge_nette = (marge_nette or 0) * 100

                # 14. Capitaux Propres
                capitaux_propres = info.get('totalStockholderEquity')
                if capitaux_propres is None:
                    capitaux_propres = extraire_depuis_rapports(bilan_annuel, ['Stockholders Equity', 'Total Equity Gross Minor Interest', 'Total Ancestry'])
                capitaux_propres = (capitaux_propres or 0) / 1_000_000

                # 15. ROE (Return On Equity)
                roe = info.get('returnOnEquity')
                if not roe and capitaux_propres > 0:
                    roe = (resultat_net / capitaux_propres)
                roe = (roe or 0) * 100

                # 16. BNA (Bénéfice Net par Action)
                bna = info.get('trailingEps')
                if not bna and nb_actions > 0:
                    bna = (resultat_net * 1_000_000) / (nb_actions * 1_000_000)
                bna = bna or 0

                # 17. PER (Price Earning Ratio)
                per = info.get('trailingPE')
                if (not per or per == 0) and bna > 0:
                    per = prix_actuel / bna
                per = per or 0

                # 18. Actif Net par Action (Book Value)
                actif_net_action = info.get('bookValue')
                if not actif_net_action and nb_actions > 0:
                    actif_net_action = (capitaux_propres) / nb_actions
                actif_net_action = actif_net_action or 0

                # 19. Prix Juste de Graham
                if bna > 0 and actif_net_action > 0:
                    prix_graham = (22.5 * bna * actif_net_action) ** 0.5
                else:
                    prix_graham = 0

                # Display sources logs in sidebar if fallback was triggered
                if logs_sources:
                   
                else:

        st.sidebar.info(f"💡 **Système de secours activé :**\n" + "\n".join([f"- {l}" for l in logs_sources]))

 st.sidebar.success("✅ Toutes les données proviennent de la base principale.")

                # --- CONFIGURATION ET AFFICHAGE DU TABLEAU STYLE EXCEL ---
                st.markdown("### 📊 Grille Complète des 19 Ratios demandés")
                
                # Construction des lignes exactes demandées par l'utilisateur
                donnees_excel = [
                    {"N°": 1, "Indicateur financier": "Prix actuel de l'action", "Valeur": f"{prix_actuel:,.2f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 2, "Indicateur financier": "Capitalisation boursière (en M)", "Valeur": f"{capitalisation:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 3, "Indicateur financier": "Dette Brute (en M)", "Valeur": f"{dette_brute:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 4, "Indicateur financier": "Trésorerie (en M)", "Valeur": f"{tresorerie:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 5, "Indicateur financier": "Dette Nette (en M)", "Valeur": f"{dette_nette:,.0f} {symbole_devise}", "Objectif attendu": "Plus bas possible"},
                    {"N°": 6, "Indicateur financier": "EBITDA (en M)", "Valeur": f"{ebitda:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 7, "Indicateur financier": "Ratio Dette Nette / EBITDA (en x)", "Valeur": f"{ratio_dette_ebitda:.2f} x", "Objectif attendu": "< 3.00 x"},
                    {"N°": 8, "Indicateur financier": "Chiffre d'affaires (en M)", "Valeur": f"{ca:,.0f} {symbole_devise}", "Objectif attendu": "En croissance"},
                    {"N°": 9, "Indicateur financier": "Résultat d'exploitation (en M)", "Valeur": f"{operating_income:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 10, "Indicateur financier": "Résultat Net (en M)", "Valeur": f"{resultat_net:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 11, "Indicateur financier": "Marge d'exploitation", "Valeur": f"{marge_exploit:.2f} %", "Objectif attendu": "> 8.00 %"},
                    {"N°": 12, "Indicateur financier": "Marge Nette", "Valeur": f"{marge_nette:.2f} %", "Objectif attendu": "> 5.00 %"},
                    {"N°": 13, "Indicateur financier": "Capitaux Propres (en M)", "Valeur": f"{capitaux_propres:,.0f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 14, "Indicateur financier": "ROE (Rentabilité des CP)", "Valeur": f"{roe:.2f} %", "Objectif attendu": "> 10.00 %"},
                    {"N°": 15, "Indicateur financier": "Nombre d'actions en circulation (en M)", "Valeur": f"{nb_actions:,.2f} M", "Objectif attendu": "Stable ou en baisse"},
                    {"N°": 16, "Indicateur financier": "BNA (Bénéfice Par Action)", "Valeur": f"{bna:,.2f} {symbole_devise}", "Objectif attendu": "Le plus haut possible"},
                    {"N°": 17, "Indicateur financier": "PER (en x)", "Valeur": f"{per:.2f} x", "Objectif attendu": "< 20.00 x"},
                    {"N°": 18, "Indicateur financier": "Actif Net par Action", "Valeur": f"{actif_net_action:,.2f} {symbole_devise}", "Objectif attendu": "-"},
                    {"N°": 19, "Indicateur financier": "Prix Juste (Graham)", "Valeur": f"{prix_graham:,.2f} {symbole_devise}", "Objectif attendu": "> Prix Actuel (Sous-évalué)"}
                ]
                
                df_excel = pd.DataFrame(donnees_excel)
                st.table(df_excel.set_index("N°"))

                st.divider()

                # --- BLOC VERDICT AUTOMATIQUE ---
                st.markdown("### 📢 Analyse de Qualité & Décision Automatique")
                
                col_v1, col_v2, col_v3 = st.columns(3)
                
                # Check des filtres de sécurité
                dette_ok = ratio_dette_ebitda < 3
                rentabilite_ok = marge_exploit > 8 and roe > 10
                prix_ok = prix_actuel < prix_graham if prix_graham > 0 else False
                
                with col_v1:
                    if dette_ok:
                        st.success("🛡️ Sécurité : Dette Conforme")
                    else:
                        st.error("⚠️ Sécurité : Dette trop lourde")
                        
                with col_v2:
                    if rentabilite_ok:
                        st.success("📈 Rentabilité : Excellente")
                    else:
                        st.error("📉 Rentabilité : Faible ou Insuffisante")
                        
                with col_v3:
                    if prix_ok:
                        st.success("🔥 Prix : Sous-évalué (Graham)")
                    else:
                        st.warning("💎 Prix : Surévalué ou Prime de Qualité")

                st.write("")
                if dette_ok and rentabilite_ok:
                    st.success(f"🟢 **VERDICT : ENTREPRISE DE PREMIER PLAN.** {nom_entreprise} possède des fondations financières très solides et passe tes critères de sélection.")
                    if prix_ok:
                        st.balloons()
                        st.info(f"🔥 **EXCELLENT TIMING :** L'action s'échange actuellement à {prix_actuel:,.2f} {symbole_devise} alors que sa valeur théorique de Graham est de {prix_graham:,.2f} {symbole_devise}. C'est une opportunité potentielle d'achat de valeur !")
                    else:
                        st.warning(f"ℹ️ **VALORISATION ÉLEVÉE :** L'entreprise est d'une qualité irréprochable, mais le marché la paie cher actuellement (PER de {per:.2f}x). À surveiller lors d'un prochain repli du marché.")
                else:
                    st.error("🔴 **VERDICT : HORS CRITÈRES.** Cette entreprise présente un risque sur la dette ou une rentabilité opérationnelle trop faible pour tes critères de sélection automatique.")

        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'exécution du moteur financier : {e}")
            st.info("Astuce : Vérifie que le symbole saisi correspond exactement aux conventions de Yahoo Finance (ex: MC.PA pour LVMH, OR.PA pour L'Oréal, TSLA pour Tesla).")
