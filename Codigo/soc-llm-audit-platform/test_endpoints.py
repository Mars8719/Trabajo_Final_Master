"""End-to-end test of all API endpoints - using correct schemas"""
import urllib.request
import urllib.error
import json

BASE = "http://localhost:8001"

def req(method, path, data=None):
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(r, timeout=15)
        result = json.loads(resp.read())
        return resp.status, result
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        try:
            body_err = json.loads(body_err)
        except:
            pass
        return e.code, body_err

def test(name, method, path, data=None, expect=200):
    status, result = req(method, path, data)
    ok = "PASS" if status == expect else "FAIL"
    detail = ""
    if status != expect:
        detail = f" (got {status}, expected {expect}) -> {json.dumps(result, default=str)[:300]}"
    elif isinstance(result, dict):
        keys = list(result.keys())[:6]
        detail = f" keys={keys}"
    elif isinstance(result, list):
        detail = f" [{len(result)} items]"
    print(f"  [{ok}] {name}: {status}{detail}")
    return status == expect, result

results = []
print("\n" + "="*60)
print("SOC-LLM AUDIT PLATFORM - FULL ENDPOINT TEST")
print("="*60)

# 1. HEALTH
print("\n--- 1. HEALTH ---")
results.append(test("Health Check", "GET", "/health"))

# 2. DASHBOARD
print("\n--- 2. DASHBOARD ---")
results.append(test("Dashboard KPIs", "GET", "/api/v1/dashboard/kpis"))

# 3. ALERTS
print("\n--- 3. ALERTS ---")
ok, alert = test("Ingest Alert 1", "POST", "/api/v1/alerts/ingest", {
    "source": "SIEM-Splunk",
    "raw_payload": {
        "message": "Failed login from 192.168.1.100 user admin@empresa.com attempt 5",
        "host": "fw-01",
        "type": "authentication_failure"
    },
    "severity_original": "high"
}, expect=201)
results.append((ok, alert))
alert_id = alert.get("alert_id", alert.get("id", "")) if isinstance(alert, dict) else ""
print(f"    -> alert_id = {alert_id}")

ok, alert2 = test("Ingest Alert 2 (critical)", "POST", "/api/v1/alerts/ingest", {
    "source": "SIEM-QRadar",
    "raw_payload": {
        "message": "Malware detected on host 10.0.0.50 by john.doe@corp.com",
        "host": "ws-042",
        "type": "malware_detection"
    },
    "severity_original": "critical"
}, expect=201)
results.append((ok, alert2))
alert_id2 = alert2.get("alert_id", alert2.get("id", "")) if isinstance(alert2, dict) else ""

if alert_id:
    results.append(test("Get Alert Detail", "GET", f"/api/v1/alerts/{alert_id}"))
else:
    print("  [SKIP] Get Alert Detail (no alert_id)")

# 4. COMPLIANCE
print("\n--- 4. COMPLIANCE ---")
results.append(test("Compliance Scores", "GET", "/api/v1/compliance/scores"))
results.append(test("Compliance Dashboard", "GET", "/api/v1/compliance/dashboard"))
results.append(test("Compliance Trends", "GET", "/api/v1/compliance/trends"))

# 5. HITL
print("\n--- 5. HITL ---")
results.append(test("HITL Queue", "GET", "/api/v1/hitl/queue"))

if alert_id:
    results.append(test("HITL Decision", "POST", f"/api/v1/hitl/{alert_id}/decision", {
        "decision": "approved",
        "justification": "Confirmed true positive after log analysis and SHAP review",
        "alternatives_considered": {"option_b": "escalate to tier-2"},
        "shap_viewed": True,
        "lime_viewed": False
    }, expect=201))

# 6. AUDIT
print("\n--- 6. AUDIT ---")
results.append(test("Audit Trail", "GET", "/api/v1/audit/trail?limit=20"))
results.append(test("Verify Chain Integrity", "GET", "/api/v1/audit/verify"))
results.append(test("Export Audit", "GET", "/api/v1/audit/export"))

# 7. EXPLAINABILITY
print("\n--- 7. EXPLAINABILITY ---")
if alert_id:
    results.append(test("Explain Decision (XAI)", "GET", f"/api/v1/alerts/{alert_id}/explanation"))

# 8. DPIA
print("\n--- 8. DPIA ---")
ok, dpia = test("Generate DPIA", "POST", "/api/v1/dpia/generate", {
    "system_description": "SOC-LLM Triage Engine processes network security logs including IPs, usernames and threat indicators for automated incident classification using GPT-4",
    "include_data_flows": True,
    "include_risk_matrix": True
}, expect=201)
results.append((ok, dpia))
dpia_id = dpia.get("id", "") if isinstance(dpia, dict) else ""

results.append(test("List DPIAs", "GET", "/api/v1/dpia/list"))

if dpia_id:
    results.append(test("DPIA Risk Matrix", "GET", f"/api/v1/dpia/{dpia_id}/risk-matrix"))

# 9. INCIDENTS NIS2
print("\n--- 9. INCIDENTS (NIS2) ---")
ok, incident = test("Report Incident", "POST", "/api/v1/incidents/report", {
    "incident_type": "data_breach",
    "severity": "critical",
    "description": "Unauthorized access to customer database via anomalous query patterns. 500+ records exposed.",
    "alert_ids": [alert_id] if alert_id else [],
    "affected_services": {"primary": "customer-db", "secondary": "api-gateway"}
}, expect=201)
results.append((ok, incident))
incident_id = incident.get("id", "") if isinstance(incident, dict) else ""

results.append(test("List Incidents", "GET", "/api/v1/incidents/"))

if incident_id:
    results.append(test("Update Incident", "PUT", f"/api/v1/incidents/{incident_id}/update", {
        "status": "investigating",
        "detailed_report": {
            "root_cause": "SQL injection via unpatched API endpoint",
            "affected_records": 523,
            "containment_actions": ["blocked IP", "rotated credentials"]
        }
    }))

# 10. BIAS
print("\n--- 10. BIAS ---")
results.append(test("Run Bias Test", "POST", "/api/v1/bias/run", {
    "model_id": "llm-triage-v2",
    "test_type": "demographic_parity",
    "data": {
        "prompts": ["Alert from user Ahmed", "Alert from user John", "Alert from user Maria"],
        "expected_equal": True
    }
}, expect=201))
results.append(test("Get Bias Results", "GET", "/api/v1/bias/results"))

# 11. KILL SWITCH
print("\n--- 11. KILL SWITCH ---")
results.append(test("Activate Kill Switch", "POST", "/api/v1/hitl/kill-switch", {
    "reason": "Anomalous LLM behavior detected - safety override",
    "activated_by": "analyst-001"
}))
results.append(test("Deactivate Kill Switch", "POST", "/api/v1/hitl/kill-switch/deactivate", {
    "analyst_id": "analyst-001"
}))

# SUMMARY
print("\n" + "="*60)
passed = sum(1 for ok, _ in results if ok)
total = len(results)
pct = (passed / total * 100) if total > 0 else 0
print(f"RESULTS: {passed}/{total} passed ({pct:.0f}%)")
if passed == total:
    print("ALL TESTS PASSED!")
elif passed >= total * 0.8:
    print(f"MOSTLY PASSING - {total - passed} test(s) need attention")
else:
    print(f"NEEDS WORK - {total - passed} test(s) failed")
print("="*60)
