import requests
import json

def send_webhook(leads, webhook_url, batch_size=10):
    """
    Envoie les leads vers un webhook générique (n8n, Make, Zapier, CRM...).
    Gratuit, sans authentification cloud.
    """
    if not webhook_url:
        print("[Webhook] URL manquante")
        return False

    headers = {"Content-Type": "application/json"}

    # Envoi par lot pour éviter les payloads trop gros
    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        payload = {
            "source": "lead-scraper",
            "total": len(leads),
            "batch": f"{i//batch_size + 1}/{(len(leads)-1)//batch_size + 1}",
            "leads": batch
        }
        try:
            resp = requests.post(webhook_url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            print(f"[Webhook] Lot {i//batch_size + 1} envoyé ({len(batch)} leads) -> {resp.status_code}")
        except Exception as e:
            print(f"[Webhook] Erreur lot {i//batch_size + 1}: {e}")
            return False

    return True


def send_discord_webhook(leads, discord_url, max_leads=10):
    """
    Envoie les leads vers un webhook Discord (gratuit).
    Formate en embeds colorés par score Hot/Warm/Cold.
    Crée un webhook Discord en 10s: Salon Discord > Paramètres > Intégrations > Webhooks > Nouveau webhook
    """
    if not discord_url:
        print("[Discord] URL manquante")
        return False

    color_map = {"hot": 0xE74C3C, "warm": 0xF39C12, "cold": 0x3498DB}

    # Discord limite à 10 embeds par message, on envoie 1 message par lead (ou groupé)
    for lead in leads[:max_leads]:
        enrichment = lead.get("ai_enrichment", {})
        score = str(enrichment.get("score_qualification", "")).lower() or "unknown"
        color = color_map.get(score, 0x95A5A6)

        title = lead.get("title", lead.get("name", "Lead sans titre"))
        company = lead.get("company", "N/A")
        location = lead.get("location", "N/A")
        url = lead.get("url") or lead.get("profile_url") or ""

        # Points clés
        approche = enrichment.get("approche_recommandee", "")
        secteur = enrichment.get("secteur_activite", "")
        potentiel = enrichment.get("potentiel_estime", "")

        embed = {
            "title": f"{title} @ {company}",
            "color": color,
            "fields": [
                {"name": "Source", "value": lead.get("source", "N/A"), "inline": True},
                {"name": "Score", "value": score.upper(), "inline": True},
                {"name": "Potentiel", "value": potentiel or "N/A", "inline": True},
                {"name": "Localisation", "value": location, "inline": True},
                {"name": "Secteur", "value": secteur or "N/A", "inline": True},
                {"name": "URL", "value": url or "N/A", "inline": False},
            ],
            "footer": {"text": f"Lead Scraper • {lead.get('scraped_at', '')[:10]}"},
        }
        if approche:
            embed["fields"].append({"name": "Approche recommandée", "value": approche[:1024], "inline": False})

        payload = {
            "username": "Lead Scraper",
            "embeds": [embed]
        }

        try:
            resp = requests.post(discord_url, json=payload, timeout=10)
            resp.raise_for_status()
            print(f"[Discord] Lead envoyé: {title}")
        except Exception as e:
            print(f"[Discord] Erreur: {e}")
            # Affiche le détail si Discord renvoie 400
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
            return False

    # Résumé
    if len(leads) > max_leads:
        try:
            summary = {
                "content": f"✅ **{len(leads)} leads scrapés** — {max_leads} affichés ci-dessus, {len(leads)-max_leads} restants disponibles en Excel/CSV dans `data/`"
            }
            requests.post(discord_url, json=summary, timeout=10)
        except:
            pass

    print(f"[Discord] {min(len(leads), max_leads)}/{len(leads)} leads envoyés")
    return True
