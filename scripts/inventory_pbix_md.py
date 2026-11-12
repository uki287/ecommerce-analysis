"""Produce a readable Markdown inventory of a PBIX report (read-only)."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

PBIX = Path(sys.argv[1] if len(sys.argv) > 1 else r"F:\power bi\data-test-v2.pbix")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else r"E:\workbuddy-space\ecommerce-analysis\report\pbix_v2_inventory.md")


def load(z, name):
    return json.loads(z.read(name).decode("utf-8"))


def refs(block):
    out = []
    for proj in block.get("projections", []):
        qr = proj.get("queryRef")
        agg = proj.get("field", {}).get("Aggregation")
        if qr:
            out.append(qr)
        elif agg:
            out.append(json.dumps(agg, ensure_ascii=False))
        else:
            out.append(json.dumps(proj.get("field", {}), ensure_ascii=False))
    return out


def main() -> int:
    lines: list[str] = []
    with zipfile.ZipFile(PBIX) as z:
        names = z.namelist()
        pages_meta = load(z, "Report/definition/pages/pages.json")
        lines.append(f"# {PBIX.name} 结构清单")
        lines.append("")
        lines.append(f"- zip 条目：{len(names)}")
        lines.append(f"- 页面数：{len(pages_meta['pageOrder'])}")
        lines.append(f"- 默认活动页：`{pages_meta.get('activePageName')}`")
        lines.append("")

        for pid in pages_meta["pageOrder"]:
            page = load(z, f"Report/definition/pages/{pid}/page.json")
            lines.append(f"## {page.get('displayName')}  ·  `{pid}`")
            filters = page.get("filterConfig", {}).get("filters", []) if page.get("filterConfig") else []
            lines.append(f"- 页面尺寸：{page.get('width')}×{page.get('height')}，displayOption={page.get('displayOption')}")
            lines.append(f"- 页面筛选器：{len(filters)}")
            prefix = f"Report/definition/pages/{pid}/visuals/"
            vids = sorted({n[len(prefix):].split('/')[0] for n in names if n.startswith(prefix)})
            lines.append(f"- 视觉对象：{len(vids)}")
            for vid in vids:
                v = load(z, f"{prefix}{vid}/visual.json")
                vis = v.get("visual", {})
                title = None
                try:
                    title = vis["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
                except Exception:
                    pass
                pos = v.get("position", {})
                lines.append("")
                lines.append(f"### {vis.get('visualType')} `{vid[:8]}`")
                if title:
                    lines.append(f"- 标题：{title}")
                lines.append(
                    f"- 位置：x={pos.get('x')} y={pos.get('y')} w={pos.get('width')} h={pos.get('height')}"
                )
                qs = vis.get("query", {}).get("queryState", {})
                for role, block in qs.items():
                    lines.append(f"- {role}: " + ", ".join(f"`{r}`" for r in refs(block)))
                sort = vis.get("query", {}).get("sortDefinition")
                if sort:
                    for s in sort.get("sort", []):
                        lines.append(f"- 排序：`{s.get('direction')}` on {json.dumps(s.get('field'), ensure_ascii=False)}")
                objs = vis.get("objects") or {}
                if objs:
                    lines.append(f"- 格式对象：{', '.join(objs)}")
                if v.get("filterConfig"):
                    lines.append(f"- 视觉筛选器：{len(v['filterConfig'].get('filters', []))}")
            lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("written:", OUT, len(lines), "lines")
    return 0


if __name__ == "__main__":
    sys.exit(main())