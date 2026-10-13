#!/usr/bin/env python3
"""
Lead Scraper GUI - Interface graphique pour le scraper de leads
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import GEMINI_API_KEY, MAX_RESULTS
from src.database import LeadsDatabase
from src.functional_scraper import FunctionalScraper
from src.ai_generated_scraper import AIGeneratedScraper
from src.gemini_enricher import GeminiEnricher


class LeadScraperApp:
    """Application GUI pour le scraping et l'enrichissement de leads."""

    def __init__(self, root):
        self.root = root
        self.root.title("Lead Scraper & Enricher")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        self.db = LeadsDatabase()
        self.is_scraping = False

        self._setup_styles()
        self._create_widgets()
        self._refresh_leads_list()

    def _setup_styles(self):
        """Configure les styles de l'application."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 9))

        style.configure("Hot.TLabel", foreground="#e74c3c", font=("Segoe UI", 10, "bold"))
        style.configure("Warm.TLabel", foreground="#f39c12", font=("Segoe UI", 10, "bold"))
        style.configure("Cold.TLabel", foreground="#3498db", font=("Segoe UI", 10, "bold"))

    def _create_widgets(self):
        """Crée tous les widgets de l'interface."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._create_header(main_frame)

        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=2)

        self._create_scraping_panel(left_panel)
        self._create_stats_panel(left_panel)
        self._create_leads_table(right_panel)
        self._create_lead_details(right_panel)
        self._create_status_bar(main_frame)

    def _create_header(self, parent):
        """Crée l'en-tête de l'application."""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X)

        ttk.Label(header, text="Lead Scraper & Enricher", style="Title.TLabel").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(btn_frame, text="Excel", command=self._export_excel).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="CSV", command=self._export_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="JSON", command=self._export_json).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Discord", command=self._send_discord).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Vider la DB", command=self._clear_database).pack(side=tk.LEFT, padx=2)

    def _create_scraping_panel(self, parent):
        """Crée le panneau de scraping."""
        frame = ttk.LabelFrame(parent, text="Scraping", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Source:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.source_var = tk.StringVar(value="indeed")
        source_combo = ttk.Combobox(frame, textvariable=self.source_var, 
                                     values=["indeed", "linkedin", "all"], 
                                     state="readonly", width=15)
        source_combo.grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(frame, text="Requête:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.query_var = tk.StringVar(value="growth hacker")
        ttk.Entry(frame, textvariable=self.query_var, width=20).grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(frame, text="Localisation:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.location_var = tk.StringVar(value="Paris")
        ttk.Entry(frame, textvariable=self.location_var, width=20).grid(row=2, column=1, sticky=tk.W, pady=2)

        ttk.Label(frame, text="Max résultats:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.max_results_var = tk.StringVar(value=str(MAX_RESULTS))
        ttk.Spinbox(frame, from_=1, to=200, textvariable=self.max_results_var, width=17).grid(row=3, column=1, sticky=tk.W, pady=2)

        self.enrich_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Enrichir avec IA", variable=self.enrich_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Webhook Discord:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.discord_var = tk.StringVar(value="")
        ttk.Entry(frame, textvariable=self.discord_var, width=20).grid(row=5, column=1, sticky=tk.W, pady=2)
        ttk.Label(frame, text="(optionnel)", font=("Segoe UI", 7)).grid(row=6, column=0, columnspan=2, sticky=tk.W)

        self.scrape_btn = ttk.Button(frame, text="Lancer le scraping", command=self._start_scraping)
        self.scrape_btn.grid(row=7, column=0, columnspan=2, pady=(10, 0), sticky=tk.EW)

        self.progress = ttk.Progressbar(frame, mode="indeterminate")
        self.progress.grid(row=8, column=0, columnspan=2, pady=(5, 0), sticky=tk.EW)

    def _create_stats_panel(self, parent):
        """Crée le panneau de statistiques."""
        frame = ttk.LabelFrame(parent, text="Statistiques", padding=10)
        frame.pack(fill=tk.X)

        self.stats_frame = ttk.Frame(frame)
        self.stats_frame.pack(fill=tk.X)

        self._update_stats_display()

    def _update_stats_display(self):
        """Met à jour l'affichage des statistiques."""
        for widget in self.stats_frame.winfo_children():
            widget.destroy()

        stats = self.db.get_stats()

        labels = [
            ("Total", stats["total"], "TLabel"),
            ("Hot", stats["hot"], "Hot.TLabel"),
            ("Warm", stats["warm"], "Warm.TLabel"),
            ("Cold", stats["cold"], "Cold.TLabel"),
        ]

        for i, (text, value, style) in enumerate(labels):
            ttk.Label(self.stats_frame, text=f"{text}:", style="Header.TLabel").grid(row=i, column=0, sticky=tk.W, pady=2)
            ttk.Label(self.stats_frame, text=str(value), style=style).grid(row=i, column=1, padx=(10, 0), pady=2)

        if stats["sources"]:
            ttk.Separator(self.stats_frame, orient=tk.HORIZONTAL).grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=5)
            ttk.Label(self.stats_frame, text="Sources:", style="Header.TLabel").grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)

            for i, (source, count) in enumerate(stats["sources"].items()):
                ttk.Label(self.stats_frame, text=f"  {source}:").grid(row=6 + i, column=0, sticky=tk.W)
                ttk.Label(self.stats_frame, text=str(count)).grid(row=6 + i, column=1, padx=(10, 0))

    def _create_leads_table(self, parent):
        """Crée le tableau des leads."""
        frame = ttk.LabelFrame(parent, text="Leads", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(filter_frame, text="Filtrer:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._filter_leads())
        ttk.Entry(filter_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="Score:").pack(side=tk.LEFT, padx=(10, 0))
        self.filter_score_var = tk.StringVar(value="all")
        score_combo = ttk.Combobox(filter_frame, textvariable=self.filter_score_var,
                                    values=["all", "hot", "warm", "cold"], state="readonly", width=8)
        score_combo.pack(side=tk.LEFT, padx=5)
        score_combo.bind("<<ComboboxSelected>>", lambda *args: self._filter_leads())

        columns = ("id", "source", "title", "company", "location", "score")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("source", text="Source")
        self.tree.heading("title", text="Titre/Nom")
        self.tree.heading("company", text="Entreprise")
        self.tree.heading("location", text="Localisation")
        self.tree.heading("score", text="Score")

        self.tree.column("id", width=40)
        self.tree.column("source", width=80)
        self.tree.column("title", width=200)
        self.tree.column("company", width=150)
        self.tree.column("location", width=120)
        self.tree.column("score", width=60)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_lead_select)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="Enrichir sélection", command=self._enrich_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Supprimer", command=self._delete_selected).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Rafraîchir", command=self._refresh_leads_list).pack(side=tk.RIGHT, padx=2)

    def _create_lead_details(self, parent):
        """Crée le panneau de détails d'un lead."""
        frame = ttk.LabelFrame(parent, text="Détails du Lead", padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.details_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=("Consolas", 10))
        self.details_text.pack(fill=tk.BOTH, expand=True)
        self.details_text.insert(tk.END, "Sélectionnez un lead pour voir ses détails...")
        self.details_text.config(state=tk.DISABLED)

    def _create_status_bar(self, parent):
        """Crée la barre de statut."""
        self.status_var = tk.StringVar(value="Prêt")
        status_bar = ttk.Label(parent, textvariable=self.status_var, style="Status.TLabel", relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(10, 0))

    def _start_scraping(self):
        """Lance le scraping dans un thread séparé."""
        if self.is_scraping:
            return

        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Attention", "Veuillez entrer une requête de recherche.")
            return

        self.is_scraping = True
        self.scrape_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Scraping en cours...")

        thread = threading.Thread(target=self._run_scraping, daemon=True)
        thread.start()

    def _run_scraping(self):
        """Exécute le scraping."""
        try:
            source = self.source_var.get()
            query = self.query_var.get()
            location = self.location_var.get()
            max_results = int(self.max_results_var.get())
            do_enrich = self.enrich_var.get()

            self.root.after(0, lambda: self.status_var.set("Scraping web en cours..."))
            scraper = FunctionalScraper()
            leads = scraper.scrape_all_sources(query, location, max_results)

            if not leads:
                self.root.after(0, lambda: self.status_var.set("Sources web bloquées. Utilisation Gemini AI..."))
                ai_scraper = AIGeneratedScraper(GEMINI_API_KEY)
                leads = ai_scraper.generate_leads(query, location, max_results)

            if do_enrich and leads:
                self.root.after(0, lambda: self.status_var.set(f"Enrichissement de {len(leads)} leads avec Gemini..."))
                enricher = GeminiEnricher(GEMINI_API_KEY)
                leads = enricher.enrich_batch(leads)

            if leads:
                self.root.after(0, lambda: self.status_var.set("Sauvegarde en base..."))
                inserted = self.db.insert_leads_batch(leads)
                self.root.after(0, lambda: self.status_var.set(f"{inserted} leads sauvegardés"))

                # Auto-export Excel/CSV gratuit
                try:
                    from src.exporters import export_to_csv, export_to_excel
                    export_to_csv(leads)
                    export_to_excel(leads)
                except Exception:
                    pass

                # Auto-envoi Discord si webhook renseigné
                discord_url = self.discord_var.get().strip()
                if discord_url:
                    self.root.after(0, lambda: self.status_var.set("Envoi Discord..."))
                    from src.webhook import send_discord_webhook
                    send_discord_webhook(leads, discord_url)
            else:
                self.root.after(0, lambda: self.status_var.set("Aucun lead trouvé"))

            self.root.after(0, self._on_scraping_complete)

        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Erreur: {str(e)}"))
            self.root.after(0, self._on_scraping_complete)

    def _on_scraping_complete(self):
        """Appelé quand le scraping est terminé."""
        self.is_scraping = False
        self.scrape_btn.config(state=tk.NORMAL)
        self.progress.stop()
        self._refresh_leads_list()
        self._update_stats_display()

    def _refresh_leads_list(self):
        """Rafraîchit la liste des leads."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        leads = self.db.get_all_leads()

        for lead in leads:
            score = lead.get("score_qualification", "") or ""
            self.tree.insert("", tk.END, values=(
                lead.get("id", ""),
                lead.get("source", ""),
                lead.get("title", lead.get("name", "")),
                lead.get("company", ""),
                lead.get("location", ""),
                score.upper() if score else "-",
            ))

    def _filter_leads(self):
        """Filtre les leads selon les critères."""
        query = self.search_var.get()
        score = self.filter_score_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        leads = self.db.search_leads(query, score=score if score != "all" else None)

        for lead in leads:
            lead_score = lead.get("score_qualification", "") or ""
            self.tree.insert("", tk.END, values=(
                lead.get("id", ""),
                lead.get("source", ""),
                lead.get("title", lead.get("name", "")),
                lead.get("company", ""),
                lead.get("location", ""),
                lead_score.upper() if lead_score else "-",
            ))

    def _on_lead_select(self, event):
        """Affiche les détails du lead sélectionné."""
        selection = self.tree.selection()
        if not selection:

            return

        item = self.tree.item(selection[0])
        lead_id = item["values"][0]

        lead = self.db.get_lead_by_id(lead_id)
        if not lead:
            return

        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)

        details = self._format_lead_details(lead)
        self.details_text.insert(tk.END, details)
        self.details_text.config(state=tk.DISABLED)

    def _format_lead_details(self, lead):
        """Formate les détails d'un lead pour l'affichage."""
        lines = []
        lines.append("=" * 50)
        lines.append("INFORMATIONS DU LEAD")
        lines.append("=" * 50)
        lines.append(f"ID: {lead.get('id')}")
        lines.append(f"Source: {lead.get('source')}")
        lines.append(f"Titre/Nom: {lead.get('title', lead.get('name', 'N/A'))}")
        lines.append(f"Entreprise: {lead.get('company', 'N/A')}")
        lines.append(f"Localisation: {lead.get('location', 'N/A')}")
        lines.append(f"URL: {lead.get('url', lead.get('profile_url', 'N/A'))}")
        lines.append(f"Scrapé le: {lead.get('scraped_at', 'N/A')}")
        lines.append(f"Ajouté le: {lead.get('created_at', 'N/A')}")

        if lead.get("description"):
            lines.append("")
            lines.append("-" * 50)
            lines.append("DESCRIPTION")
            lines.append("-" * 50)
            lines.append(lead["description"])

        if lead.get("score_qualification"):
            lines.append("")
            lines.append("=" * 50)
            lines.append("ENRICHISSEMENT IA")
            lines.append("=" * 50)
            lines.append(f"Score: {lead.get('score_qualification', 'N/A').upper()}")
            lines.append(f"Potentiel: {lead.get('potentiel_estime', 'N/A')}")
            lines.append(f"Secteur: {lead.get('secteur_activite', 'N/A')}")
            lines.append(f"Taille: {lead.get('taille_entreprise', 'N/A')}")
            lines.append(f"Décideur: {'Oui' if lead.get('decision_maker') else 'Non'}")

            if lead.get("approche_recommandee"):
                lines.append("")
                lines.append("Approche recommandée:")
                lines.append(f"  {lead['approche_recommandee']}")

            if lead.get("points_de_contact"):
                lines.append("")
                lines.append("Points de contact:")
                try:
                    points = json.loads(lead["points_de_contact"])
                    for p in points:
                        lines.append(f"  • {p}")
                except (json.JSONDecodeError, TypeError):
                    lines.append(f"  {lead['points_de_contact']}")

            if lead.get("risques"):
                lines.append("")
                lines.append("Risques:")
                try:
                    risques = json.loads(lead["risques"])
                    for r in risques:
                        lines.append(f"  ⚠ {r}")
                except (json.JSONDecodeError, TypeError):
                    lines.append(f"  {lead['risques']}")

            if lead.get("opportunites"):
                lines.append("")
                lines.append("Opportunités:")
                try:
                    opps = json.loads(lead["opportunites"])
                    for o in opps:
                        lines.append(f"  ✓ {o}")
                except (json.JSONDecodeError, TypeError):
                    lines.append(f"  {lead['opportunites']}")

        return "\n".join(lines)

    def _enrich_selected(self):
        """Enrichit le lead sélectionné avec l'IA."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un lead à enrichir.")
            return

        item = self.tree.item(selection[0])
        lead_id = item["values"][0]
        lead = self.db.get_lead_by_id(lead_id)

        if not lead:
            return

        if lead.get("score_qualification"):
            if not messagebox.askyesno("Confirmation", "Ce lead est déjà enrichir. Voulez-vous le réenrichir ?"):
                return

        self.status_var.set("Enrichissement en cours...")

        def enrich_thread():
            try:
                enricher = GeminiEnricher(GEMINI_API_KEY)
                lead_data = {
                    "source": lead.get("source"),
                    "title": lead.get("title"),
                    "company": lead.get("company"),
                    "location": lead.get("location"),
                    "description": lead.get("description"),
                }

                enrichment = enricher.enrich_lead(lead_data)
                self.db.insert_enrichment(lead_id, enrichment)

                self.root.after(0, lambda: self.status_var.set("Enrichissement terminé"))
                self.root.after(0, self._refresh_leads_list)
                self.root.after(0, self._update_stats_display)
                self.root.after(0, lambda: self._on_lead_select(None))

            except Exception as e:
                self.root.after(0, lambda: self.status_var.set(f"Erreur: {str(e)}"))

        threading.Thread(target=enrich_thread, daemon=True).start()

    def _delete_selected(self):
        """Supprime le lead sélectionné."""
        selection = self.tree.selection()
        if not selection:
            return

        if not messagebox.askyesno("Confirmation", "Supprimer ce lead ?"):
            return

        item = self.tree.item(selection[0])
        lead_id = item["values"][0]
        self.db.delete_lead(lead_id)
        self._refresh_leads_list()
        self._update_stats_display()
        self.status_var.set("Lead supprimé")

    def _export_json(self):
        """Exporte les leads en JSON."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        if filename:
            count = self.db.export_to_json(filename)
            self.status_var.set(f"{count} leads exportés en JSON")
            messagebox.showinfo("Export", f"{count} leads exportés avec succès.")

    def _export_csv(self):
        """Exporte les leads en CSV (gratuit)."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        if filename:
            from src.exporters import export_to_csv
            leads = self.db.get_all_leads()
            if not leads:
                messagebox.showwarning("Export", "Aucun lead à exporter.")
                return
            export_to_csv(leads, filename)
            self.status_var.set(f"{len(leads)} leads exportés en CSV")
            messagebox.showinfo("Export", f"{len(leads)} leads exportés: {filename}")

    def _export_excel(self):
        """Exporte les leads en Excel .xlsx (gratuit)."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if filename:
            from src.exporters import export_to_excel
            leads = self.db.get_all_leads()
            if not leads:
                messagebox.showwarning("Export", "Aucun lead à exporter.")
                return
            try:
                export_to_excel(leads, filename)
                self.status_var.set(f"{len(leads)} leads exportés en Excel")
                messagebox.showinfo("Export", f"{len(leads)} leads exportés: {filename}")
            except ImportError as e:
                messagebox.showerror("Erreur", str(e))

    def _send_discord(self):
        """Envoie les leads vers Discord webhook."""
        url = self.discord_var.get().strip()
        if not url:
            url = filedialog.askstring = None
            # Demande l'URL via popup simple
            import tkinter.simpledialog as simpledialog
            url = simpledialog.askstring("Webhook Discord", "Collez l'URL du webhook Discord:\n(Salon > Paramètres > Intégrations > Webhooks)")
            if not url:
                return
            self.discord_var.set(url)

        from src.webhook import send_discord_webhook
        leads = self.db.get_all_leads()
        # Convertir format DB -> format attendu par webhook (avec ai_enrichment)
        formatted = []
        for l in leads:
            formatted.append({
                "source": l.get("source"),
                "title": l.get("title"),
                "company": l.get("company"),
                "location": l.get("location"),
                "description": l.get("description"),
                "url": l.get("url"),
                "scraped_at": l.get("scraped_at"),
                "ai_enrichment": {
                    "score_qualification": l.get("score_qualification"),
                    "potentiel_estime": l.get("potentiel_estime"),
                    "secteur_activite": l.get("secteur_activite"),
                    "approche_recommandee": l.get("approche_recommandee"),
                }
            })

        if not formatted:
            messagebox.showwarning("Discord", "Aucun lead à envoyer.")
            return

        self.status_var.set("Envoi Discord en cours...")
        def do_send():
            ok = send_discord_webhook(formatted, url)
            if ok:
                self.root.after(0, lambda: self.status_var.set("Envoyé vers Discord"))
                self.root.after(0, lambda: messagebox.showinfo("Discord", f"{len(formatted)} leads envoyés vers Discord"))
            else:
                self.root.after(0, lambda: self.status_var.set("Erreur Discord"))
                self.root.after(0, lambda: messagebox.showerror("Discord", "Échec de l'envoi. Vérifiez l'URL du webhook."))

        import threading
        threading.Thread(target=do_send, daemon=True).start()

    def _clear_database(self):
        """Vide la base de données."""
        if messagebox.askyesno("Confirmation", "Supprimer TOUS les leads ? Cette action est irréversible."):
            self.db.clear_all()
            self._refresh_leads_list()
            self._update_stats_display()
            self.status_var.set("Base de données vidée")

    def on_closing(self):
        """Appelé à la fermeture de l'application."""
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = LeadScraperApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
