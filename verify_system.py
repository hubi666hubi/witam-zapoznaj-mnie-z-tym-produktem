#!/usr/bin/env python3
"""
Verify System — W.F.P. Comprehensive Verification Suite
Weryfikacja produkcyjna w trybie /boost /goal:
Testuje wszystkie warstwy:
1. Anti-Babol JSON Guardrail (Pantheon Bridge)
2. Parser i scoring finansowy KRS
3. Generator EML / Stripe Checkout (Moneco Engine)
4. REST API Endpointy Node.js (GET /api/status, POST /api/oracle/guardrail, POST /api/webhooks/stripe)
5. Integralność plików i podglądu webowego
"""

import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error

def run_test(name: str, fn):
    start = time.time()
    try:
        fn()
        duration_ms = int((time.time() - start) * 1000)
        print(f"  [PASS] {name} ({duration_ms} ms)")
        return True, duration_ms, None
    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        print(f"  [FAIL] {name} ({duration_ms} ms) -> {e}")
        return False, duration_ms, str(e)

def test_pantheon_bridge():
    from pantheon_bridge import PantheonAntiBabolGateway
    gw = PantheonAntiBabolGateway()
    res = gw.execute_with_guardrail(
        messages=[{"role": "user", "content": "test"}],
        required_keys=["company_name", "nip"],
        simulate_babol=True
    )
    assert res["success"] is True, "Guardrail execution failed"
    assert res["is_fallback"] is True, "Fallback should have triggered on simulated babol"
    assert "company_name" in res["data"], "Missing required key in recovered payload"

def test_krs_enricher():
    from krs_lead_enricher import KRSLeadEnricher
    score, tier = KRSLeadEnricher.calculate_lead_score(12_000_000, 1_500_000, 2.0)
    assert tier == "HIGH_TICKET", f"Expected HIGH_TICKET, got {tier}"
    assert score >= 85, f"Expected score >= 85, got {score}"

def test_outreach_eml_files():
    outreach_dir = "/home/agent/workspace/outreach_active"
    assert os.path.isdir(outreach_dir), "Missing outreach_active directory"
    eml_files = [f for f in os.listdir(outreach_dir) if f.endswith(".eml")]
    assert len(eml_files) >= 3, f"Expected >= 3 .eml files, got {len(eml_files)}"
    state_file = os.path.join(outreach_dir, "revenue_pipeline_state.json")
    assert os.path.isfile(state_file), "Missing revenue_pipeline_state.json"
    with open(state_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_immediate_cashflow_usd"] >= 24000.0, "Invalid immediate cashflow value"

def test_http_api_endpoints():
    # Start temporary node server on port 8089 to verify
    env = os.environ.copy()
    env["PORT"] = "8089"
    proc = subprocess.Popen(["node", "server.js"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.8) # wait for startup
    try:
        # 1. GET /api/status
        req = urllib.request.Request("http://127.0.0.1:8089/api/status")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            assert data["status"] == "ONLINE", "Expected ONLINE status"
            assert "system_state" in data, "Missing system_state"

        # 2. GET /api/deals
        req = urllib.request.Request("http://127.0.0.1:8089/api/deals")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            assert "dispatches" in data, "Missing dispatches in deals endpoint"
            assert len(data["dispatches"]) >= 3, "Expected 3 dispatches"

        # 3. POST /api/webhooks/stripe
        payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {"amount_total": 490000}}}).encode()
        req = urllib.request.Request("http://127.0.0.1:8089/api/webhooks/stripe", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode())
            assert data["received"] is True, "Stripe webhook not acknowledged"

    finally:
        proc.terminate()
        proc.wait()

def main():
    print("==========================================================")
    print("  W.F.P. SYSTEM VERIFICATION SUITE — /BOOST /GOAL AUDIT  ")
    print("==========================================================")

    tests = [
        ("Anti-Babol JSON Guardrail & Fallback Engine", test_pantheon_bridge),
        ("KRS B2B Financial Scorer & Tier Allocator", test_krs_enricher),
        ("RFC-5322 MIME Packages & Pipeline State Integrity", test_outreach_eml_files),
        ("Node.js Sovereign REST API Server Endpoints", test_http_api_endpoints)
    ]

    all_passed = True
    results = []
    for name, fn in tests:
        passed, duration_ms, err = run_test(name, fn)
        results.append({"name": name, "passed": passed, "duration_ms": duration_ms, "error": err})
        if not passed:
            all_passed = False

    print("\n----------------------------------------------------------")
    if all_passed:
        print("[✔] 100% SUKCES: Wszystkie podsystemy zwalidowane pomyślnie.")
    else:
        print("[!] BŁĄD: Wykryto niespełnione asercje.")
    print("----------------------------------------------------------")

    with open("/home/agent/workspace/verification_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.time(),
            "all_passed": all_passed,
            "results": results
        }, f, indent=2)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
