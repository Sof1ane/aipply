"""
ÉTAPE 2 : Génération automatique de CV (à exécuter à chaque offre)
Fichier : generer_cv.py

Lancez ce script, collez l'offre, et le CV est généré automatiquement !
"""

import requests
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
import re


class GenerateurCVAuto:
    def __init__(self, modele="mistral", url_ollama="http://localhost:11434"):
        self.modele = modele
        self.url_ollama = url_ollama
        self.profil = self.charger_profil()

    def charger_profil(self):
        """Charge le profil depuis le fichier local"""
        try:
            with open('profil_structure.json', 'r', encoding='utf-8') as f:
                profil = json.load(f)
                print(f"✅ Profil chargé : {profil['identite']['nom']}")
                return profil
        except FileNotFoundError:
            print("❌ Erreur : fichier 'profil_structure.json' introuvable")
            print("   Exécutez d'abord 'preparer_profil.py'")
            exit(1)

    def appeler_mistral(self, prompt):
        """Appelle Mistral via Ollama"""
        url = f"{self.url_ollama}/api/generate"
        payload = {
            "model": self.modele,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3}
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur: {e}")
            raise

    def extraire_titre_offre(self, offre):
        """Extrait le titre du poste depuis l'offre"""
        prompt = f"""Extrait le titre du poste de cette offre d'emploi. Retourne UNIQUEMENT le titre, rien d'autre.

Offre :
{offre[:1000]}

Titre du poste :"""

        reponse = self.appeler_mistral(prompt)
        titre = reponse.strip().replace('\n', ' ')

        # Nettoyer le titre pour en faire un nom de fichier
        titre = re.sub(r'[<>:"/\\|?*]', '', titre)
        titre = titre[:50]  # Limiter la longueur

        return titre if titre else None

    def adapter_profil(self, offre):
        """Adapte le profil pour l'offre"""
        prompt = f"""Tu es un expert en rédaction de CV. 

OFFRE D'EMPLOI :
{offre}

PROFIL COMPLET DU CANDIDAT :
{self.profil['profil_long']}

Rédige un paragraphe de profil de 4-5 lignes qui met en avant les points pertinents pour cette offre.
Utilise les mots-clés de l'offre. Sois détaillé et percutant.
Retourne UNIQUEMENT le paragraphe, sans introduction ni commentaire."""

        return self.appeler_mistral(prompt)

    def selectionner_experiences(self, offre):
        """Sélectionne et adapte les expériences pertinentes"""
        experiences_json = json.dumps(self.profil['experiences'], ensure_ascii=False, indent=2)

        prompt = f"""Tu es un expert en rédaction de CV.

OFFRE D'EMPLOI :
{offre}

EXPÉRIENCES DU CANDIDAT :
{experiences_json}

Sélectionne les 2-3 expériences les PLUS pertinentes et reformule les missions pour matcher l'offre.
Pour chaque expérience, garde 4-5 missions détaillées qui mettent en valeur les compétences demandées.

IMPORTANT : Utilise les VRAIES valeurs (vrais noms d'entreprises, vraies villes, vraies dates du JSON).

Retourne UNIQUEMENT un JSON valide :
[
  {{
    "entreprise": "Nom réel de l'entreprise",
    "lieu": "Ville réelle",
    "poste": "Titre réel du poste",
    "dates": "Dates réelles",
    "missions": ["mission détaillée 1", "mission détaillée 2", "mission détaillée 3", "mission détaillée 4"]
  }}
]"""

        reponse = self.appeler_mistral(prompt)

        try:
            debut = reponse.find('[')
            fin = reponse.rfind(']') + 1
            if debut != -1 and fin > debut:
                json_str = reponse[debut:fin]
                return json.loads(json_str)
            else:
                return json.loads(reponse)
        except json.JSONDecodeError:
            print("⚠️ Erreur parsing expériences, utilisation des 2 premières")
            return self.profil['experiences'][:2]

    def selectionner_competences(self, offre):
        """Sélectionne les compétences pertinentes"""
        competences_json = json.dumps(self.profil['competences'], ensure_ascii=False, indent=2)

        prompt = f"""Tu es un expert en rédaction de CV.

OFFRE D'EMPLOI :
{offre}

COMPÉTENCES DU CANDIDAT :
{competences_json}

Sélectionne les compétences pertinentes pour cette offre (8-10 par catégorie).
Priorise les compétences mentionnées dans l'offre.

Retourne UNIQUEMENT ce format exact :
<b>Techniques :</b> comp1, comp2, comp3, comp4, comp5, comp6, comp7, comp8<br/>
<b>Gestion &amp; Méthodes :</b> comp1, comp2, comp3, comp4, comp5, comp6"""

        return self.appeler_mistral(prompt)

    def generer_nom_fichier(self, titre_offre):
        """Génère le nom du fichier PDF"""
        if titre_offre:
            nom = f"CV_{titre_offre}"
        else:
            nom_candidat = self.profil['identite']['nom'].replace(' ', '_')
            date = datetime.now().strftime("%Y%m%d")
            nom = f"CV_{nom_candidat}_{date}"

        # Nettoyer le nom
        nom = re.sub(r'[<>:"/\\|?*]', '', nom)
        return f"{nom}.pdf"

    def generer_pdf(self, profil_adapte, experiences, competences, nom_fichier):
        """Génère le PDF final"""
        doc = SimpleDocTemplate(
            nom_fichier,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()

        style_titre = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=4,
            textColor='#1a1a1a',
            fontName='Helvetica-Bold'
        )

        style_sous_titre = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=11,
            spaceAfter=10,
            textColor='#444444'
        )

        style_section = ParagraphStyle(
            'CustomSection',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor='#2c3e50',
            fontName='Helvetica-Bold'
        )

        style_normal = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=3
        )

        style_experience = ParagraphStyle(
            'CustomExperience',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            spaceAfter=4
        )

        content = []

        # En-tête
        content.append(Paragraph(self.profil['identite']['nom'], style_titre))
        content.append(Paragraph(self.profil['identite']['titre'], style_sous_titre))
        content.append(Spacer(1, 8))

        # Profil
        content.append(Paragraph("<b>Profil</b>", style_section))
        content.append(Paragraph(profil_adapte, style_normal))
        content.append(Spacer(1, 10))

        # Expériences
        content.append(Paragraph("<b>Expériences professionnelles</b>", style_section))
        for exp in experiences:
            titre_exp = f"<b>{exp['entreprise']} – {exp['lieu']}</b> | {exp['poste']} ({exp['dates']})"
            content.append(Paragraph(titre_exp, style_experience))

            missions_text = "<br/>".join([f"• {m}" for m in exp['missions']])
            content.append(Paragraph(missions_text, style_normal))
            content.append(Spacer(1, 8))

        # Compétences
        content.append(Paragraph("<b>Compétences</b>", style_section))
        content.append(Paragraph(competences, style_normal))
        content.append(Spacer(1, 10))

        # Formation
        content.append(Paragraph("<b>Formation</b>", style_section))
        content.append(Paragraph(self.profil['formation'], style_normal))
        content.append(Spacer(1, 10))

        # Langues
        content.append(Paragraph("<b>Langues</b>", style_section))
        langues_text = " • ".join(self.profil['langues'])
        content.append(Paragraph(langues_text, style_normal))

        # Centres d'intérêt (si disponibles)
        if 'centres_interet' in self.profil and self.profil['centres_interet']:
            content.append(Spacer(1, 10))
            content.append(Paragraph("<b>Centres d'intérêt</b>", style_section))
            if isinstance(self.profil['centres_interet'], list):
                interets_text = ", ".join(self.profil['centres_interet'])
            else:
                interets_text = self.profil['centres_interet']
            content.append(Paragraph(interets_text, style_normal))

        # Génération
        doc.build(content)
        print(f"✅ CV généré : {nom_fichier}")

    def generer(self, offre_emploi):
        """Pipeline complet de génération"""
        print("\n🎯 Analyse de l'offre d'emploi...")

        # Extraire le titre pour le nom du fichier
        print("📝 Extraction du titre du poste...")
        titre_offre = self.extraire_titre_offre(offre_emploi)
        if titre_offre:
            print(f"   → Titre détecté : {titre_offre}")

        # Adapter chaque section
        print("🤖 Adaptation du profil...")
        profil_adapte = self.adapter_profil(offre_emploi)

        print("🤖 Sélection des expériences...")
        experiences = self.selectionner_experiences(offre_emploi)

        print("🤖 Sélection des compétences...")
        competences = self.selectionner_competences(offre_emploi)

        # Générer le nom du fichier
        nom_fichier = self.generer_nom_fichier(titre_offre)

        # Générer le PDF
        print("📄 Génération du PDF...")
        self.generer_pdf(profil_adapte, experiences, competences, nom_fichier)

        print(f"\n✨ TERMINÉ ! CV sauvegardé : {nom_fichier}")


if __name__ == "__main__":
    print("=" * 60)
    print("   GÉNÉRATEUR DE CV AUTOMATIQUE")
    print("=" * 60)
    print()

    # Charger le générateur
    generateur = GenerateurCVAuto(modele="mistral")

    # Demander l'offre d'emploi
    print("📋 Collez l'offre d'emploi ci-dessous, puis appuyez sur Entrée deux fois :")
    print("-" * 60)

    lignes = []
    while True:
        ligne = input()
        if ligne == "" and len(lignes) > 0 and lignes[-1] == "":
            break
        lignes.append(ligne)

    offre_emploi = "\n".join(lignes).strip()

    if not offre_emploi:
        print("❌ Aucune offre fournie. Abandon.")
        exit(1)

    # Générer le CV
    generateur.generer(offre_emploi)