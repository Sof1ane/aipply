"""
ÉTAPE 1 : Préparation du profil (à exécuter UNE SEULE FOIS)
Fichier : preparer_profil.py

Ce script analyse votre PDF de compétences et stocke tout en local
"""

import requests
import json
import PyPDF2
from datetime import datetime


class PreparateurProfil:
    def __init__(self, modele="mistral", url_ollama="http://localhost:11434"):
        self.modele = modele
        self.url_ollama = url_ollama

    def extraire_pdf(self, chemin_pdf):
        """Extrait le texte du PDF"""
        texte = ""
        with open(chemin_pdf, 'rb') as fichier:
            lecteur = PyPDF2.PdfReader(fichier)
            for page in lecteur.pages:
                texte += page.extract_text()
        return texte

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
            print("Vérifiez qu'Ollama est lancé : ollama serve")
            raise

    def structurer_profil(self, texte_brut):
        """Utilise Mistral pour structurer le profil"""
        prompt = f"""Tu es un expert RH. Analyse ce CV complet et structure-le en JSON.

{texte_brut}

Retourne UNIQUEMENT un JSON valide avec cette structure exacte :
{{
  "identite": {{
    "nom": "Nom Prénom complet",
    "titre": "Titre professionnel exact"
  }},
  "profil_long": "Description complète du profil en 5-6 lignes avec tous les détails",
  "experiences": [
    {{
      "entreprise": "Nom exact de l'entreprise",
      "lieu": "Ville exacte",
      "poste": "Titre exact du poste",
      "dates": "AAAA-AAAA",
      "missions": ["mission détaillée 1", "mission détaillée 2", "mission détaillée 3", "mission 4", "mission 5"]
    }}
  ],
  "competences": {{
    "techniques": ["toutes les compétences techniques"],
    "methodologiques": ["toutes les compétences méthodologiques"]
  }},
  "formation": "Formation principale complète avec école, diplôme et dates",
  "langues": ["Français (niveau)", "Anglais (niveau)"],
  "centres_interet": ["intérêt 1", "intérêt 2", "intérêt 3"]
}}

IMPORTANT : 
- Utilise les VRAIES valeurs du CV (noms d'entreprises réels, villes réelles, dates réelles)
- Liste TOUTES les missions de chaque expérience (jusqu'à 5 missions par expérience)
- Retourne SEULEMENT le JSON, rien d'autre."""

        print("🤖 Analyse du profil par Mistral...")
        reponse = self.appeler_mistral(prompt)

        # Extraire le JSON de la réponse
        try:
            # Trouver le JSON dans la réponse
            debut = reponse.find('{')
            fin = reponse.rfind('}') + 1
            if debut != -1 and fin > debut:
                json_str = reponse[debut:fin]
                return json.loads(json_str)
            else:
                print("⚠️ JSON non trouvé, tentative de parsing...")
                return json.loads(reponse)
        except json.JSONDecodeError:
            print("❌ Erreur de parsing JSON")
            print("Réponse brute:", reponse[:500])
            raise

    def preparer(self, chemin_pdf_competences):
        """Prépare et sauvegarde le profil"""
        print("📄 Extraction du PDF...")
        texte = self.extraire_pdf(chemin_pdf_competences)

        print("🧠 Structuration du profil...")
        profil_structure = self.structurer_profil(texte)

        # Sauvegarder en local
        with open('profil_structure.json', 'w', encoding='utf-8') as f:
            json.dump(profil_structure, f, ensure_ascii=False, indent=2)

        print("✅ Profil préparé et sauvegardé dans 'profil_structure.json'")
        print(f"   → Nom: {profil_structure['identite']['nom']}")
        print(f"   → {len(profil_structure['experiences'])} expériences")
        print(f"   → {len(profil_structure['competences']['techniques'])} compétences techniques")


if __name__ == "__main__":
    preparateur = PreparateurProfil(modele="mistral")

    # Chemin vers votre PDF de compétences complètes
    preparateur.preparer("mes_competences_completes.pdf")