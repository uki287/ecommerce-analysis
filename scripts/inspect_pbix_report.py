"""Read-only inspection of a PBIX report definition (no modification)."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

PBIX = Path(sys.argv[1] if len(sys.argv) > 1 else r"F:\power bi\data-test-v2.pbix")


def load(z: zipfile.ZipFile, name: str):
    return json.loads(z.read(name).decode("utf-8"))


def role_refs(qs: dict) -> dict[str, list[str]]:
    out = {}
    for role, block in (qs or {}).items():
        refs = []
        for proj in block.get("projections", []):
            qr = proj.get("queryRef") or proj.get("field", {})
            refs.append(qr if isinstance(qr, str) else json.dumps(qr, ensure_ascii=False))
        out[role] = refs
    return out


def main() -> int:
    with zipfile.ZipFile(PBIX) as z:
        names = z.namelist()
        pages_json = load(z, "Report/definition/pages/pages.json")
        order = pages_json["pageOrder"]
        result = {
            "file": str(PBIX),
            "entries": len(names),
            "activePage": pages_json.get("activePageName"),
            "pages": [],
        }
        for pid in order:
            page = load(z, f"Report/definition/pages/{pid}/page.json")
            prefix = f"Report/definition/pages/{pid}/visuals/"
            vids = sorted({n[len(prefix):].split("/")[0] for n in names if n.startswith(prefix)})
            visuals = []
            for vid in vids:
                v = load(z, f"{prefix}{vid}/visual.json")
                vis = v.get("visual", {})
                title = None
                try:
                    title = vis["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
                except Exception:
                    title = None
                visuals.append(
                    {
                        "id": vid,
                        "type": vis.get("visualType"),
                        "title": title,
                        "roles": role_refs(vis.get("query", {}).get("queryState")),
                        "filters": bool(v.get("filterConfig")),
                        "objects": list((vis.get("objects") or {}).keys()),
                        "pos": v.get("position"),
                    }
                )
            result["pages"].append(
                {
                    "id": pid,
                    "name": page.get("displayName"),
                    "filters": bool(page.get("filterConfig")),
                    "visuals": visuals,
                }
            )
    out = Path(r"E:\workbuddy-space\ecommerce-analysis\report\pbix_v2_structure.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("written:", out)
    for p in result["pages"]:
        print(f"{p['name']} | {len(p['visuals'])} visual(s)")
        for v in p["visuals"]:
            print(f"   - {v['type']} | {v['title']!r} | roles={list(v['roles'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())