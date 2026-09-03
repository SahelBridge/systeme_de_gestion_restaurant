# 🍽️ Système de Gestion de Restaurant (Smart Restaurant System)

Système complet de prise de commande sur tablette client et gestion en temps réel en cuisine (KDS), intégrant traitement de données, logique métier, base de données MongoDB et interfaces Streamlit.

---

## 🏗️ Architecture du Projet

```plaintext
systeme_de_gestion_restaurant/
│
├── data/
│   └── menu.json                 # Catalogue des plats, ingrédients, tags, prix et disponibilités
│
├── api_backend.py                # Routage, calcul des totaux et logique métier (Backend API)
├── database.py                   # Connexion & requêtes MongoDB (Backend DB)
├── app_client.py                 # Interface utilisateur Tablette Client (dev-client)
├── app_cuisine.py                # Interface utilisateur Écran Cuisine KDS (dev-cuisine)
│
├── requirements.txt              # Dépendances Python
└── README.md                     # Documentation d'installation et d'exécution
```

---

## 📱 Module Frontend - Tablette Client (`dev-client`)

Le module **`app_client.py`** fournit une interface intuitive et optimisée pour un usage tactile sur tablette :

- 📜 **Catalogue Interactif** : Consultation des entrées, plats, desserts et boissons avec photos/descriptions, recherche textuelle et filtres par régimes (Halal, Végétarien, Sans gluten, Spécialités).
- ✨ **Fonctionnalité 1 : Appel Serveur Rapide** : Boutons d'accès direct pour appeler le serveur (*Demander de l'eau*, *Demander du pain*, *Demander l'addition*, ou demande sur-mesure) rattachés au numéro de table.
- ✨ **Fonctionnalité 2 : Personnalisation des Plats** : Choix de la cuisson (Bleu, Saignant, À point, Bien cuit), gestion des allergies/exclusions (*Sans sel*, *Allergie arachide*, *Sans piment*, *Sans oignon*, *Sans gluten*) et instructions pour le chef.
- 🛒 **Gestion du Panier en Temps Réel** : Ajout/suppression, incrémentation, calcul immédiat du total et transmission sécurisée vers le Backend et la Base de Données.
- ⭐ **Avis & Programme de Fidélité** : Notation de l'expérience en fin de repas (1 à 5 étoiles) et enregistrement du numéro de téléphone pour créditer les points de fidélité.

---

## 🚀 Installation & Exécution

### 1. Cloner le dépôt et se positionner sur la branche `dev-client`
```bash
git clone git@github.com:SahelBridge/systeme_de_gestion_restaurant.git
cd systeme_de_gestion_restaurant
git checkout dev-client
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Lancer l'application Tablette Client
```bash
streamlit run app_client.py
```
L'interface s'ouvre automatiquement dans votre navigateur à l'adresse `http://localhost:8501`.

---

## 👥 Répartition des Rôles de l'Équipe

| Rôle | Branche Git | Fichier Cible | Responsabilité |
| :--- | :--- | :--- | :--- |
| **Frontend Client** | `dev-client` | `app_client.py` | Interface Tablette Client, Appel Serveur, Personnalisation |
| **Frontend Cuisine** | `dev-cuisine` | `app_cuisine.py` | Écran KDS Cuisine, Gestion urgence & rupture stock |
| **Backend API** | `dev_API` | `api_backend.py` | Logique métier, calcul de délais, filtres régimes |
| **Backend DB / Data** | `dev-db` | `database.py` & `data/` | Connexion MongoDB, Top ventes & Programme Fidélité |

---

## 🔄 Workflow Git & Pull Request

1. Travailler sur sa branche dédiée : `git checkout dev-client`
2. Valider les modifications : `git commit -m "feat(client): ..."`
3. Pousser sur GitHub : `git push origin dev-client`
4. Ouvrir une **Pull Request** vers `main` et solliciter la validation des 3 équipiers selon la règle des 3 approbations.
