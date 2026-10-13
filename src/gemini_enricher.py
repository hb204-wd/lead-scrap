from google import genai
import json
import time


class GeminiEnricher:
    """Enrichit les leads avec des analyses IA via Google Gemini."""

    MODEL = "gemini-3.5-flash-lite"

    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)

    def enrich_lead(self, lead_data):
        """Enrichit un lead avec des informations analytiques."""
        prompt = self._build_enrichment_prompt(lead_data)

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=prompt
            )
            result = response.text

            json_match = result[result.find("{"):result.rfind("}") + 1]
            enrichment = json.loads(json_match)
            return enrichment

        except json.JSONDecodeError:
            return {"raw_response": result}
        except Exception as e:
            print(f"Erreur enrichissement Gemini: {e}")
            return {}

    def _build_enrichment_prompt(self, lead_data):
        """Construit le prompt d'enrichissement."""
        return f"""Analyse ce lead et fournis un enrichissement en JSON.

Données du lead:
{json.dumps(lead_data, indent=2, ensure_ascii=False)}

Réponds UNIQUEMENT avec un JSON contenant ces champs:
{{
    "score_qualification": "hot/warm/cold",
    "potentiel_estime": "high/medium/low",
    "secteur_activite": "secteur identifié",
    "taille_entreprise": "startup/pme/etp",
    "decision_maker": true/false,
    "approche_recommandee": "conseil d'approche commercial",
    "points_de_contact": ["sujets pertinents"],
    "risques": ["risques potentiels"],
    "opportunites": ["opportunités identifiées"]
}}"""

    def enrich_batch(self, leads):
        """Enrichit un lot de leads."""
        enriched = []

        for i, lead in enumerate(leads):
            print(f"Enrichissement {i + 1}/{len(leads)}...")
            enrichment = self.enrich_lead(lead)
            enriched_lead = {**lead, "ai_enrichment": enrichment}
            enriched.append(enriched_lead)

            if i < len(leads) - 1:
                time.sleep(0.5)

        return enriched

    def analyze_market(self, leads):
        """Analyse globale d'un marché cible."""
        leads_summary = json.dumps(leads[:10], indent=2, ensure_ascii=False)

        try:
            response = self.client.models.generate_content(
                model=self.MODEL,
                contents=f"""Analyse ces {len(leads)} leads et fournis:
1. Les tendances du marché
2. Les segments prioritaires
3. Les recommandations d'action

Leads:
{leads_summary}"""
            )

            return response.text

        except Exception as e:
            print(f"Erreur analyse marché: {e}")
            return None
