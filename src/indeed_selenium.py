from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
from datetime import datetime


class IndeedSeleniumScraper:
    """Scraper Indeed utilisant Selenium pour contourner la protection anti-bot."""

    BASE_URL = "https://fr.indeed.com/jobs"

    def __init__(self):
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.driver = None

    def _init_driver(self):
        """Initialise le navigateur Selenium."""
        if self.driver is None:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def scrape_jobs(self, query, location="", max_results=50):
        """Scrape les offres Indeed avec Selenium."""
        self._init_driver()
        jobs = []
        start = 0

        while len(jobs) < max_results:
            params = f"q={query.replace(' ', '+')}"
            if location:
                params += f"&l={location.replace(' ', '+')}"
            params += f"&start={start}"

            url = f"{self.BASE_URL}?{params}"

            try:
                self.driver.get(url)
                time.sleep(random.uniform(3, 6))

                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon")

                if not job_cards:
                    break

                for card in job_cards:
                    job = self._parse_job_card(card)
                    if job:
                        jobs.append(job)

                start += 10
                time.sleep(random.uniform(2, 5))

            except Exception as e:
                print(f"Erreur Selenium: {e}")
                break

        return jobs[:max_results]

    def _parse_job_card(self, card):
        """Parse une carte d'offre."""
        try:
            title = card.find_element(By.CSS_SELECTOR, "h2.jobTitle span").text
            company = card.find_element(By.CSS_SELECTOR, "span.companyName").text
            location = card.find_element(By.CSS_SELECTOR, "div.companyLocation").text

            try:
                summary = card.find_element(By.CSS_SELECTOR, "div.job-snippet").text
            except NoSuchElementException:
                summary = ""

            try:
                link = card.find_element(By.CSS_SELECTOR, "a[id]").get_attribute("href")
            except NoSuchElementException:
                link = ""

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
            return None

    def close(self):
        """Ferme le navigateur."""
        if self.driver:
            self.driver.quit()
            self.driver = None


class GoogleJobsScraper:
    """Scraper alternatif utilisant Google Jobs (plus accessible)."""

    BASE_URL = "https://www.google.com/search"

    def __init__(self):
        self.session = None

    def scrape_jobs(self, query, location="", max_results=50):
        """Scrape les offres via Google Jobs."""
        import requests
        from bs4 import BeautifulSoup

        jobs = []

        search_query = f"emploi {query}"
        if location:
            search_query += f" {location}"

        params = {
            "q": search_query,
            "ibp": "htivrtjcs",  # Google Jobs
            "hl": "fr",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }

        try:
            response = requests.get(self.BASE_URL, params=params, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")

                job_cards = soup.find_all("div", class_="iFjolb")

                for card in job_cards[:max_results]:
                    job = self._parse_google_job(card)
                    if job:
                        jobs.append(job)

        except Exception as e:
            print(f"Erreur Google Jobs: {e}")

        return jobs

    def _parse_google_job(self, card):
        """Parse une offre Google Jobs."""
        try:
            title = card.find("div", class_="BjJfJf").text if card.find("div", class_="BjJfJf") else "N/A"
            company = card.find("div", class_="vNEEBe").text if card.find("div", class_="vNEEBe") else "N/A"
            location = card.find("div", class_="Qk80Jf").text if card.find("div", class_="Qk80Jf") else "N/A"

            return {
                "source": "Google Jobs",
                "title": title,
                "company": company,
                "location": location,
                "description": "",
                "url": "",
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception:
            return None
