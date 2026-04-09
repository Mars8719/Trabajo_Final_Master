import json, sys, urllib.request

resp = urllib.request.urlopen("http://localhost:8001/openapi.json")
d = json.loads(resp.read())
schemas = d.get("components", {}).get("schemas", {})
for name in ["AlertIngest", "HITLDecisionRequest", "DPIARequest", "IncidentReport", "BiasTestRequest", "KillSwitchRequest"]:
    if name in schemas:
        props = schemas[name].get("properties", {})
        req = schemas[name].get("required", [])
        print(f"\n{name}:")
        for k, v in props.items():
            r = " *REQUIRED*" if k in req else ""
            t = v.get("type", str(v.get("anyOf", "?")))
            print(f"  {k}: {t}{r}")
    else:
        print(f"\n{name}: NOT FOUND")
