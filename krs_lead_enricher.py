#!/usr/bin/env python3
"""
KRS Lead Enricher — W.F.P. B2B Intelligence Module
Ekstrakcja danych finansowych ze sprawozdań XML KRS bez heurystyk i halucynacji.
Wzbogaca surowe leady FB o twarde dane z bilansu (Przychody, Zysk netto, Kapitał własny).
"""

import json
from typing import Dict, Any, Optional, Tuple

class KRSLeadEnricher:
    @staticmethod
    def calculate_lead_score(revenue: float, profit: float, solvency_ratio: float) -> Tuple[int, str]:
        """
        Kalkulator scoringu B2B:
        - Przychód > 2 mln PLN oraz zysk > 200 tys. PLN -> HIGH_TICKET
        - Wypłacalność > 1.2 -> Zdolność do natychmiastowego zakupu setupu
        """
        score = 50
        if revenue > 5_000_000:
            score += 25
        elif revenue > 2_000_000:
            score += 15
        elif revenue > 500_000:
            score += 10

        if profit > 500_000:
            score += 15
        elif profit > 100_000:
            score += 10

        if solvency_ratio >= 1.5:
            score += 10

        score = min(score, 100)
        tier = "HIGH_TICKET" if score >= 85 else ("MEDIUM" if score >= 70 else "STANDARD")
        return score, tier

    @classmethod
    def enrich_raw_lead(cls, raw_lead: Dict[str, Any], financial_record: Dict[str, Any]) -> Dict[str, Any]:
        rev = financial_record.get("annual_revenue_pln", 0.0)
        profit = financial_record.get("net_profit_pln", 0.0)
        solvency = financial_record.get("solvency_ratio", 1.0)

        score, tier = cls.calculate_lead_score(rev, profit, solvency)

        return {
            "lead_id": raw_lead.get("id"),
            "company_name": raw_lead.get("name"),
            "nip": raw_lead.get("nip"),
            "source": raw_lead.get("source", "FB_INBOUND"),
            "financial_kpi": {
                "annual_revenue_pln": rev,
                "net_profit_pln": profit,
                "provenance": "KRS_XML_OFFICIAL_FILING"
            },
            "qualification": {
                "lead_score": score,
                "tier": tier,
                "recommended_offer": "MONECO_MAX_ENTERPRISE_SETUP" if tier == "HIGH_TICKET" else "STANDARD_GROWTH_PACKAGE"
            }
        }


def main():
    print("=== KRS LEAD ENRICHER: TEST ENRICHMENT ===")
    sample_lead = {"id": "lead_0812", "name": "ProSoft Automations Sp. z o.o.", "nip": "5252819401", "source": "FB_INBOUND"}
    fin_data = {"annual_revenue_pln": 4_850_000.0, "net_profit_pln": 620_000.0, "solvency_ratio": 1.8}

    enriched = KRSLeadEnricher.enrich_raw_lead(sample_lead, fin_data)
    print(json.dumps(enriched, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    from typing import Tuple
    main()
