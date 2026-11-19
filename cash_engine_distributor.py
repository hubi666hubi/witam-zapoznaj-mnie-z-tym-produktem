#!/usr/bin/env python3
"""
Cash Engine Distributor — W.F.P. Monetization Core
Automatyczne spięcie potoku Lead -> Kwalifikacja KRS -> Wycena Dynamiczna -> Stripe Checkout Link.
Przekształca zainwestowany czas w realny strumień przychodów ($).
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

class CashEngineDistributor:
    def __init__(self, stripe_secret_key: Optional[str] = None):
        self.stripe_key = stripe_secret_key or os.getenv("STRIPE_SECRET_KEY", "")

    def calculate_deal_size(self, lead_kpi: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dobiera model cenowy pod sytuację finansową firmy ze sprawozdania KRS:
        - Przychód > 10M PLN -> Pakiet Enterprise: 4 900 PLN / msc + 5 000 PLN setup
        - Przychód 2M-10M PLN -> Pakiet Growth Pro: 2 400 PLN / msc + 2 500 PLN setup
        - Deweloper / Startup -> Brama Pantheon Oracle: 199 PLN ($49) / msc
        """
        rev = lead_kpi.get("annual_revenue_pln", 0.0)
        net = lead_kpi.get("net_profit_pln", 0.0)

        if rev >= 10_000_000:
            tier = "ENTERPRISE_SWARM"
            mrr_pln = 4900
            setup_fee_pln = 5000
            pitch_hook = f"Przy skali {rev:,.0f} PLN przychodów, automatyzacja procesów B2B generuje zwrot w pierwszym kwartale."
        elif rev >= 2_000_000:
            tier = "GROWTH_KOMBAYN"
            mrr_pln = 2400
            setup_fee_pln = 2500
            pitch_hook = f"Zabezpiecz stabilność zysku ({net:,.0f} PLN netto) eliminując wąskie gardła w pozyskiwaniu kontraktów."
        else:
            tier = "PANTHEON_ORACLE_BYOK"
            mrr_pln = 199
            setup_fee_pln = 0
            pitch_hook = "Zero awarii JSON w zapytaniach LLM i 80% niższe koszty tokenów."

        return {
            "tier": tier,
            "monthly_pln": mrr_pln,
            "setup_pln": setup_fee_pln,
            "currency": "pln",
            "pitch_hook": pitch_hook
        }

    def generate_stripe_checkout_payload(self, company_name: str, email: str, deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tworzy specyfikację sesji Stripe Checkout gotową do wywołania API Stripe.
        """
        line_items = [
            {
                "price_data": {
                    "currency": deal["currency"],
                    "product_data": {
                        "name": f"W.F.P. Autonomiczny System AI — {deal['tier']}",
                        "description": deal["pitch_hook"],
                    },
                    "unit_amount": int(deal["monthly_pln"] * 100),
                    "recurring": {"interval": "month"}
                },
                "quantity": 1
            }
        ]

        if deal["setup_pln"] > 0:
            line_items.append({
                "price_data": {
                    "currency": deal["currency"],
                    "product_data": {
                        "name": "Wdrożenie & Konfiguracja Dedykowanego Agenta",
                    },
                    "unit_amount": int(deal["setup_pln"] * 100),
                },
                "quantity": 1
            })

        return {
            "customer_email": email,
            "payment_method_types": ["card", "blik", "p24"],
            "line_items": line_items,
            "mode": "subscription",
            "success_url": "https://antigravity.luch.dev/site/success?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": "https://antigravity.luch.dev/site/canceled",
            "metadata": {
                "company_name": company_name,
                "tier": deal["tier"]
            }
        }

    def compose_high_velocity_outreach(self, lead: Dict[str, Any], deal: Dict[str, Any]) -> str:
        """
        Generuje elitarny cold email z twardymi liczbami ze sprawozdania KRS i wezwaniem do płatności/demo.
        """
        return f"""Temat: Automatyzacja lejków w {lead['name']} (Analiza KRS NIP: {lead['nip']})

Dzień dobry,

Zgodnie z oficjalnym sprawozdaniem finansowym za ubiegły rok, {lead['name']} wygenerowała {lead['financial_kpi']['annual_revenue_pln']:,.0f} PLN przychodu oraz {lead['financial_kpi']['net_profit_pln']:,.0f} PLN zysku netto.

Tradycyjny zespół prospectingowy przy tej skali generuje wysoki koszt stały oraz błędy w danych. 

Przygotowaliśmy dla Państwa dedykowaną instancję W.F.P. Omega AI (zabezpieczoną bramką Pantheon Oracle), która:
1. Autonomicznie monitoruje nowe podmioty w KRS i grupy docelowe 24/7.
2. Przygotowuje personalizowane analizy wideo VSL przed pierwszym kontaktem.
3. Bezpośrednio kieruje decydentów do zindywidualizowanego panelu zamówień.

Pakiet wdrożeniowy dla Państwa skali: {deal['tier']} ({deal['monthly_pln']} PLN / miesięcznie).

Możemy uruchomić pilotaż w 48h. Czy możemy podesłać 2-minutowy materiał wideo obrazujący działanie na Państwa ofercie?

Z poważaniem,
W.F.P. Commercial Automation Group
hubi666hubi / Autonomous Systems
"""


def main():
    print("==================================================")
    print("   CASH ENGINE DISTRIBUTOR — RUNTIME TEST        ")
    print("==================================================")

    distributor = CashEngineDistributor()
    sample_lead = {
        "name": "Nordic Apex Logistics S.A.",
        "nip": "5833190281",
        "financial_kpi": {
            "annual_revenue_pln": 12_400_000.0,
            "net_profit_pln": 1_450_000.0
        }
    }

    deal = distributor.calculate_deal_size(sample_lead["financial_kpi"])
    print(f"\n[+] Zakwalifikowano: {deal['tier']}")
    print(f"    Miesięczny abonament: {deal['monthly_pln']} PLN | Setup fee: {deal['setup_pln']} PLN")

    payload = distributor.generate_stripe_checkout_payload(
        sample_lead["name"], "zarzad@nordicapex.pl", deal
    )
    print(f"\n[+] Przygotowano Stripe Checkout Payload: {len(payload['line_items'])} pozycje (Metody: Karta, BLIK, Przelewy24)")

    letter = distributor.compose_high_velocity_outreach(sample_lead, deal)
    print("\n--- TREŚĆ WYGENEROWANEGO PITCHU HANDLOWEGO ---")
    print(letter)


if __name__ == "__main__":
    main()
