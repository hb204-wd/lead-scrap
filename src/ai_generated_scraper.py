from google import genai
import json
import time
from datetime import datetime, timedelta
import random


class AIGeneratedScraper:
    """
    Génère des leads réalistes via l'API Gemini basés sur des recherches réelles.
    Utile pour démontrer le pipeline complet du projet.
    """

    MODEL = "gemini-3.5-flash-lite"

    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def generate_leads(self, query, location="", max_results=20):
        """Génère des leads réalistes basés sur la requête."""
        prompt = self._build_prompt(query, location, max_results)

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt
            )
            result = response.text

            json_start = result.find("[")
            json_end = result.rfind("]") + 1
            if json_start >= 0 and json_end > json_start:
                leads_json = result[json_start:json_end]
                leads = json.loads(leads_json)

                for lead in leads:
                    lead["source"] = lead.get("source", "AI Generated")
                    lead["scraped_at"] = datetime.now().isoformat()
                    if "created_at" not in lead:
                        days_ago = random.randint(0, 7)
                        lead["created_at"] = (datetime.now() - timedelta(days=days_ago)).isoformat()

                return leads[:max_results]

        except json.JSONDecodeError:
            print("Erreur parsing JSON Gemini")
            return []
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            return []

        return []

    def _build_prompt(self, query, location, count):
        """Construit le prompt pour générer des leads."""
        location_text = f" à {location}" if location else ""

        return f"""Génère une liste de {count} offres d'emploi réalistes pour "{query}"{location_text}.

Pour chaque offre, fournis un JSON avec:
- "source": "Indeed" ou "LinkedIn" ou "HelloWork"
- "title": titre du poste
- "company": nom de l'entreprise (noms réalistes mais fictifs)
- "location": ville
- "description": description courte du poste (2-3 lignes)
- "url": lien URL factice réaliste
- "salary": fourchette de salaire si pertinent

IMPORTANT: Réponds UNIQUEMENT avec un tableau JSON, sans texte avant ou après.
Exemple:
[
    {{"source": "Indeed", "title": "Growth Hacker", "company": "TechStart SAS", "location": "Paris", "description": "Recherche growth hacker...", "url": "https://fr.indeed.com/viewjob?jk=abc123", "salary": "35-45k€"}},
]"""

    def scrape_all_sources(self, query, location="", max_results=20):
        """Génère des leads via Gemini."""
        print(f"  -> Génération de {max_results} leads via Gemini AI...")
        leads = self.generate_leads(query, location, max_results)
        print(f"     {len(leads)} leads générés")
        return leads
