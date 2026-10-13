#!/usr/bin/env python3
"""
Lead Scraper & Enricher - Moteur de Web Scraping et d'Enrichissement de Leads
==============================================================================

Ce script automatise:
1. Le scraping de leads depuis Indeed (offres) et LinkedIn (profils)
2. L'enrichissement des données via OpenAI GPT-4
3. Le stockage en base SQLite

Usage:
    python src/main.py --source indeed --query "growth hacker" --location "Paris"
    python src/main.py --source linkedin --query "CTO" --location "France"
    python src/main.py --gui  # Lance l'interface graphique
"""

import argparse
import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import GEMINI_API_KEY, MAX_RESULTS, DISCORD_WEBHOOK_URL, WEBHOOK_URL
from src.database import LeadsDatabase
from src.functional_scraper import FunctionalScraper
from src.ai_generated_scraper import AIGeneratedScraper
from src.gemini_enricher import GeminiEnricher
from src.exporters import export_to_csv, export_to_excel, export_to_json
from src.webhook import send_webhook, send_discord_webhook


def scrape_leads(source, query, location, max_results):
    """Scrape les leads selon la source avec fallback IA."""
    leads = []

    print(f"\n[Scraping] Recherche: '{query}' à '{location}'")

    print("  -> Tentative avec sources web...")
    scraper = FunctionalScraper()
    leads = scraper.scrape_all_sources(query, location, max_results)

    if not leads:
        print("  -> Sources web bloquées. Utilisation de Gemini AI...")
        ai_scraper = AIGeneratedScraper(GEMINI_API_KEY)
        leads = ai_scraper.generate_leads(query, location, max_results)

    print(f"  -> {len(leads)} offres trouvées au total")

    return leads


def enrich_leads(leads):
    """Enrichit les leads avec l'IA Gemini."""
    if not leads:
        return leads

    print(f"\n[IA] Enrichissement de {len(leads)} leads via Gemini...")
    enricher = GeminiEnricher(GEMINI_API_KEY)
    enriched = enricher.enrich_batch(leads)

    hot = sum(1 for l in enriched if l.get("ai_enrichment", {}).get("score_qualification") == "hot")
    warm = sum(1 for l in enriched if l.get("ai_enrichment", {}).get("score_qualification") == "warm")
    cold = sum(1 for l in enriched if l.get("ai_enrichment", {}).get("score_qualification") == "cold")

    print(f"  -> Hot: {hot} | Warm: {warm} | Cold: {cold}")

    return enriched


def save_to_database(leads):
    """Sauvegarde les leads dans SQLite."""
    print(f"\n[DB] Sauvegarde de {len(leads)} leads...")
    db = LeadsDatabase()
    inserted = db.insert_leads_batch(leads)
    print(f"  -> {inserted} leads sauvegardés en base")

    stats = db.get_stats()
    print(f"  -> Stats total: {stats['total']} | Hot: {stats['hot']} | Warm: {stats['warm']} | Cold: {stats['cold']}")

    db.close()
    return inserted


def print_summary(leads):
    """Affiche un résumé des résultats."""
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Total leads scrapés: {len(leads)}")

    sources = {}
    for lead in leads:
        src = lead.get("source", "Unknown")
        sources[src] = sources.get(src, 0) + 1

    for src, count in sources.items():
        print(f"  - {src}: {count}")

    enriched = [l for l in leads if l.get("ai_enrichment")]
    print(f"Leads enrichis: {len(enriched)}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Lead Scraper & Enricher - Scraping et enrichissement automatique"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Lance l'interface graphique",
    )
    parser.add_argument(
        "--source",
        choices=["indeed", "linkedin", "all"],
        default="indeed",
        help="Source de scraping (défaut: indeed)",
    )
    parser.add_argument(
        "--query",
        help="Requête de recherche (ex: 'growth hacker', 'CTO')",
    )
    parser.add_argument(
        "--location",
        default="",
        help="Localisation cible (ex: 'Paris', 'France')",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=MAX_RESULTS,
        help=f"Nombre max de résultats (défaut: {MAX_RESULTS})",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Désactiver l'enrichissement IA",
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv", "excel", "all"],
        help="Exporter les leads (excel/csv/json/all) dans data/",
    )
    parser.add_argument(
        "--excel",
        action="store_true",
        help="Exporte en Excel .xlsx (gratuit)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Exporte en CSV (gratuit)",
    )
    parser.add_argument(
        "--webhook",
        type=str,
        default="",
        help="URL webhook générique (n8n/Make/Zapier) pour envoyer les leads",
    )
    parser.add_argument(
        "--discord",
        type=str,
        default="",
        help="URL webhook Discord pour envoyer les leads",
    )

    args = parser.parse_args()

    if args.gui:
        from gui import main as gui_main
        gui_main()
        return

    if not args.query:
        parser.error("--query est requis (sauf avec --gui)")

    print("=" * 60)
    print("LEAD SCRAPER & ENRICHER")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    leads = scrape_leads(args.source, args.query, args.location, args.max_results)

    if not leads:
        print("\nAucun lead trouvé. Essayez une autre requête.")
        sys.exit(1)

    if not args.no_enrich:
        leads = enrich_leads(leads)

    save_to_database(leads)

    # --- Exports gratuits (Excel / CSV / JSON) ---
    do_excel = args.excel or args.export in ("excel", "all")
    do_csv = args.csv or args.export in ("csv", "all")
    do_json = args.export in ("json", "all")

    # Par défaut si aucun export spécifié : génère Excel + CSV automatiquement
    if not any([do_excel, do_csv, do_json, args.webhook, args.discord]) and not args.webhook and not args.discord:
        # On exporte Excel + CSV par défaut (pratique pour le CV/démo)
        do_excel = True
        do_csv = True

    # Utilise les URLs du .env si non passées en CLI
    webhook_url = args.webhook or WEBHOOK_URL
    discord_url = args.discord or DISCORD_WEBHOOK_URL

    if do_excel:
        try:
            export_to_excel(leads)
        except ImportError as e:
            print(f"[Excel] {e}")

    if do_csv:
        export_to_csv(leads)

    if do_json:
        export_to_json(leads)

    if webhook_url:
        print(f"\n[Webhook] Envoi vers {webhook_url[:40]}...")
        send_webhook(leads, webhook_url)

    if discord_url:
        print(f"\n[Discord] Envoi vers Discord...")
        send_discord_webhook(leads, discord_url)

    print_summary(leads)


if __name__ == "__main__":
    main()
