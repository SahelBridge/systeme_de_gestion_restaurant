#!/usr/bin/env python3
"""
=============================================================================
Campagne d'Emailing B2B Automatisée - SmartResto Mali
Auteur: Ibrahim Tomota
=============================================================================
Ce script permet d'envoyer des emails personnalisés aux restaurants du Mali :
- Mode Simulation (--dry-run) : affiche et génère les aperçus sans envoyer
- Mode Test (--test-email ton_email@gmail.com) : envoie 1 email test sur ta boîte
- Mode Envoi Réel (--send) : envoie les emails via SMTP avec temporisation anti-spam
=============================================================================
"""

import os
import sys
import json
import time
import smtplib
import argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# Chargement configuration depuis variables d'environnement ou fichier .env
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "itomota11@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # Mot de passe d'application Google (16 caractères)
SENDER_NAME = os.getenv("SENDER_NAME", "Ibrahim Tomota | SmartResto Mali")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "prospects_restaurants_mali.json"


def load_prospects():
    if not DATA_FILE.exists():
        print(f"❌ Fichier introuvable : {DATA_FILE}")
        sys.exit(1)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def build_email_content(p):
    """Génère le sujet, le texte brut et le template HTML responsive pour chaque restaurant."""
    nom = p["nom"]
    quartier = p.get("quartier", "Bamako")
    type_resto = p.get("type", "Restaurant")
    offre = p.get("offre", "SaaS Mensuel ou Licence à vie")
    argument = p.get("argument", "Optimisation du service et anti-coulage des stocks")

    subject = f"🍽️ Modernisation & Démo SmartResto pour {nom} (Tablettes & Cuisine KDS)"

    # Version Texte Brut
    text_body = f"""Bonjour la direction de {nom},

Je me permets de vous contacter pour vous présenter SmartResto, notre solution numérique développée spécialement pour les restaurants à Bamako ({quartier}).

Pourquoi SmartResto est pensé pour {nom} :
• {argument}
• Prise de commande sur tablettes tactiles élégantes avec photos HD de vos spécialités
• Écran Cuisine KDS connecté en direct : élimine les pertes de tickets et accélère le service
• 100% Fonctionnel en Wi-Fi local : aucune coupure même si la connexion Orange ou Moov ralentit
• Zéro coulage : contrôle rigoureux des boissons au bar et inventaire des viandes

Deux formules flexibles selon votre stratégie :
1. Abonnement SaaS mensuel tout compris (démarrage immédiat sans investissement lourd)
2. Licence Perpétuelle à vie (achat unique sans redevance mensuelle obligatoire)

Seriez-vous disponible cette semaine pour une brève démonstration de 15 minutes sur tablette dans votre établissement ?

Bien cordialement,

Ibrahim Tomota
Fondateur SmartResto Mali
Tél / WhatsApp : +223 93 23 91 87
Email : {SMTP_USER}
Bamako, Mali
"""

    # Version HTML Stylisée & Responsive
    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
    .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
    .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 28px 24px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
    .header p {{ margin: 6px 0 0 0; opacity: 0.9; font-size: 14px; }}
    .content {{ padding: 24px; line-height: 1.6; font-size: 15px; }}
    .benefit-box {{ background: #f1f5f9; border-left: 4px solid #2563eb; padding: 14px 16px; border-radius: 6px; margin: 18px 0; }}
    .benefit-item {{ margin-bottom: 8px; }}
    .cta-button {{ display: inline-block; background: #2563eb; color: #ffffff !important; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 15px; }}
    .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 24px; font-size: 13px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="card">
    <div class="header">
        <h1>🍽️ SmartResto Mali</h1>
        <p>Solution Tactile & KDS Cuisine pour Restaurants d'Exception</p>
    </div>
    <div class="content">
        <p>Bonjour la direction de <strong>{nom}</strong>,</p>
        <p>Je me permets de vous contacter car votre établissement fait partie des références culinaires à <strong>{quartier}</strong>, et notre solution a été spécialement pensée pour fluidifier le service des tables comme la vôtre.</p>
        
        <div class="benefit-box">
            <div class="benefit-item">⚡ <strong>Commande Tablette Intuitive :</strong> Vos clients parcourent votre carte interactive, personnalisent leurs plats (cuisson, allergies, suppléments) et commandent en 1 clic.</div>
            <div class="benefit-item">🧑‍🍳 <strong>Écran Cuisine KDS :</strong> Finis les bons papier perdus ou tachés ! Vos cuisiniers reçoivent les tickets ordonnancés avec minutage dynamique.</div>
            <div class="benefit-item">📶 <strong>100% Résistant aux pannes Internet :</strong> Le système tourne en réseau local Wi-Fi autonome, sans dépendre de la fibre ou d'Orange/Moov.</div>
            <div class="benefit-item">🛡️ <strong>Anti-coulage & Contrôle des Stocks :</strong> Suivi précis des boissons servies et clôture de caisse quotidienne infalsifiable.</div>
        </div>

        <p><strong>Nos Formules au choix :</strong></p>
        <ul>
            <li><strong>SaaS Mensuel :</strong> Abonnement accessible sans gros investissement au démarrage.</li>
            <li><strong>Licence Perpétuelle :</strong> Paiement unique « une fois pour toutes », vous êtes propriétaire à vie de votre logiciel.</li>
        </ul>

        <p style="text-align: center;">
            <a href="https://wa.me/22393239187?text=Bonjour%20Ibrahim%2C%20je%20souhaite%20une%20d%C3%A9mo%20SmartResto%20pour%20{nom.replace(' ', '%20')}" class="cta-button">📲 Réserver une démo de 10 min sur WhatsApp</a>
        </p>
    </div>
    <div class="footer">
        <strong>Ibrahim Tomota</strong> — Concepteur SmartResto Mali<br>
        Bamako, Mali • Tél / WhatsApp : +223 93 23 91 87 • Email : {SMTP_USER}
    </div>
</div>
</body>
</html>
"""
    return subject, text_body, html_body


def send_single_email(server, recipient, subject, text_body, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = recipient

    part1 = MIMEText(text_body, "plain", "utf-8")
    part2 = MIMEText(html_body, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)

    server.sendmail(SENDER_EMAIL, recipient, msg.as_string())


def main():
    parser = argparse.ArgumentParser(description="Campagne Emailing Commerciale B2B SmartResto Mali")
    parser.add_argument("--dry-run", action="store_true", help="Génère les aperçus sans envoyer d'emails")
    parser.add_argument("--test-email", type=str, help="Envoie un email de test à l'adresse spécifiée")
    parser.add_argument("--send", action="store_true", help="Lance l'envoi réel de la campagne")
    parser.add_argument("--yes", action="store_true", help="Confirme automatiquement sans demander")
    parser.add_argument("--limit", type=int, default=None, help="Limite le nombre d'emails à envoyer")
    parser.add_argument("--quartier", type=str, default=None, help="Filtre par quartier (ex: Hippodrome, ACI 2000)")

    args = parser.parse_args()
    prospects = load_prospects()

    # Filtrer ceux qui ont un email valide
    valid_prospects = [
        p for p in prospects 
        if p.get("email") and "@" in p["email"] and not p["email"].endswith(".mali")
    ]

    if args.quartier:
        valid_prospects = [p for p in valid_prospects if args.quartier.lower() in p.get("quartier", "").lower()]

    if args.limit:
        valid_prospects = valid_prospects[:args.limit]

    print(f"================================================================")
    print(f"🚀 CAMPAGNE EMAILING SMARTRESTO MALI")
    print(f"📋 Prospects ciblés avec email : {len(valid_prospects)} sur {len(prospects)}")
    print(f"================================================================")

    # 1. Mode TEST EMAIL
    if args.test_email:
        print(f"🧪 Envoi d'un email de test vers : {args.test_email}")
        if not SMTP_PASSWORD:
            print("❌ Erreur : SMTP_PASSWORD n'est pas configuré.")
            return

        sample_p = valid_prospects[0] if valid_prospects else prospects[0]
        subj, txt, html = build_email_content(sample_p)

        try:
            print(f"🔌 Connexion à {SMTP_HOST}:{SMTP_PORT}...")
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            send_single_email(server, args.test_email, f"[TEST] {subj}", txt, html)
            server.quit()
            print("✅ Email de test envoyé avec succès ! Vérifiez votre boîte de réception.")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi test : {e}")
        return

    # 2. Mode SIMULATION (DRY-RUN)
    if args.dry_run or not args.send:
        preview_dir = BASE_DIR / "previews_emailing"
        preview_dir.mkdir(exist_ok=True)
        print(f"🔍 Mode Simulation actif (--dry-run). Aucun email ne sera expédié.")
        print(f"📁 Sauvegarde des 5 premiers aperçus HTML dans : {preview_dir}")

        for idx, p in enumerate(valid_prospects[:5], 1):
            subj, txt, html = build_email_content(p)
            file_path = preview_dir / f"apercu_{idx}_{p['nom'].replace(' ', '_')}.html"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  [{idx}] {p['nom']} ({p['email']}) -> Sujet : {subj}")

        print(f"\n💡 Pour lancer l'envoi réel :")
        print(f"   1. export SMTP_PASSWORD='votre_mot_de_passe_google'")
        print(f"   2. python3 {sys.argv[0]} --send --yes")
        return

    # 3. Mode ENVOI RÉEL (--send)
    if args.send:
        if not SMTP_PASSWORD:
            print("❌ Erreur : SMTP_PASSWORD est obligatoire pour l'envoi réel.")
            print("Configurez la variable : export SMTP_PASSWORD='...' puis relancez.")
            sys.exit(1)

        if not args.yes:
            confirm = input(f"⚠️ Êtes-vous sûr de vouloir envoyer {len(valid_prospects)} emails maintenant ? (o/N) : ")
            if confirm.lower() not in ["o", "oui", "y"]:
                print("Annulation de l'envoi.")
                return

        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("✅ Connecté au serveur SMTP avec succès.")

            success_count = 0
            for idx, p in enumerate(valid_prospects, 1):
                subj, txt, html = build_email_content(p)
                dest = p["email"]
                print(f"[{idx}/{len(valid_prospects)}] Envoi à {p['nom']} <{dest}>...", end="", flush=True)
                try:
                    send_single_email(server, dest, subj, txt, html)
                    print(" ✅ Envoyé !")
                    success_count += 1
                except Exception as ex:
                    print(f" ❌ Échec ({ex})")

                # Délai de courtoisie anti-spam (4 secondes entre chaque email)
                if idx < len(valid_prospects):
                    time.sleep(4)

            server.quit()
            print(f"\n🎉 Campagne terminée : {success_count}/{len(valid_prospects)} emails envoyés avec succès !")
        except Exception as e:
            print(f"❌ Erreur SMTP globale : {e}")


if __name__ == "__main__":
    main()
