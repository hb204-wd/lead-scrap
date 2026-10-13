import sqlite3
import json
from datetime import datetime
from pathlib import Path


class LeadsDatabase:
    """Gestion de la base de données SQLite pour les leads."""

    def __init__(self, db_path="data/leads.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None
        self._connect()
        self._create_tables()

    def _connect(self):
        """Établit la connexion à la base de données."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")

    def _create_tables(self):
        """Crée les tables nécessaires."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT,
                name TEXT,
                company TEXT,
                location TEXT,
                description TEXT,
                url TEXT,
                profile_url TEXT,
                scraped_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrichments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                score_qualification TEXT,
                potentiel_estime TEXT,
                secteur_activite TEXT,
                taille_entreprise TEXT,
                decision_maker INTEGER,
                approche_recommandee TEXT,
                points_de_contact TEXT,
                risques TEXT,
                opportunites TEXT,
                raw_response TEXT,
                enriched_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    def insert_lead(self, lead_data):
        """Insère un lead dans la base de données."""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO leads (source, title, name, company, location, description, url, profile_url, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_data.get("source", ""),
            lead_data.get("title", lead_data.get("name", "")),
            lead_data.get("name", ""),
            lead_data.get("company", ""),
            lead_data.get("location", ""),
            lead_data.get("description", lead_data.get("headline", "")),
            lead_data.get("url", ""),
            lead_data.get("profile_url", ""),
            lead_data.get("scraped_at", datetime.now().isoformat()),
        ))

        self.conn.commit()
        return cursor.lastrowid

    def insert_enrichment(self, lead_id, enrichment_data):
        """Insère les données d'enrichissement pour un lead."""
        cursor = self.conn.cursor()

        points_contact = enrichment_data.get("points_de_contact", [])
        risques = enrichment_data.get("risques", [])
        opportunites = enrichment_data.get("opportunites", [])

        cursor.execute("""
            INSERT INTO enrichments (lead_id, score_qualification, potentiel_estime, 
                                    secteur_activite, taille_entreprise, decision_maker,
                                    approche_recommandee, points_de_contact, risques, 
                                    opportunites, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_id,
            enrichment_data.get("score_qualification", ""),
            enrichment_data.get("potentiel_estime", ""),
            enrichment_data.get("secteur_activite", ""),
            enrichment_data.get("taille_entreprise", ""),
            1 if enrichment_data.get("decision_maker") else 0,
            enrichment_data.get("approche_recommandee", ""),
            json.dumps(points_contact, ensure_ascii=False),
            json.dumps(risques, ensure_ascii=False),
            json.dumps(opportunites, ensure_ascii=False),
            json.dumps(enrichment_data, ensure_ascii=False),
        ))

        self.conn.commit()

    def insert_leads_batch(self, leads):
        """Insère un lot de leads avec leurs enrichissements."""
        inserted = 0

        for lead in leads:
            lead_id = self.insert_lead(lead)
            enrichment = lead.get("ai_enrichment", {})

            if enrichment:
                self.insert_enrichment(lead_id, enrichment)

            inserted += 1

        return inserted

    def get_all_leads(self, with_enrichment=True):
        """Récupère tous les leads avec optionnellement leurs enrichissements."""
        cursor = self.conn.cursor()

        if with_enrichment:
            cursor.execute("""
                SELECT l.*, 
                       e.score_qualification, e.potentiel_estime, e.secteur_activite,
                       e.taille_entreprise, e.decision_maker, e.approche_recommandee,
                       e.points_de_contact, e.risques, e.opportunites
                FROM leads l
                LEFT JOIN enrichments e ON l.id = e.lead_id
                ORDER BY l.created_at DESC
            """)
        else:
            cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_lead_by_id(self, lead_id):
        """Récupère un lead par son ID."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT l.*, 
                   e.score_qualification, e.potentiel_estime, e.secteur_activite,
                   e.taille_entreprise, e.decision_maker, e.approche_recommandee,
                   e.points_de_contact, e.risques, e.opportunites
            FROM leads l
            LEFT JOIN enrichments e ON l.id = e.lead_id
            WHERE l.id = ?
        """, (lead_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def search_leads(self, query, source=None, score=None):
        """Recherche des leads par mots-clés."""
        cursor = self.conn.cursor()

        sql = """
            SELECT l.*, 
                   e.score_qualification, e.potentiel_estime, e.secteur_activite,
                   e.taille_entreprise, e.decision_maker, e.approche_recommandee,
                   e.points_de_contact, e.risques, e.opportunites
            FROM leads l
            LEFT JOIN enrichments e ON l.id = e.lead_id
            WHERE (l.title LIKE ? OR l.name LIKE ? OR l.company LIKE ? OR l.description LIKE ?)
        """
        params = [f"%{query}%"] * 4

        if source:
            sql += " AND l.source = ?"
            params.append(source)

        if score:
            sql += " AND e.score_qualification = ?"
            params.append(score)

        sql += " ORDER BY l.created_at DESC"

        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def delete_lead(self, lead_id):
        """Supprime un lead et son enrichissement."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM enrichments WHERE lead_id = ?", (lead_id,))
        cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        self.conn.commit()

    def get_stats(self):
        """Récupère les statistiques des leads."""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM leads")
        total = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT e.score_qualification, COUNT(*) as count
            FROM leads l
            LEFT JOIN enrichments e ON l.id = e.lead_id
            WHERE e.score_qualification IS NOT NULL
            GROUP BY e.score_qualification
        """)
        scores = {row["score_qualification"]: row["count"] for row in cursor.fetchall()}

        cursor.execute("SELECT source, COUNT(*) as count FROM leads GROUP BY source")
        sources = {row["source"]: row["count"] for row in cursor.fetchall()}

        return {
            "total": total,
            "hot": scores.get("hot", 0),
            "warm": scores.get("warm", 0),
            "cold": scores.get("cold", 0),
            "sources": sources,
        }

    def clear_all(self):
        """Supprime tous les leads."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM enrichments")
        cursor.execute("DELETE FROM leads")
        self.conn.commit()

    def export_to_json(self, filename="leads_export.json"):
        """Exporte les leads en JSON."""
        leads = self.get_all_leads()

        for lead in leads:
            for key in ["points_de_contact", "risques", "opportunites"]:
                if lead.get(key) and isinstance(lead[key], str):
                    try:
                        lead[key] = json.loads(lead[key])
                    except json.JSONDecodeError:
                        pass

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)

        return len(leads)

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
