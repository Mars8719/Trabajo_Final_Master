import json, urllib.request

resp = urllib.request.urlopen("http://localhost:8001/openapi.json")
d = json.loads(resp.read())
schemas = d.get("components", {}).get("schemas", {})
print("ALL SCHEMAS:")
for name in sorted(schemas.keys()):
    props = schemas[name].get("properties", {})
    req = schemas[name].get("required", [])
    print(f"\n  {name}:")
    for k, v in props.items():
        r = " *REQ*" if k in req else ""
        t = v.get("type", str(v.get("anyOf", v)))[:50]
        print(f"    {k}: {t}{r}")
