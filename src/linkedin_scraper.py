import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime


class LinkedInScraper:
    """
    Scraper LinkedIn (limité - LinkedIn bloque le scraping agressif).
    
    IMPORTANT: Ce scraper utilise des endpoints publiques.
    Pour un usage professionnel, utilisez l'API LinkedIn officielle.
    """

    SEARCH_URL = "https://www.linkedin.com/search/results/people/"
    COMPANY_URL = "https://www.linkedin.com/company/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def search_people(self, keywords, location="", max_results=25):
        """
        Recherche de personnes sur LinkedIn.
        
        NOTE: LinkedIn nécessite une authentification pour la plupart des recherches.
        Cette fonction tente d'accéder aux résultats publics.
        """
        people = []

        try:
            params = {
                "keywords": keywords,
                "geoUrn": "",
                "origin": "FACETED_SEARCH",
            }

            response = self.session.get(self.SEARCH_URL, params=params, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                cards = soup.find_all("div", class_="entity-result__item")

                for card in cards[:max_results]:
                    person = self._parse_person_card(card)
                    if person:
                        people.append(person)

        except requests.RequestException as e:
            print(f"Erreur scraping LinkedIn: {e}")

        return people

    def _parse_person_card(self, card):
        """Parse une carte de personne."""
        try:
            name_elem = card.find("span", class_="entity-result__title-text")
            name = name_elem.get_text(strip=True) if name_elem else "N/A"

            headline_elem = card.find("div", class_="entity-result__primary-subtitle")
            headline = headline_elem.get_text(strip=True) if headline_elem else "N/A"

            location_elem = card.find("div", class_="entity-result__secondary-subtitle")
            location = location_elem.get_text(strip=True) if location_elem else "N/A"

            link_elem = card.find("a", class_="app-aware-link")
            profile_url = link_elem["href"] if link_elem else ""

            return {
                "source": "LinkedIn",
                "name": name,
                "headline": headline,
                "location": location,
                "profile_url": profile_url,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Erreur parsing personne: {e}")
            return None

    def scrape_company_employees(self, company_slug, max_results=25):
        """Scrape les employés d'une entreprise (basique)."""
        employees = []

        try:
            url = f"{self.COMPANY_URL}{company_slug}/people/"
            response = self.session.get(url, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                cards = soup.find_all("li", class_="org-people-profile-card")

                for card in cards[:max_results]:
                    emp = self._parse_employee_card(card)
                    if emp:
                        employees.append(emp)

        except requests.RequestException as e:
            print(f"Erreur scraping entreprise: {e}")

        return employees

    def _parse_employee_card(self, card):
        """Parse une carte d'employé."""
        try:
            name_elem = card.find("span", class_="artdeco-entity-lockup__title")
            name = name_elem.get_text(strip=True) if name_elem else "N/A"

            title_elem = card.find("div", class_="artdeco-entity-lockup__subtitle")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            link_elem = card.find("a")
            profile_url = link_elem["href"] if link_elem else ""

            return {
                "source": "LinkedIn",
                "name": name,
                "title": title,
                "profile_url": profile_url,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return None
