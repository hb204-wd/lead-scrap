from openai import OpenAI
import json
import time


class AIEnricher:
    """Enrichit les leads scrapés avec des analyses IA via OpenAI."""

    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def enrich_lead(self, lead_data):
        """Enrichit un lead avec des informations analytiques."""
        prompt = self._build_enrichment_prompt(lead_data)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un expert en growth engineering et en génération de leads. "
                            "Analyse les données fournies et enrichis-les avec des informations "
                            "actionnables pour une équipe commerciale."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            result = response.choices[0].message.content
            enrichment = json.loads(result)
            return enrichment

        except json.JSONDecodeError:
            return self._parse_text_response(result)
        except Exception as e:
            print(f"Erreur enrichissement IA: {e}")
            return {}

    def _build_enrichment_prompt(self, lead_data):
        """Construit le prompt d'enrichissement."""
        return f"""Analyse ce lead et fournis un enrichissement en JSON avec les champs suivants:

Données du lead:
{json.dumps(lead_data, indent=2, ensure_ascii=False)}

Réponds UNIQUEMENT avec un JSON contenant:
{{
    "score_qualification": "hot/warm/cold",
    "potentiel_estime": "high/medium/low",
    "secteur_activite": "secteur identifié",
    "taille_entreprise": "startup/pme/etp",
    "decision_maker": true/false,
    "approche_recommandee": "conseil d'approche commercial",
    "points_de_contact": ["sujets pertinents à aborder"],
    "risques": ["risques potentiels identifiés"],
    "opportunites": ["opportunités business identifiées"]
}}"""

    def _parse_text_response(self, text):
        """Parse une réponse textuelle en dict."""
        return {"raw_response": text}

    def enrich_batch(self, leads):
        """Enrichit un lot de leads avec gestion du rate limiting."""
        enriched = []

        for i, lead in enumerate(leads):
            print(f"Enrichissement {i + 1}/{len(leads)}...")
            enrichment = self.enrich_lead(lead)
            enriched_lead = {**lead, "ai_enrichment": enrichment}
            enriched.append(enriched_lead)

            if i < len(leads) - 1:
                time.sleep(1)

        return enriched

    def analyze_market(self, leads):
        """Analyse globale d'un marché cible à partir des leads."""
        leads_summary = json.dumps(leads[:10], indent=2, ensure_ascii=False)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un analyste marché B2B. Fournis une synthèse stratégique.",
                    },
                    {
                        "role": "user",
                        "content": f"""Analyse ces {len(leads)} leads et fournis:
1. Les tendances du marché
2. Les segments prioritaires
3. Les recommandations d'action

Leads:
{leads_summary}""",
                    },
                ],
                temperature=0.4,
                max_tokens=1000,
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Erreur analyse marché: {e}")
            return None
