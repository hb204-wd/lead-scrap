# Lead Scraper & Enricher

Moteur de Web Scraping et d'Enrichissement de Leads pour Growth Engineering — **100% gratuit, sans carte bancaire**.

## Fonctionnalités

- **Scraping** : Indeed + LinkedIn + fallback IA (Gemini)
- **Enrichissement IA** : Qualification Hot/Warm/Cold via Gemini
- **Base SQLite** : Stockage local `data/leads.db`
- **Interface Graphique** : GUI tkinter
- **Exports gratuits** : **Excel (.xlsx)**, **CSV**, **JSON** — aucun compte cloud requis
- **Webhooks gratuits** : **Discord** + webhook générique (n8n/Make/Zapier/CRM)

> **Google Sheets a été retiré** — il nécessite un compte GCP payant. Remplacé par Excel/CSV/Webhook qui sont gratuits et suffisent pour le portfolio.

## Installation

```bash
cd "web scrap"
pip install -r requirements.txt
```

## Configuration

Clés déjà dans `.env` (OpenAI + Gemini). Pour les exports :

- **Excel/CSV** : rien à configurer, fichiers dans `data/`
- **Discord** : crée un webhook en 10s (Salon Discord > Paramètres > Intégrations > Webhooks > Nouveau webhook) puis colle l'URL dans `.env` → `DISCORD_WEBHOOK_URL=` ou dans la GUI
- **Webhook générique** : colle ton URL n8n/Make/Zapier dans `.env` → `WEBHOOK_URL=`

## Utilisation

### Interface Graphique (recommandée)

```bash
python gui.py
# Boutons: Excel / CSV / JSON / Discord / Vider la DB
# Champ "Webhook Discord" : colle ton URL et lance le scraping -> envoi auto
```

### Ligne de commande

```bash
# Scraping + export auto Excel + CSV (par défaut)
python src/main.py --query "growth hacker" --location "Paris"

# Exports explicites
python src/main.py --query "CTO" --location "Paris" --excel --csv
python src/main.py --query "startup" --export all        # excel+csv+json
python src/main.py --query "marketing" --export excel
python src/main.py --query "data" --export csv

# Webhooks (gratuits)
python src/main.py --query "growth hacker" --discord "https://discord.com/api/webhooks/..."
python src/main.py --query "CTO" --webhook "https://n8n.example.com/webhook/xxx"

# Via .env (pas besoin de passer l'URL en CLI)
# Renseigne DISCORD_WEBHOOK_URL dans .env puis :
python src/main.py --query "growth hacker"

# Sans IA (plus rapide)
python src/main.py --query "marketing" --no-enrich
```

## Structure

```
web scrap/
├── config/settings.py      # Config (DISCORD_WEBHOOK_URL, WEBHOOK_URL)
├── src/
│   ├── functional_scraper.py   # Scraping web
│   ├── ai_generated_scraper.py # Fallback IA
│   ├── gemini_enricher.py      # Enrichissement
│   ├── database.py             # SQLite
│   ├── exporters.py            # Excel / CSV / JSON (gratuit)
│   ├── webhook.py              # Discord + webhook générique (gratuit)
│   └── main.py                 # CLI
├── gui.py                  # GUI avec boutons Excel/CSV/Discord
├── data/                   # leads.db + exports .xlsx/.csv
├── .env
└── requirements.txt
```

## Format Excel généré

Colonnes: ID | Source | Titre | Entreprise | Localisation | Description | URL | Score | Potentiel | Secteur | Taille | Décideur | Approche | Points de contact | Risques | Opportunités | Date — avec coloration Hot (rouge) / Warm (jaune) / Cold (bleu), filtres et colonnes figées.

## Pour le CV — Growth Engineer

Démontre: automatisation Lead Gen, intégration APIs IA, exports data sans dépendance cloud payante, webhooks, SQLite, architecture modulaire.

## Notes

- Respecte les ToS des sites scrapés
- LinkedIn bloque le scraping agressif -> fallback IA inclus
- Aucun service payant requis
