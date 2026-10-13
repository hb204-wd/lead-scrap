import requests
from bs4 import BeautifulSoup
import time
import random
import json
from datetime import datetime


class IndeedScraper:
    """Scraper pour extraire les offres d'emploi depuis Indeed."""

    BASE_URL = "https://fr.indeed.com/jobs"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def scrape_jobs(self, query, location="", max_results=50):
        """Scrape les offres Indeed pour une requête donnée."""
        jobs = []
        start = 0

        while len(jobs) < max_results:
            params = {
                "q": query,
                "l": location,
                "start": start,
                "sort": "date",
            }

            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

                job_cards = soup.find_all("div", class_="job_seen_beacon")

                if not job_cards:
                    break

                for card in job_cards:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

                start += 10
                time.sleep(random.uniform(2, 5))

            except requests.RequestException as e:
                print(f"Erreur lors du scraping: {e}")
                break

        return jobs[:max_results]

    def _parse_job_card(self, card):
        """Parse une carte d'offre individuelle."""
        try:
            title_elem = card.find("h2", class_="jobTitle")
            title = title_elem.get_text(strip=True) if title_elem else "N/A"

            company_elem = card.find("span", class_="companyName")
            company = company_elem.get_text(strip=True) if company_elem else "N/A"

            location_elem = card.find("div", class_="companyLocation")
            location = location_elem.get_text(strip=True) if location_elem else "N/A"

            summary_elem = card.find("div", class_="job-snippet")
            summary = summary_elem.get_text(strip=True) if summary_elem else ""

            link_elem = card.find("a", id=True)
            link = f"https://fr.indeed.com{link_elem['href']}" if link_elem else ""

            return {
                "source": "Indeed",
                "title": title,
                "company": company,
                "location": location,
                "description": summary,
                "url": link,
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Erreur parsing carte: {e}")
            return None

    def scrape_company(self, company_name, max_results=20):
        """Scrape toutes les offres d'une entreprise spécifique."""
        return self.scrape_jobs(f'"{company_name}"', max_results=max_results)
