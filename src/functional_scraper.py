import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime


class FunctionalScraper:
    """
    Scraper alternatif utilisant des sources accessibles.
    Utilise des APIs publiques et des sites moins protégés.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        })

    def scrape_jobs_api(self, query, location="", max_results=50):
        """
        Utilise l'API Adzuna (gratuite) pour récupérer des offres d'emploi.
        """
        jobs = []

        try:
            url = "https://api.adzuna.com/v1/api/jobs/fr/search/1"
            params = {
                "app_id": "test",
                "app_key": "test",
                "results_per_page": min(max_results, 50),
                "what": query,
                "where": location,
                "content-type": "application/json",
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for job in data.get("results", [])[:max_results]:
                    jobs.append({
                        "source": "Adzuna",
                        "title": job.get("title", "N/A"),
                        "company": job.get("company", {}).get("display_name", "N/A"),
                        "location": job.get("location", {}).get("display_name", "N/A"),
                        "description": job.get("description", "")[:500],
                        "url": job.get("redirect_url", ""),
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "created_at": job.get("created", ""),
                        "scraped_at": datetime.now().isoformat(),
                    })

        except Exception as e:
            print(f"Erreur Adzuna API: {e}")

        return jobs

    def scrape_from_html(self, query, location="", max_results=50):
        """
        Scrape des offres depuis des sites web accessibles.
        """
        jobs = []

        try:
            search_url = "https://www.hellowork.com/fr-fr/emploi/recherche.html"
            params = {
                "k": query,
                "l": location,
                "p": 1,
            }

            response = self.session.get(search_url, params=params, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                job_cards = soup.find_all("article", class_="card-job")

                for card in job_cards[:max_results]:
                    job = self._parse_hellowork(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Erreur HelloWork: {e}")

        return jobs

    def _parse_hellowork(self, card):
        """Parse une carte HelloWork."""
        try:
            title_elem = card.find("h2", class_="card-job-title")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            company_elem = card.find("p", class_="card-job-company")
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            location_elem = card.find("p", class_="card-job-location")
            location = location_elem.get_text(strip=True) if location_elem else "N/A"

            link_elem = card.find("a", href=True)
            url = f"https://www.hellowork.com{link_elem['href']}" if link_elem else ""

            return {
                "source": "HelloWork",
                "title": title,
                "company": company,
                "location": location,
                "description": "",
                "url": url,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def scrape_talent(self, query, location="", max_results=50):
        """
        Scrape depuis Talent.com (anciennement Monster).
        """
        jobs = []

        try:
            search_url = "https://www.talent.com/jobs"
            params = {
                "k": query,
                "l": location,
            }

            response = self.session.get(search_url, params=params, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                job_cards = soup.find_all("div", class_="card__body") or soup.find_all("li", class_="job-card")

                for card in job_cards[:max_results]:
                    job = self._parse_talent(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Erreur Talent.com: {e}")

        return jobs

    def _parse_talent(self, card):
        """Parse une carte Talent.com."""
        try:
            title_elem = card.find("h2") or card.find("a", class_="job-title")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            company_elem = card.find("span", class_="company") or card.find("p", class_="company-name")
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            location_elem = card.find("span", class_="location") or card.find("li", class_="location")
            location = location_elem.get_text(strip=True) if location_elem else "N/A"

            link_elem = card.find("a", href=True)
            url = link_elem["href"] if link_elem else ""
            if url and not url.startswith("http"):
                url = f"https://www.talent.com{url}"

            return {
                "source": "Talent.com",
                "title": title,
                "company": company,
                "location": location,
                "description": "",
                "url": url,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception:
            return None

    def scrape_all_sources(self, query, location="", max_results=50):
        """
        Scrape toutes les sources disponibles et combine les résultats.
        """
        all_jobs = []
        per_source = max_results // 3

        print("  -> Tentative avec Talent.com...")
        talent_jobs = self.scrape_talent(query, location, per_source)
        all_jobs.extend(talent_jobs)
        print(f"     {len(talent_jobs)} offres trouvées")

        time.sleep(random.uniform(1, 2))

        print("  -> Tentative avec HelloWork...")
        hellowork_jobs = self.scrape_from_html(query, location, per_source)
        all_jobs.extend(hellowork_jobs)
        print(f"     {len(hellowork_jobs)} offres trouvées")

        time.sleep(random.uniform(1, 2))

        print("  -> Tentative avec Adzuna API...")
        adzuna_jobs = self.scrape_jobs_api(query, location, per_source)
        all_jobs.extend(adzuna_jobs)
        print(f"     {len(adzuna_jobs)} offres trouvées")

        return all_jobs[:max_results]
