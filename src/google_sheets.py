import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json


class GoogleSheetsManager:
    """Gère l'envoi des leads enrichis vers Google Sheets."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    HEADERS = [
        "Source",
        "Titre/Name",
        "Entreprise",
        "Localisation",
        "Description",
        "URL",
        "Score Qualification",
        "Potentiel",
        "Secteur",
        "Taille",
        "Decision Maker",
        "Approche Recommandée",
        "Points de Contact",
        "Risques",
        "Opportunités",
        "Date Scraping",
    ]

    def __init__(self, credentials_path, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.gc = self._authenticate(credentials_path)
        self.spreadsheet = self.gc.open_by_key(spreadsheet_id)

    def _authenticate(self, credentials_path):
        """Authentifie avec Google Sheets API."""
        creds = Credentials.from_service_account_file(
            credentials_path, scopes=self.SCOPES
        )
        return gspread.authorize(creds)

    def get_or_create_sheet(self, worksheet_name="Leads"):
        """Récupère ou crée une feuille de calcul."""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=20
            )
            worksheet.update("A1", [self.HEADERS])
            worksheet.format("A1:O1", {"textFormat": {"bold": True}})

        return worksheet

    def send_leads(self, leads, worksheet_name="Leads"):
        """Envoie les leads enrichis vers Google Sheets."""
        worksheet = self.get_or_create_sheet(worksheet_name)

        existing_rows = worksheet.get_all_values()
        start_row = len(existing_rows) + 1

        rows_to_add = []
        for lead in leads:
            enrichment = lead.get("ai_enrichment", {})
            points_contact = enrichment.get("points_de_contact", [])
            risques = enrichment.get("risques", [])
            opportunites = enrichment.get("opportunites", [])

            row = [
                lead.get("source", "N/A"),
                lead.get("title", lead.get("name", "N/A")),
                lead.get("company", "N/A"),
                lead.get("location", "N/A"),
                lead.get("description", lead.get("headline", "N/A")),
                lead.get("url", lead.get("profile_url", "N/A")),
                enrichment.get("score_qualification", "N/A"),
                enrichment.get("potentiel_estime", "N/A"),
                enrichment.get("secteur_activite", "N/A"),
                enrichment.get("taille_entreprise", "N/A"),
                str(enrichment.get("decision_maker", "N/A")),
                enrichment.get("approche_recommandee", "N/A"),
                "; ".join(points_contact) if points_contact else "N/A",
                "; ".join(risques) if risques else "N/A",
                "; ".join(opportunites) if opportunites else "N/A",
                lead.get("scraped_at", datetime.now().isoformat()),
            ]
            rows_to_add.append(row)

        if rows_to_add:
            worksheet.update(
                f"A{start_row}:O{start_row + len(rows_to_add) - 1}",
                rows_to_add,
            )
            print(f"{len(rows_to_add)} leads envoyés vers Google Sheets")

        return len(rows_to_add)

    def get_leads_stats(self, worksheet_name="Leads"):
        """Récupère les statistiques des leads."""
        worksheet = self.get_or_create_sheet(worksheet_name)
        all_data = worksheet.get_all_values()

        if len(all_data) <= 1:
            return {"total": 0, "hot": 0, "warm": 0, "cold": 0}

        headers = all_data[0]
        data_rows = all_data[1:]

        stats = {
            "total": len(data_rows),
            "hot": 0,
            "warm": 0,
            "cold": 0,
        }

        score_col = headers.index("Score Qualification") if "Score Qualification" in headers else -1

        if score_col >= 0:
            for row in data_rows:
                score = row[score_col].lower().strip()
                if score in stats:
                    stats[score] += 1

        return stats

    def export_to_csv(self, filename="leads_export.csv"):
        """Exporte les leads en CSV."""
        worksheet = self.get_or_create_sheet()
        all_data = worksheet.get_all_values()

        import csv
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(all_data)

        print(f"Export CSV: {filename}")
