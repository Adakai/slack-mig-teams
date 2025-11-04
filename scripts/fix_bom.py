import io, json, sys
p = "mapping.json"
raw = io.open(p, "r", encoding="utf-8-sig").read()   # accepts BOM if present
obj = json.loads(raw)                                  # validate JSON
io.open(p, "w", encoding="utf-8").write(
    json.dumps(obj, ensure_ascii=False, indent=2)
)
print("Rewrote mapping.json without BOM.")
