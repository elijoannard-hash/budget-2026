import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Mon Budget", page_icon="💸")
st.title("💸 Mon Budget Perso")

# Date butoir
fin_objectif = date(2026, 8, 31)
today = date.today()
mois_restants = (fin_objectif.year - today.year) * 12 + (fin_objectif.month - today.month)
st.caption(f"📅 Objectif Fin d'études : 31 Août 2026 (Reste {mois_restants} mois)")

# --- CONNEXION GOOGLE SHEET ---
# C'est ici que l'appli va chercher tes données sauvegardées
conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="Feuille 1", usecols=[0, 1, 2, 3], ttl=5)
# On s'assure que les données vides sont bien gérées
if data.empty:
    data = pd.DataFrame(columns=["Date", "Categorie", "Montant", "Note"])

# --- 1. PARAMÈTRES DU MOIS (CALCULATRICE) ---
with st.expander("📝 Configurer le mois (Salaire & Planning)", expanded=True):
    col_salaire, col_papa = st.columns(2)
    salaire = col_salaire.number_input("Salaire Reçu (€)", value=1200.0, step=50.0)
    epargne_papa = col_papa.number_input("Virement Papa (€)", value=800.0)

    st.write("---")
    c1, c2 = st.columns(2)
    jours_travail = c1.number_input("Jours Travail (Cantine)", value=12)
    jours_cours = c2.number_input("Jours Cours (Risque Tupp)", value=8)

    # Coûts fixes (Tu peux modifier les valeurs par défaut dans le code si tu veux)
    ABONNEMENTS = 30.0
    PRIX_CANTINE = 4.0
    PRIX_RESTO_COURS = 10.0
    PRIX_ESSENCE_JOUR = 5.0
    RISQUE_OUBLI = 0.20 # 20% de chance d'oublier le tupp

    # Calculs automatiques
    budget_cantine = jours_travail * PRIX_CANTINE
    budget_bouffe_cours = (jours_cours * RISQUE_OUBLI) * PRIX_RESTO_COURS
    budget_essence = (jours_travail + jours_cours) * PRIX_ESSENCE_JOUR
    
    total_charges = epargne_papa + ABONNEMENTS + budget_cantine + budget_essence + budget_bouffe_cours
    reste_theorique = salaire - total_charges

    st.info(f"Une fois tout payé (Papa, Essence, Cantine...), il devrait te rester : **{reste_theorique:.2f} €** pour les plaisirs/imprévus.")

# --- 2. AJOUTER UNE DÉPENSE (SAUVEGARDÉE) ---
st.write("---")
st.header("➕ Nouvelle Dépense")

with st.form(key="add_form"):
    c_date, c_cat, c_montant = st.columns([1, 1, 1])
    date_depense = c_date.date_input("Date", value=today)
    cat = c_cat.selectbox("Type", ["Courses", "Resto/Bar", "Shopping", "Essence (Extra)", "Autre"])
    montant = c_montant.number_input("Montant (€)", min_value=0.0, step=1.0)
    note = st.text_input("Note (ex: Mcdo avec potes)")
    
    submit_button = st.form_submit_button(label="Enregistrer la dépense")

    if submit_button and montant > 0:
        # Création de la nouvelle ligne
        new_row = pd.DataFrame([
            {"Date": date_depense.strftime("%Y-%m-%d"), "Categorie": cat, "Montant": montant, "Note": note}
        ])
        # Ajout à la feuille existante
        updated_df = pd.concat([data, new_row], ignore_index=True)
        # Sauvegarde dans Google Sheets
        conn.update(worksheet="Feuille 1", data=updated_df)
        st.success("Dépense sauvegardée dans le Cloud ! 🎉")
        st.rerun()

# --- 3. BILAN RÉEL ---
st.write("---")
st.header("📊 Bilan du Mois")

# Filtrer pour ne voir que les dépenses du mois en cours
data["Date"] = pd.to_datetime(data["Date"])
mask_mois = (data["Date"].dt.month == today.month) & (data["Date"].dt.year == today.year)
depenses_mois = data[mask_mois]

total_depense_plaisir = depenses_mois["Montant"].sum()
vrai_reste_final = reste_theorique - total_depense_plaisir

col_res1, col_res2 = st.columns(2)
col_res1.metric("Dépensé en plaisirs", f"{total_depense_plaisir:.2f} €")
col_res2.metric("Reste RÉEL sur le compte", f"{vrai_reste_final:.2f} €", delta=f"{vrai_reste_final:.2f} €")

if vrai_reste_final < 0:
    st.error("🚨 Tu es dans le rouge par rapport à tes prévisions !")

# Afficher l'historique récent
st.subheader("Dernières dépenses")
st.dataframe(depenses_mois.sort_values(by="Date", ascending=False), use_container_width=True)
