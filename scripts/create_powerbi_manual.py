# -*- coding: utf-8 -*-
"""Build the Chinese Power BI operation manual (DOCX)."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "report" / "PowerBI操作手册.docx"
PREVIEW = ROOT / "report" / "figures" / "manual_preview.png"

FONT = "Microsoft YaHei"
MONO = "Consolas"
BLUE = RGBColor(0x1F, 0x4E, 0x79)
TEAL = RGBColor(0x2A, 0x9D, 0x8F)
DARK = RGBColor(0x1F, 0x29, 0x37)
GRAY = RGBColor(0x6B, 0x72, 0x80)
RED = RGBColor(0xE7, 0x6F, 0x51)
LIGHT_BLUE = "EAF2F8"
LIGHT_GRAY = "F3F4F6"
HEADER_BLUE = "1F4E79"


def set_run_font(run, name=FONT, size=10.5, bold=None, color=None, mono=False):
    font_name = MONO if mono else name
    run.font.name = font_name
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font_name)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=50, start=80, bottom=50, end=80):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for tag, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{tag}"))
        if node is None:
            node = OxmlElement(f"w:{tag}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_text(cell, text, bold=False, size=9, color=DARK, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(str(text))
    set_run_font(run, size=size, bold=bold, color=color)


def set_col_widths(table, widths_cm):
    table.autofit = False
    for row in table.rows:
        for idx, width in enumerate(widths_cm):
            row.cells[idx].width = Cm(width)


def add_table(doc, headers, rows, widths_cm, font_size=8.5, header_fill=HEADER_BLUE):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    table.autofit = False

    hdr = table.rows[0]
    for idx, header in enumerate(headers):
        cell = hdr.cells[idx]
        set_cell_shading(cell, header_fill)
        set_cell_margins(cell)
        set_cell_text(cell, header, bold=True, size=font_size, color=RGBColor(0xFF, 0xFF, 0xFF))
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    tr_pr = hdr._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)

    for row_data in rows:
        row = table.add_row()
        for idx, value in enumerate(row_data):
            cell = row.cells[idx]
            set_cell_margins(cell)
            set_cell_text(cell, value, size=font_size)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    set_col_widths(table, widths_cm)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_para(doc, text, size=10.5, bold=False, color=DARK, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.35
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    return p


def add_lead(doc, lead, body):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.35
    r1 = p.add_run(lead)
    set_run_font(r1, size=10.5, bold=True, color=BLUE)
    r2 = p.add_run(body)
    set_run_font(r2, size=10.5)
    return p


def add_bullets(doc, items, size=10.2):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.3
        run = p.add_run(item)
        set_run_font(run, size=size)


def add_steps(doc, items, size=10.2):
    for idx, item in enumerate(items, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.45)
        p.paragraph_format.first_line_indent = Cm(-0.45)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.3
        r1 = p.add_run(f"{idx}. ")
        set_run_font(r1, size=size, bold=True, color=TEAL)
        r2 = p.add_run(item)
        set_run_font(r2, size=size)


def add_code(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.25)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_together = True
    p_pr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), LIGHT_GRAY)
    p_pr.append(shd)
    lines = text.strip("\n").split("\n")
    for idx, line in enumerate(lines):
        if idx:
            p.add_run().add_break()
        run = p.add_run(line)
        set_run_font(run, size=8.5, mono=True, color=RGBColor(0x11, 0x18, 0x27))
    return p


def add_note(doc, title, text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    cell = table.cell(0, 0)
    set_cell_shading(cell, LIGHT_BLUE)
    set_cell_margins(cell, top=100, start=140, bottom=100, end=140)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(title)
    set_run_font(r, size=9.5, bold=True, color=BLUE)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(text)
    set_run_font(r2, size=9.3, color=DARK)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        set_run_font(run, size=(17 if level == 1 else 13 if level == 2 else 11.5), bold=True, color=BLUE)
    h.paragraph_format.space_before = Pt(10 if level == 1 else 8)
    h.paragraph_format.space_after = Pt(5)
    h.paragraph_format.keep_with_next = True
    return h


def add_page_number(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)
    set_run_font(run, size=8, color=GRAY)


def setup_document() -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(1.9)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)

    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(5)

    for level, size, color in (
        (1, 17, BLUE),
        (2, 13, BLUE),
        (3, 11.5, TEAL),
    ):
        style = doc.styles[f"Heading {level}"]
        style.font.name = FONT
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    header = section.header.paragraphs[0]
    header.text = ""
    hr = header.add_run("Olist 电商数据 · Power BI 图表操作手册")
    set_run_font(hr, size=8, color=GRAY)
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = footer.add_run("第 ")
    set_run_font(fr, size=8, color=GRAY)
    add_page_number(footer)
    fr2 = footer.add_run(" 页  |  数据口径见 report/analysis_guide.md")
    set_run_font(fr2, size=8, color=GRAY)

    doc.core_properties.title = "Olist 电商数据 Power BI 图表操作手册"
    doc.core_properties.author = "Olist 数据分析项目"
    doc.core_properties.subject = "Power BI 10 张图表复刻步骤"
    return doc


def cover(doc: Document):
    # Top blue band
    band = doc.add_table(rows=1, cols=1)
    band.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = band.cell(0, 0)
    set_cell_shading(cell, HEADER_BLUE)
    cell.height = Cm(0.45)
    cell.text = ""

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(45)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("Olist 电商数据")
    set_run_font(r, size=27, bold=True, color=BLUE)

    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(10)
    r2 = p2.add_run("Power BI 图表操作手册")
    set_run_font(r2, size=25, bold=True, color=DARK)

    p3 = doc.add_paragraph()
    p3.paragraph_format.space_after = Pt(32)
    r3 = p3.add_run("用中文数据底表复刻 10 张图表 · 从导入到发布")
    set_run_font(r3, size=12, color=TEAL, bold=True)

    meta = doc.add_table(rows=4, cols=2)
    meta.alignment = WD_TABLE_ALIGNMENT.LEFT
    meta.autofit = False
    rows = [
        ("适用对象", "需要在 Power BI 中制作中文经营看板的数据分析/BI 人员"),
        ("数据来源", "report/tables_zh/ 与 data/processed_zh/"),
        ("目标效果", "report/Olist_10_charts.html、report/figures/"),
        ("版本 / 日期", "v1.0 / 2026-11-11"),
    ]
    for idx, (k, v) in enumerate(rows):
        set_cell_margins(meta.cell(idx, 0))
        set_cell_margins(meta.cell(idx, 1))
        set_cell_text(meta.cell(idx, 0), k, bold=True, size=9.5, color=GRAY)
        set_cell_text(meta.cell(idx, 1), v, size=9.5)
    set_col_widths(meta, [3.0, 12.5])

    doc.add_paragraph()
    add_note(
        doc,
        "先读这一句",
        "Power BI 原生能完成 8 张图；箱线图和雷达图需要从 AppSource 安装自定义视觉对象。"
        "如果公司租户禁用了自定义视觉对象，手册里给了原生替代方案。建议先做「快速版」，"
        "确认 10 张图都能出效果，再升级为可交叉筛选的「完整版」。",
    )

    p4 = doc.add_paragraph()
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p4.paragraph_format.space_before = Pt(18)
    r4 = p4.add_run("本手册假定你使用 Windows 版 Power BI Desktop；所有路径均为项目内相对路径。")
    set_run_font(r4, size=8.5, color=GRAY)
    doc.add_page_break()


def contents(doc: Document):
    add_heading(doc, "手册结构", 1)
    rows = [
        ("1", "准备工作", "文件位置、编码、区域设置、目标效果"),
        ("2", "导入数据", "Text/CSV、Power Query 类型设置、导入校验"),
        ("3", "快速版模型", "预聚合表、日期表、页面设置、主题"),
        ("4", "10 张图逐步操作", "字段井、筛选、排序、格式化、DAX"),
        ("5", "完整版模型", "事实/维度关系、DAX 度量值、交互"),
        ("6", "统一视觉规范", "颜色、字体、百分比、标题、tooltip"),
        ("7", "页面布局", "4 页看板的组件摆放与尺寸"),
        ("8", "发布与刷新", "保存、发布、OneDrive/SharePoint、网关"),
        ("9", "常见问题", "乱码、日期、地图、Top N、重复计数"),
        ("10", "验收清单", "交付前逐项检查"),
    ]
    add_table(doc, ["章", "内容", "你会得到什么"], rows, [1.2, 4.0, 11.5], font_size=9)
    add_para(
        doc,
        "建议阅读顺序：第 1–3 章建立环境；第 4 章按图逐张操作；第 5 章再决定是否升级完整模型；"
        "第 6–8 章统一风格和发布。时间紧时可以直接看第 4 章的「快速版」步骤。",
    )
    doc.add_page_break()


def chapter_1(doc: Document):
    add_heading(doc, "1. 准备工作", 1)
    add_heading(doc, "1.1 软件与显示环境", 2)
    add_bullets(
        doc,
        [
            "Power BI Desktop：Windows 版，建议 2023 年之后的版本；本文以「获取数据 → 文本/CSV」和「折线和簇状柱形图」为准。",
            "中文字体：Microsoft YaHei（微软雅黑）。如果公司电脑没有，用 SimHei 也可；不要用只支持英文的字体。",
            "浏览器：用于打开 report/Olist_10_charts.html 对照最终效果。",
            "可选：AppSource 访问权限，用于「Box and Whisker」和「Radar Chart」两个自定义视觉对象。",
        ],
    )

    add_heading(doc, "1.2 把数据放到稳定位置", 2)
    add_para(
        doc,
        "Power BI 会记住 CSV 的本地路径。不要把数据留在临时下载目录，也不要在导入后移动文件。"
        "建议把 report/tables_zh 和 data/processed_zh 复制到一个固定目录，例如：",
    )
    add_code(
        doc,
        "D:\\PowerBI\\Olist\\data\\tables_zh\\\n"
        "D:\\PowerBI\\Olist\\data\\processed_zh\\",
    )
    add_note(
        doc,
        "路径建议",
        "路径中可以有中文，但不要有会频繁变化的临时目录。导入后如果移动了 CSV，Power BI 会提示找不到源，"
        "需要在「数据源设置」里改路径。发布到云端后，本地路径不能自动刷新；第 8 章会讲 OneDrive/SharePoint 方案。",
    )

    add_heading(doc, "1.3 关键文件与粒度", 2)
    rows = [
        ("monthly_kpis_zh", "20", "月", "月度 GMV、订单、客单价、迟到率"),
        ("category_kpis_zh", "74", "品类", "品类 GMV、评分、迟到率"),
        ("payment_type_kpis_zh", "4", "支付方式", "支付金额占比"),
        ("state_kpis_zh", "27", "州", "州级 GMV、地图、雷达图"),
        ("delivery_distribution_zh", "7", "送达时长区间", "送达分布"),
        ("seller_kpis_zh", "3,068", "卖家", "帕累托、卖家排名"),
        ("cohort_retention_wide_zh", "20", "首购月份", "Cohort 热力图"),
        ("order_category_zh", "99,470", "订单-品类", "箱线图、品类金额分布"),
        ("orders_master_zh", "99,441", "订单", "完整版事实表、直方图分箱"),
        ("customer_rfm_zh", "94,703", "客户", "客户维度、RFM 下钻"),
    ]
    add_table(doc, ["文件（不含 .csv）", "行数", "粒度", "主要用途"], rows, [5.3, 1.8, 3.0, 6.7], font_size=8.8)
    add_para(
        doc,
        "快速版先导入前 8 个文件即可；orders_master_zh 和 customer_rfm_zh 留给完整版。"
        "所有文件都是 UTF-8 with BOM，金额单位是巴西雷亚尔（BRL），比例字段是 0–1 小数。",
    )

    add_heading(doc, "1.4 Power BI 初始设置", 2)
    add_steps(
        doc,
        [
            "打开 Power BI Desktop，先不要建视觉对象。",
            "文件 → 选项和设置 → 选项 → 当前文件 → 区域设置：选择「中文（简体，中国）」。",
            "数据加载 → 时间智能 → 自动日期/时间：建议关闭。后面会自建日期表，避免每张表自动生成隐藏日期表。",
            "数据加载 → 数据源设置：确认没有旧的 CSV 路径残留。",
            "视图 → 主题 → 浏览主题：选择 dashboard/olist_theme.json；如果暂时不导入，第 6 章有手动配色。",
        ],
    )
    add_note(
        doc,
        "关于区域设置",
        "本数据的小数点是「.」，不是巴西常用的逗号。导入时将「文件原始格式」设为 65001，"
        "并在 Power Query 里对金额列使用「使用区域设置」→「中文（简体，中国）」；不要选会改变小数点含义的区域。",
    )
    doc.add_page_break()


def chapter_2(doc: Document):
    add_heading(doc, "2. 导入数据", 1)
    add_heading(doc, "2.1 逐个导入 CSV（推荐）", 2)
    add_steps(
        doc,
        [
            "主页 → 获取数据 → 文本/CSV。",
            "选择 report/tables_zh/monthly_kpis_zh.csv（或复制后的固定路径）。",
            "预览窗口：文件原始格式选「65001: Unicode (UTF-8)」，分隔符选「逗号」。",
            "点「转换数据」进入 Power Query，先不要直接「加载」。",
            "在 Power Query 里检查：第一行是否为标题、列名是否为中文、是否有空行、数字列是否被识别为文本。",
            "右键查询 → 重命名，改成业务名，例如「月度KPI」「品类KPI」「支付KPI」「州KPI」「配送分布」「卖家KPI」「Cohort宽表」「订单品类」。",
            "关闭并应用。",
            "重复以上步骤导入其余表。导入后可在「模型」视图检查表名和字段名。",
        ],
    )
    add_para(
        doc,
        "如果表很多，可以用「获取数据 → 文件夹」批量读取，但 28 张表结构不同，"
        "批量合并会产生大量 null 列。更稳妥的做法是只导入本页需要的 8 张表，"
        "或者用「数据流/SharePoint 文件夹」做统一数据源。",
    )

    add_heading(doc, "2.2 列类型与格式", 2)
    rows = [
        ("月份", "文本", "保持 YYYY-MM；另建月份序号用于排序"),
        ("商品GMV / 商品金额 / 运费 / 客单价", "小数（固定十进制）", "格式 R$ #,##0.00"),
        ("有效订单数 / 订单数 / 客户数 / 商品件数", "整数", "格式 #,##0"),
        ("迟到率 / 准时率 / 复购率 / GMV占比", "小数（固定十进制）", "格式 0.0%"),
        ("评论分 / 平均评论分", "小数（固定十进制）", "格式 0.00"),
        ("州 / 品类 / 支付方式 / 送达时长区间", "文本", "不要转成数字；区间列后面做自定义排序"),
        ("卖家ID / 商品ID / 订单ID / 客户唯一ID", "文本", "ID 不能转成数字，否则前导零/长哈希会丢"),
        ("首购月份", "文本", "Cohort 行标签，保持 YYYY-MM"),
    ]
    add_table(doc, ["列", "Power BI 类型", "说明"], rows, [6.5, 4.2, 6.1], font_size=8.8)

    add_heading(doc, "2.3 导入后的三个校验", 2)
    add_steps(
        doc,
        [
            "看行数：monthly_kpis_zh=20、category_kpis_zh=74、state_kpis_zh=27、payment_type_kpis_zh=4、seller_kpis_zh=3,068。",
            "看总额：有效订单数合计 97,905；商品GMV 合计 13,449,529.68；支付金额合计 15,686,469.07（支付表口径不同，不能和 GMV 直接相等）。",
            "看中文：品类、州、支付方式、订单状态是否为中文；如果出现乱码，回到数据源把编码改成 65001 重新导入。",
        ],
    )
    add_note(
        doc,
        "不要在这一步做汇总",
        "这些 CSV 已经是聚合表。导入后不要再按「月份」或「品类」做一次 Group By，否则会把订单数/金额重复汇总。"
        "只有 orders_master_zh、order_category_zh 这类明细才适合在 Power Query 里继续筛选/分箱。",
    )
    doc.add_page_break()


def chapter_3(doc: Document):
    add_heading(doc, "3. 快速版模型：先让 10 张图跑起来", 1)
    add_heading(doc, "3.1 快速版的原则", 2)
    add_bullets(
        doc,
        [
            "一页只用一个主表：月度页用「月度KPI」；品类页用「品类KPI」；支付页用「支付KPI」；地图/雷达用「州KPI」；Cohort 用「Cohort宽表」。",
            "不要急着把 8 张聚合表全部连起来。它们粒度不同，硬连会产生多对多和重复计数。",
            "快速版不支持跨页统一筛选，但能在 1–2 小时内复刻 10 张图；确认视觉和口径后，再做完整版。",
        ],
    )

    add_heading(doc, "3.2 建立日期表（推荐）", 2)
    add_para(doc, "建模 → 新建表，输入以下 DAX。即使快速版只在月度页使用，也建议先建好，后面完整版直接复用。")
    add_code(
        doc,
        "日期表 =\n"
        "ADDCOLUMNS(\n"
        "    CALENDAR ( DATE ( 2017, 1, 1 ), DATE ( 2018, 8, 31 ) ),\n"
        "    \"年\", YEAR ( [Date] ),\n"
        "    \"月份\", FORMAT ( [Date], \"YYYY-MM\" ),\n"
        "    \"月份序号\", YEAR ( [Date] ) * 100 + MONTH ( [Date] ),\n"
        "    \"月名\", FORMAT ( [Date], \"m月\" )\n"
        ")",
    )
    add_steps(
        doc,
        [
            "选中「日期表」→ 表工具 → 标记为日期表 → 日期列选 Date。",
            "如果月度KPI表需要按日期切片，新建计算列：月份首日 = DATEVALUE ( '月度KPI'[月份] & \"-01\" )。",
            "建立关系：日期表[Date] 1 → * 月度KPI[月份首日]（或直接连订单事实的下单日期）。",
            "选中「月份」列 → 按列排序 → 月份序号，避免按字母排序。",
        ],
    )

    add_heading(doc, "3.3 页面与主题", 2)
    add_steps(
        doc,
        [
            "视图 → 页面视图 → 实际大小；页面设置选 16:9（1280×720）。",
            "画布背景设为 #F7F9FC；页面顶部放一个 #1F4E79 的矩形作为标题栏。",
            "视图 → 主题 → 浏览主题，导入 dashboard/olist_theme.json；或按第 6 章手动设置颜色。",
            "插入 → 文本框：标题「Olist 经营分析」；右下角放数据来源「数据：2017-01 至 2018-08」。",
            "建议建立 4 个页面：经营总览、品类商品、履约体验、客户与卖家；每页 2–3 张图 + 切片器。",
        ],
    )
    add_note(
        doc,
        "快速版不需要关系",
        "如果只做单页图表，选中视觉对象后直接拖字段即可，不必在模型里连线。"
        "一旦你要让「州」切片器同时过滤月度、品类、支付三张表，就必须进入完整版，用订单事实表或共享维度表。",
    )
    doc.add_page_break()


def chapter_4(doc: Document):
    add_heading(doc, "4. 10 张图逐步操作（快速版）", 1)
    add_para(
        doc,
        "每张图按「视觉对象 → 字段井 → 筛选/排序 → 格式化 → 常见问题」五步做。"
        "字段名用中文表里的列名；如果你的 Power BI 显示的是英文表，请先导入 tables_zh。",
    )

    # 4.1
    add_heading(doc, "4.1 图 1：月度 GMV 与有效订单（双轴组合图）", 2)
    add_table(
        doc,
        ["字段井", "字段"],
        [
            ("X 轴", "月份"),
            ("列 Y 轴", "商品GMV"),
            ("行 Y 轴", "有效订单数"),
            ("工具提示", "客单价、迟到率、平均评论分"),
        ],
        [4.5, 12.0],
        font_size=9,
    )
    add_steps(
        doc,
        [
            "视觉对象 → 折线和簇状柱形图。",
            "把「月份」拖到 X 轴，「商品GMV」拖到列 Y 轴，「有效订单数」拖到行 Y 轴。",
            "格式 → Y 轴 → 打开「次坐标轴」；列轴单位设为百万，行轴单位设为千。",
            "格式 → 数据颜色：柱 #1F4E79，线 #F4A261；线宽 2.5，标记打开。",
            "格式 → X 轴 → 连续/分类按月份序号排序；如果月份是文本，先按「月份序号」排序。",
            "标题写成「月度 GMV 与有效订单：2017-11 为峰值」；关闭图例或放顶部一行。",
        ],
    )
    add_para(
        doc,
        "如果柱和线都用了同一张月度表，不需要关系；如果使用完整版订单事实表，"
        "X 轴改用日期表的「月份」，度量值用第 5 章的 DAX。",
    )

    # 4.2
    add_heading(doc, "4.2 图 2：品类 GMV Top 10（横向条形图）", 2)
    add_table(
        doc,
        ["字段井", "字段"],
        [
            ("Y 轴", "品类"),
            ("X 轴", "商品GMV"),
            ("工具提示", "GMV占比、有效订单数、评论分、迟到率"),
        ],
        [4.5, 12.0],
        font_size=9,
    )
    add_steps(
        doc,
        [
            "视觉对象 → 簇状条形图。",
            "把「品类」放 Y 轴，「商品GMV」放 X 轴。",
            "筛选器 → 品类 → 筛选类型「Top N」→ 显示前 10 项 → 按「商品GMV」降序。",
            "视觉对象右上角 → 排序 → 按商品GMV降序；如果是横向条形图，默认从下往上，勾选「按值排序」后检查方向。",
            "格式 → 数据标签 → 打开，显示单位「百万」或自定义格式 R$#,##0.00。",
            "格式 → 条形 → 圆角 2px；颜色用深蓝到浅蓝渐变（第 6 章给色值）。",
        ],
    )
    add_note(
        doc,
        "Top N 是在视觉对象筛选器里做",
        "不要用 DAX 过滤表；在视觉对象筛选器里对「品类」设置 Top N，才能保留其他页面的完整数据。",
    )

    # 4.3
    add_heading(doc, "4.3 图 3：支付金额构成（环形图）", 2)
    add_table(
        doc,
        ["字段井", "字段"],
        [
            ("图例", "支付方式"),
            ("值", "支付金额"),
            ("工具提示", "支付金额占比、订单数"),
        ],
        [4.5, 12.0],
        font_size=9,
    )
    add_steps(
        doc,
        [
            "视觉对象 → 环形图。",
            "「支付方式」放图例，「支付金额」放值。",
            "格式 → 详细信息标签 → 打开，标签内容选「类别、百分比」；小数位 1。",
            "格式 → 环 → 内径 65%–70%；图例放右侧。",
            "在环形图中心叠一个「卡片图」：度量值 = SUM('支付KPI'[支付金额])，背景透明，标题「支付总额」。",
            "如果图例太挤，把图例放右侧并调整字号 9；不要把四个小切片都塞进环内。",
        ],
    )
    add_note(
        doc,
        "不要用订单占比画饼图",
        "一笔订单可能同时有信用卡 + 代金券，订单占比相加会超过 100%。环形图用「支付金额」，不要用「订单占比」。",
    )

    # 4.4
    add_heading(doc, "4.4 图 4：品类规模、评分与迟到率（气泡散点图）", 2)
    add_table(
        doc,
        ["字段井", "字段"],
        [
            ("X 轴", "商品GMV"),
            ("Y 轴", "评论分"),
            ("大小", "有效订单数"),
            ("详细信息", "品类"),
            ("图例", "迟到率分组（需新建）"),
            ("工具提示", "GMV占比、迟到率、有效订单数"),
        ],
        [4.5, 12.0],
        font_size=9,
    )
    add_code(
        doc,
        "迟到率分组 =\n"
        "SWITCH (\n"
        "    TRUE (),\n"
        "    '品类KPI'[迟到率] < 0.05, \"低于5%\",\n"
        "    '品类KPI'[迟到率] < 0.08, \"5%-8%\",\n"
        "    '品类KPI'[迟到率] < 0.11, \"8%-11%\",\n"
        "    \"11%以上\"\n"
        ")",
    )
    add_steps(
        doc,
        [
            "先建计算列「迟到率分组」（上方 DAX），或回到 Power Query 加条件列。",
            "视觉对象 → 散点图；X 轴商品GMV，Y 轴评论分，大小有效订单数，详细信息品类，图例迟到率分组。",
            "筛选器 → 有效订单数 ≥ 30，去掉只有 1–2 单的长尾品类。",
            "格式 → X 轴 → 对数刻度；Y 轴范围 3.6–4.8。",
            "分析窗格 → 添加中位数线（X 和 Y 各一条），颜色灰、虚线。",
            "Power BI 原生散点图不支持连续颜色渐变；用「迟到率分组」图例表达颜色，工具提示里保留具体迟到率。",
        ],
    )

    # 4.5
    add_heading(doc, "4.5 图 5：州级 GMV 与迟到率（地理气泡图）", 2)
    add_table(
        doc,
        ["字段井", "字段"],
        [
            ("位置", "州"),
            ("纬度", "客户纬度"),
            ("经度", "客户经度"),
            ("大小", "商品GMV"),
            ("颜色饱和度", "迟到率"),
            ("工具提示", "有效订单数、准时率、平均送达天数"),
        ],
        [4.5, 12.0],
        font_size=9,
    )
    add_steps(
        doc,
        [
            "视觉对象 → 地图（Map）；如果只需要填色，用「着色地图」。",
            "把「州」放位置，纬度/经度分别放「客户纬度」「客户经度」；大小商品GMV，颜色饱和度迟到率。",
            "建模 → 选中「州」列 → 数据类别 → 州或省；如果地图不识别中文州名，优先用经纬度。",
            "新建计算列「国家」= \"巴西\"，放到地图的「国家/地区」字段（如果视觉对象有该字段）。",
            "格式 → 地图主题 → 灰度/浅色；气泡透明度 20%；颜色图例放右下。",
            "如果公司禁用了 Bing 地图，改用「散点图」：X=客户经度，Y=客户纬度，大小=商品GMV，图例=迟到率分组。",
        ],
    )

    # 4.6
    add_heading(doc, "4.6 图 6：送达天数分布（直方图）", 2)
    add_para(
        doc,
        "最快做法：用已聚合的「配送分布」表画柱状图；如果要真正的逐单直方图，用「订单事实」表分箱。",
    )
    add_table(
        doc,
        ["方案", "表", "字段", "适合"],
        [
            ("A 快速", "delivery_distribution_zh", "送达时长区间 / 订单数", "汇报页、快速复刻"),
            ("B 真直方图", "orders_master_zh", "送达天数（分箱）", "需要自定义箱宽"),
        ],
        [3.0, 5.5, 5.0, 3.5],
        font_size=9,
    )
    add_steps(
        doc,
        [
            "方案 A：簇状柱形图，X=送达时长区间，Y=订单数；按自定义顺序排序（0-3天 → 60天以上）。",
            "方案 A：添加平均线/中位线用「分析」窗格，或直接用卡片图展示中位数 10.2 天、P90 22.9 天。",
            "方案 B：导入 orders_master_zh；筛选「是否送达」= 是。",
            "方案 B：建模 → 新建列，用 DAX 按 0–3、4–7、8–14、15–21、22–30、31–60、60+ 分箱；或用 Power Query「分箱」。",
            "方案 B：柱形图 X=送达天数区间，Y=订单数；排序用区间排序列。",
        ],
    )
    add_code(
        doc,
        "送达天数区间 =\n"
        "SWITCH (\n"
        "    TRUE (),\n"
        "    '订单事实'[送达天数] <= 3, \"0-3天\",\n"
        "    '订单事实'[送达天数] <= 7, \"4-7天\",\n"
        "    '订单事实'[送达天数] <= 14, \"8-14天\",\n"
        "    '订单事实'[送达天数] <= 21, \"15-21天\",\n"
        "    '订单事实'[送达天数] <= 30, \"22-30天\",\n"
        "    '订单事实'[送达天数] <= 60, \"31-60天\",\n"
        "    \"60天以上\"\n"
        ")",
    )

    # 4.7
    add_heading(doc, "4.7 图 7：头部品类订单金额分布（箱线图）", 2)
    add_para(
        doc,
        "Power BI 原生没有箱线图。推荐从 AppSource 安装 Microsoft 的「Box and Whisker chart」；"
        "如果租户禁用自定义视觉对象，用「表 + 中位数/P25/P75」或 Python/R 视觉对象替代。",
    )
    add_steps(
        doc,
        [
            "视觉对象 → 更多视觉对象 → 从 AppSource 获取 → 搜索「Box and Whisker」→ 添加。",
            "导入 order_category_zh（订单-品类明细），筛选「是否有效订单」= 是、「含运费金额」> 0。",
            "视觉对象字段：类别 = 品类（中文）；值/采样 = 含运费金额；可选「详细信息」= 订单ID。",
            "筛选器 → 品类（中文）→ Top N 6 → 按含运费金额降序。",
            "格式 → Y 轴 → 对数刻度（金额跨度大）；打开中位数线、须线；关闭离群点或单独显示。",
            "标题「Top 6 品类订单金额分布（对数轴）」；脚注注明「订单-品类粒度，不是订单总额」。",
        ],
    )
    add_note(
        doc,
        "替代方案",
        "如果无法安装自定义视觉对象：用「簇状条形图」画每个品类的 P25/中位数/P75（需要先建三个度量值），"
        "或用 Python 视觉对象（需启用 Python）画箱线图；不要用普通柱形图冒充箱线图。",
    )

    # 4.8
    add_heading(doc, "4.8 图 8：Cohort 留存（热力图）", 2)
    add_para(
        doc,
        "Power BI 原生没有热力图视觉对象，但可以用「矩阵 + 条件格式」做出热力图。"
        "原始表是宽表（第1月…第12月），需要先在 Power Query 逆透视。",
    )
    add_steps(
        doc,
        [
            "导入 cohort_retention_wide_zh；在 Power Query 中选中「首购月份」。",
            "选中「第1月」到「第12月」→ 转换 → 逆透视列。",
            "把「属性」列重命名为「首购后月数」，「值」列重命名为「留存率」。",
            "清洗「首购后月数」：替换「第」和「月」为空，转换为整数；过滤空值。",
            "关闭并应用；在报表页放「矩阵」。",
            "行 = 首购月份；列 = 首购后月数；值 = 留存率（聚合选「平均值」或「最大值」，每个格子只有一行）。",
            "格式 → 值 → 字体颜色/背景色 → 条件格式 → 背景色 → 渐变：最小值 0 白色，最大值 0.008 深蓝。",
            "格式 → 行标题/列标题 → 字号 8；关闭小计；列宽调窄。",
        ],
    )
    add_note(
        doc,
        "为什么从第 1 月开始",
        "第 0 月留存率永远是 100%，放进热力图会把颜色压平。图 8 只展示第 1–12 月；第 0 月用卡片图单独显示 cohort 客户数。",
    )

    # 4.9
    add_heading(doc, "4.9 图 9：卖家 GMV 集中度（帕累托图）", 2)
    add_table(
        doc,
        ["字段井", "字段"],
        [
            ("X 轴", "卖家排名"),
            ("列 Y 轴", "商品GMV"),
            ("行 Y 轴", "累计GMV占比"),
            ("工具提示", "卖家ID、订单数、评论分、迟到率"),
        ],
        [4.5, 12.0],
        font_size=9,
    )
    add_steps(
        doc,
        [
            "视觉对象 → 折线和簇状柱形图。",
            "X 轴卖家排名；列 Y 轴商品GMV；行 Y 轴累计GMV占比。",
            "打开次坐标轴，行轴范围 0–100%，列轴格式 R$#,##0.00。",
            "筛选器 → 卖家排名 ≤ 100（或 Top N 100 by 商品GMV）。",
            "分析窗格 → 添加常量线 80%，灰色虚线，标签「80% 参考线」。",
            "标题「卖家帕累托：前 100 名贡献约 45% GMV」；在脚注说明累计占比按全部卖家计算。",
        ],
    )

    # 4.10
    add_heading(doc, "4.10 图 10：Top 5 州多指标（雷达图）", 2)
    add_para(
        doc,
        "Power BI 原生没有雷达图，需要 AppSource 的「Radar Chart」自定义视觉对象。"
        "如果无法安装，用「100% 堆叠条形图 + 5 个归一化度量值」或「小倍数条形图」替代。",
    )
    add_steps(
        doc,
        [
            "先建 5 个归一化度量值（见下方 DAX），全部返回 0–1。",
            "安装 Radar Chart：更多视觉对象 → AppSource → 搜索 Radar → 添加。",
            "字段：类别 = 州；值 = GMV归一、客单价归一、评分归一、准时率、复购率归一。",
            "筛选器 → 州 → Top N 5 → 按商品GMV降序。",
            "格式：填充透明度 10%–15%；线宽 2；图例放右侧；坐标轴 0–1。",
            "如果自定义视觉对象被禁用：用「簇状条形图」+ 5 个度量值，或做一张表格 + 条件格式。",
        ],
    )
    add_code(
        doc,
        "GMV归一 =\n"
        "DIVIDE (\n"
        "    MAX ( '州KPI'[商品GMV] ),\n"
        "    CALCULATE ( MAX ( '州KPI'[商品GMV] ), ALL ( '州KPI' ) )\n"
        ")\n\n"
        "客单价归一 =\n"
        "DIVIDE (\n"
        "    MAX ( '州KPI'[客单价] ),\n"
        "    CALCULATE ( MAX ( '州KPI'[客单价] ), ALL ( '州KPI' ) )\n"
        ")\n\n"
        "评分归一 = DIVIDE ( MAX ( '州KPI'[评论分] ), 5 )\n"
        "准时率 = MAX ( '州KPI'[准时率] )\n"
        "复购率归一 =\n"
        "DIVIDE (\n"
        "    MAX ( '州KPI'[复购客户率] ),\n"
        "    CALCULATE ( MAX ( '州KPI'[复购客户率] ), ALL ( '州KPI' ) )\n"
        ")",
    )
    doc.add_page_break()


def chapter_5(doc: Document):
    add_heading(doc, "5. 完整版模型：可交叉筛选的星型结构", 1)
    add_heading(doc, "5.1 为什么要升级", 2)
    add_para(
        doc,
        "快速版每张图各用一张聚合表，优点是快；缺点是「州」切片器不能同时过滤月度、品类和支付表。"
        "完整版用订单事实表 + 维度表，所有视觉对象共享筛选上下文，才能做真正的交互式看板。",
    )
    add_heading(doc, "5.2 推荐的表与关系", 2)
    rows = [
        ("订单事实", "orders_master_zh", "一行一个订单", "月度、州、评论、配送、KPI"),
        ("订单品类事实", "order_category_zh", "一行一个订单-品类", "品类金额、品类评论、箱线图"),
        ("订单卖家事实", "order_seller_zh", "一行一个订单-卖家", "卖家帕累托、卖家体验"),
        ("商品明细", "items_enriched_zh", "一行一个订单商品", "商品 Top N、商品下钻"),
        ("客户维度", "customer_rfm_zh", "一行一个客户", "RFM、复购、客户下钻"),
        ("日期维度", "日期表", "一行一天", "统一时间筛选"),
        ("汇报层", "monthly/category/state/seller 等 KPI", "预聚合", "只做单页展示，不参与关系"),
    ]
    add_table(doc, ["角色", "表", "粒度", "用途"], rows, [3.4, 6.0, 4.0, 3.6], font_size=8.6)
    rows = [
        ("订单事实[订单ID]", "订单品类事实[订单ID]", "1:*", "单方向", "品类明细归到订单"),
        ("订单事实[订单ID]", "订单卖家事实[订单ID]", "1:*", "单方向", "卖家明细归到订单"),
        ("订单事实[订单ID]", "商品明细[订单ID]", "1:*", "单方向", "商品明细归到订单"),
        ("客户维度[客户唯一ID]", "订单事实[客户唯一ID]", "1:*", "单方向", "客户筛选订单"),
        ("日期表[Date]", "订单事实[下单日期]", "1:*", "单方向", "月份切片"),
        ("日期表[Date]", "商品明细[下单时间戳]", "1:*", "单方向", "商品页时间切片"),
    ]
    add_table(doc, ["从", "到", "基数", "交叉筛选", "说明"], rows, [4.6, 4.8, 1.6, 2.0, 4.0], font_size=8.4)
    add_note(
        doc,
        "不要连接聚合表",
        "monthly_kpis_zh、category_kpis_zh 等是汇报层，不要和订单事实表建立关系，也不要用它们做跨表筛选。"
        "需要交互时用订单事实/订单品类事实；需要快速展示时单独放一页。",
    )

    add_heading(doc, "5.3 DAX 基础度量值", 2)
    add_para(doc, "在「订单事实」表上新建度量值，放入专用「度量值」表也可以。先建下面 8 个，够 10 张图使用。")
    add_code(
        doc,
        "有效订单数 =\n"
        "CALCULATE ( COUNTROWS ( '订单事实' ), '订单事实'[是否有效订单] = \"是\" )\n\n"
        "商品GMV =\n"
        "CALCULATE ( SUM ( '订单事实'[商品GMV] ), '订单事实'[是否有效订单] = \"是\" )\n\n"
        "含运费订单总额 =\n"
        "CALCULATE ( SUM ( '订单事实'[含运费订单总额] ), '订单事实'[是否有效订单] = \"是\" )\n\n"
        "客单价 =\n"
        "DIVIDE ( [含运费订单总额], [有效订单数] )\n\n"
        "迟到率 =\n"
        "DIVIDE (\n"
        "    CALCULATE (\n"
        "        COUNTROWS ( '订单事实' ),\n"
        "        '订单事实'[是否迟到] = \"是\",\n"
        "        NOT ISBLANK ( '订单事实'[送达天数] )\n"
        "    ),\n"
        "    CALCULATE (\n"
        "        COUNTROWS ( '订单事实' ),\n"
        "        '订单事实'[是否送达] = \"是\",\n"
        "        NOT ISBLANK ( '订单事实'[送达天数] )\n"
        "    )\n"
        ")\n\n"
        "平均评论分 =\n"
        "CALCULATE ( AVERAGE ( '订单事实'[评论分] ), '订单事实'[是否有效订单] = \"是\" )\n\n"
        "客户数 =\n"
        "CALCULATE ( DISTINCTCOUNT ( '订单事实'[客户唯一ID] ), '订单事实'[是否有效订单] = \"是\" )\n\n"
        "复购客户数 =\n"
        "COUNTROWS (\n"
        "    FILTER (\n"
        "        ADDCOLUMNS (\n"
        "            VALUES ( '订单事实'[客户唯一ID] ),\n"
        "            \"@订单数\", CALCULATE (\n"
        "                COUNTROWS ( '订单事实' ),\n"
        "                '订单事实'[是否有效订单] = \"是\"\n"
        "            )\n"
        "        ),\n"
        "        [@订单数] > 1\n"
        "    )\n"
        ")\n\n"
        "复购客户率 = DIVIDE ( [复购客户数], [客户数] )",
    )
    add_para(
        doc,
        "如果只做单表快速版，把上面的表名换成「月度KPI」或「品类KPI」，并把条件去掉，"
        "例如 有效订单数 = SUM('月度KPI'[有效订单数])、客单价 = DIVIDE(SUM('月度KPI'[含运费订单总额]), SUM('月度KPI'[有效订单数]))。",
    )

    doc.add_page_break()
    add_heading(doc, "5.4 排序与分箱列", 2)
    add_para(
        doc,
        "Power BI 默认按字母排序。以下三列必须建立「排序依据列」，否则图 6/图 8/图 9 的横轴会乱。",
    )
    rows = [
        ("送达时长区间", "0-3天=1，4-7天=2，…，60天以上=7", "图 6"),
        ("延迟区间", "准时或提前=1，迟到1-3天=2，…，迟到15天以上=5", "履约页"),
        ("订单金额区间", "0-50=1，50-100=2，…，1000以上=6", "金额分布"),
        ("月份", "月份序号 = 年*100+月", "图 1"),
    ]
    add_table(doc, ["列", "排序值", "用于"], rows, [5.0, 9.0, 3.0], font_size=8.8)
    add_code(
        doc,
        "区间排序 =\n"
        "SWITCH (\n"
        "    '配送分布'[送达时长区间],\n"
        "    \"0-3天\", 1, \"4-7天\", 2, \"8-14天\", 3,\n"
        "    \"15-21天\", 4, \"22-30天\", 5, \"31-60天\", 6, \"60天以上\", 7\n"
        ")",
    )
    add_para(doc, "建好后：选中「送达时长区间」→ 列工具 → 按列排序 → 区间排序。")
    doc.add_page_break()


def chapter_6(doc: Document):
    add_heading(doc, "6. 统一视觉规范", 1)
    add_heading(doc, "6.1 颜色", 2)
    rows = [
        ("主色 / 柱形", "#1F4E79", "标题、信用卡、主要柱"),
        ("辅助青", "#2A9D8F", "银行票据、准时/正向"),
        ("橙色", "#F4A261", "订单折线、均值线"),
        ("红色", "#E76F51", "峰值、迟到、差评风险"),
        ("黄色", "#E9C46A", "中性提示、参考"),
        ("灰色", "#6C757D", "辅助文字、脚注、参考线"),
    ]
    add_table(doc, ["用途", "HEX", "示例"], rows, [5.0, 3.5, 8.0], font_size=8.8)
    add_para(
        doc,
        "也可以在「视图 → 主题 → 浏览主题」导入 dashboard/olist_theme.json，一次设置 8 个数据色和字体。"
        "导入后检查各视觉对象的数据颜色是否被主题覆盖；需要单独强调的图再手动改。",
    )

    add_heading(doc, "6.2 字体与数字格式", 2)
    add_bullets(
        doc,
        [
            "全局字体 Microsoft YaHei；标题 16pt 加粗，坐标轴/图例 9–10pt，脚注 8pt。",
            "金额：R$ #,##0.00；大额 KPI 可用 R$ #,##0.0,,\"M\" 显示百万。",
            "比例：0.0%；不要先把 0.078 乘 100。",
            "计数：#,##0；送达天数：0.0 天；评分：0.00。",
            "标题不要用全角空格；脚注固定写「数据：report/tables_zh；口径见 analysis_guide.md」。",
        ],
    )

    add_heading(doc, "6.3 标题、脚注与 tooltip", 2)
    add_bullets(
        doc,
        [
            "每张图标题写「结论」，不要只写「月度GMV」；例如「2017-11 为 GMV 峰值」。",
            "脚注写数据来源、粒度、过滤条件；例如「订单-品类粒度；仅有效订单」。",
            "tooltip 放 2–4 个补充指标：订单数、同比/环比、样本量；不要把所有列都塞进去。",
            "为每张图添加「Alt 文本」（格式 → 常规 → 替代文本），方便导出和无障碍阅读。",
        ],
    )

    add_heading(doc, "6.4 切片器与交互", 2)
    add_bullets(
        doc,
        [
            "顶部统一放切片器：月份（日期范围）、州（下拉多选）、品类（下拉多选）、支付方式（按钮）。",
            "视图 → 同步切片器：将「月份」「州」同步到 4 个页面；只在一页显示，其他页隐藏。",
            "编辑交互：地图点击州 → 其他图只高亮，不筛选；需要下钻时再设置「钻取」。",
            "为「州」页设置钻取页：从州 → 品类 → 商品/卖家；钻取页放返回按钮。",
            "书签：保存「重置筛选」状态；按钮动作选书签。",
        ],
    )
    doc.add_page_break()


def chapter_7(doc: Document):
    add_heading(doc, "7. 页面布局（4 页看板）", 1)
    add_para(
        doc,
        "推荐 16:9、1280×720。用「视图 → 网格线/对齐」保持边距 24px；每页顶部 64px 标题栏，"
        "底部 24px 脚注。下图是建议的组件分配，不要求逐像素一致。",
    )
    rows = [
        ("P1 经营总览", "6 个 KPI 卡片 + 图 1 + 图 2 + 图 3", "月度/品类/支付总览"),
        ("P2 品类商品", "图 4 + 图 7 + 商品 Top 20 表", "品类规模、评分、金额分布"),
        ("P3 地域履约", "图 5 + 图 6 + 迟到率/评分卡", "地图、送达分布、体验"),
        ("P4 客户卖家", "图 8 + 图 9 + 图 10", "Cohort、帕累托、州雷达"),
    ]
    add_table(doc, ["页面", "主要组件", "回答的问题"], rows, [4.0, 9.0, 4.0], font_size=8.8)
    add_heading(doc, "7.1 P1 经营总览", 2)
    add_bullets(
        doc,
        [
            "顶部 6 个卡片：有效订单数、商品GMV、客单价、复购客户率、平均评论分、迟到率。",
            "左侧 60% 放图 1（月度组合图），右侧 40% 放图 2（品类 Top 10）。",
            "底部左侧放图 3（支付环形图），右侧放 3 行文字洞察（峰值、品类、支付结构）。",
            "切片器：月份、州。图 2 需要「品类」筛选时，用视觉对象级筛选器，不要放页面级品类切片器，避免图 3 被清空。",
        ],
    )
    add_heading(doc, "7.2 P2 品类商品", 2)
    add_bullets(
        doc,
        [
            "左上图 4（气泡散点），右下图 7（箱线图）；右侧放商品 Top 20 表。",
            "图 4 的「迟到率分组」图例放右上；图 7 的 Top 6 品类用视觉对象筛选器。",
            "表格列：商品ID、品类、商品GMV、有效订单数、评论分、迟到率；按 GMV 降序。",
        ],
    )
    add_heading(doc, "7.3 P3 地域履约", 2)
    add_bullets(
        doc,
        [
            "左侧 55% 放图 5 地图；右侧 45% 放图 6 送达分布。",
            "地图用经纬度散点，避免中文州名识别问题；颜色用迟到率，大小用 GMV。",
            "图 6 下方放 3 个卡片：中位送达天数、P90、迟到率。",
        ],
    )
    add_heading(doc, "7.4 P4 客户卖家", 2)
    add_bullets(
        doc,
        [
            "上方图 8 Cohort 热力图（矩阵），下方左侧图 9 帕累托，下方右侧图 10 雷达。",
            "图 8 的矩阵列宽调窄，只显示第 1–12 月；第 0 月用卡片显示 cohort 客户数。",
            "图 10 只显示 Top 5 州；雷达图的五个轴用「归一化」值，图例放右侧。",
        ],
    )
    doc.add_page_break()


def chapter_8(doc: Document):
    add_heading(doc, "8. 发布、刷新与分享", 1)
    add_heading(doc, "8.1 保存与发布", 2)
    add_steps(
        doc,
        [
            "文件 → 另存为：dashboard/Olist_Report.pbix（不要放在临时目录）。",
            "主页 → 发布 → 选择工作区（例如「Olist 分析」）。",
            "在 Power BI 服务中打开报表，检查字体、切片器、地图和自定义视觉对象是否正常。",
            "工作区 → 创建应用 → 添加报表 → 发布给需要的人；按需设置查看/编辑权限。",
        ],
    )
    add_heading(doc, "8.2 刷新：本地 CSV 的限制", 2)
    add_para(
        doc,
        "Power BI 服务不能直接访问你电脑上的 D:\\PowerBI\\Olist\\data。发布后如果源还是本地路径，"
        "只能手动刷新失败。要让云端定时刷新，必须把 CSV 放到服务能访问的位置。",
    )
    rows = [
        ("OneDrive / SharePoint", "推荐", "把 tables_zh 放到文档库；Power BI 用「SharePoint 文件夹」或 Web 连接；支持计划刷新。"),
        ("本地数据网关", "可选", "公司内网文件服务器；安装网关并配置数据源；维护成本较高。"),
        ("手动上传 pbix", "临时", "每次更新重新发布；不适合日常运营。"),
    ]
    add_table(doc, ["方案", "适用", "说明"], rows, [5.0, 3.0, 9.0], font_size=8.8)
    add_para(
        doc,
        "无论用哪种方式，刷新前先运行 python src/run_analysis.py 重新生成 tables_zh；"
        "不要把旧 CSV 直接覆盖成不同列名/列顺序，否则 Power BI 会报「找不到列」。",
    )
    add_heading(doc, "8.3 计划刷新与凭据", 2)
    add_steps(
        doc,
        [
            "Power BI 服务 → 数据集 → 设置 → 数据源凭据 → 编辑凭据（OneDrive/SharePoint 用 OAuth）。",
            "计划刷新 → 打开 → 设置每天/每周时间；时区选 Asia/Shanghai。",
            "刷新失败时看「刷新历史」：常见原因是路径变更、列名变更、文件被占用、凭据过期。",
            "设置刷新失败通知；重要看板建议每天上午检查一次。",
        ],
    )
    add_heading(doc, "8.4 导出与移动端", 2)
    add_bullets(
        doc,
        [
            "文件 → 导出 → PDF：用于邮件/汇报；导出前把页面设为「适合页面」。",
            "移动端：视图 → 移动布局 → 调整卡片和图表顺序；不要把 4 页 10 图硬塞进手机一屏。",
            "分享链接时确认权限：工作区成员/应用受众；不要把含有客户 ID 的明细页直接公开。",
        ],
    )
    doc.add_page_break()


def chapter_9(doc: Document):
    add_heading(doc, "9. 常见问题与排查", 1)
    rows = [
        ("中文乱码", "CSV 被按 ANSI/936 读取", "数据源 → 文件原始格式改 65001 → 重新导入；不要用记事本另存为 ANSI。"),
        ("数字变成文本", "列类型被识别为文本", "Power Query 更改类型 → 小数/整数；区域设置选中文（简体，中国）。"),
        ("月份按字母排序", "月份是文本且无排序依据", "建月份序号，按列排序；或把月份转成日期。"),
        ("地图只显示一个点", "州名未被识别/经纬度缺失", "用客户纬度/经度；或给州列设置数据类别「州或省」，并加国家=巴西。"),
        ("Top N 不生效", "在表上做了筛选而不是视觉对象筛选", "选中视觉对象 → 筛选器 → 品类 → Top N → 按商品GMV。"),
        ("订单数重复", "把多张事实表直接连接，或对 order-category 求 SUM", "一个视觉只用一个事实粒度；订单数用 DISTINCTCOUNT(订单ID)。"),
        ("支付占比相加超过100%", "用了订单占比或订单数", "环形图用支付金额/支付金额占比；不要用订单占比。"),
        ("箱线图找不到", "Power BI 原生不支持", "AppSource 安装 Box and Whisker；或改用 Python/R 视觉对象。"),
        ("雷达图找不到", "Power BI 原生不支持", "AppSource 安装 Radar Chart；或用 100% 堆叠条形图替代。"),
        ("自定义视觉对象被禁用", "租户/组织策略限制", "让管理员在管理门户允许 AppSource 视觉对象；否则用原生替代。"),
        ("刷新失败", "本地路径/凭据/列名变化", "改用 OneDrive/SharePoint；检查数据源设置；保持列名稳定。"),
        ("图表很慢", "导入过多明细列/自动日期表", "只导入需要的列；关闭自动日期/时间；用聚合表做汇报页。"),
        ("中文字体不对", "主题字体未覆盖", "主题 JSON 的 fontFace 改为 Microsoft YaHei；逐图检查字体。"),
    ]
    add_table(doc, ["现象", "可能原因", "处理"], rows, [4.3, 5.2, 7.5], font_size=8.3)
    add_note(
        doc,
        "口径优先",
        "遇到数字对不上时，先回到 report/tables_zh/overview_kpis_zh.csv 和 data_quality_report_zh.csv 对总数，"
        "不要在 Power BI 里为了「看起来对」而改口径。",
    )


def chapter_10(doc: Document):
    add_heading(doc, "10. 交付验收清单", 1)
    checks = [
        "10 张图全部存在，且图表类型与第 4 章一致（箱线图/雷达图允许用替代方案，但要在页脚说明）。",
        "所有金额格式为 R$ #,##0.00；比例格式为 0.0%，不是 0.078 这样的裸小数。",
        "月份、送达时长区间、延迟区间、订单金额区间按业务顺序排序，不是字母顺序。",
        "图 1 的双轴有明确左右轴单位；图 9 的累计线使用 0–100% 次坐标轴。",
        "图 3 使用支付金额/占比，不是订单占比；图 4 的散点颜色有图例说明。",
        "图 5 地图能显示州级差异；如果只用经纬度，脚注说明「州中心坐标」。",
        "图 8 的 cohort 只展示第 1–12 月，第 0 月用卡片另示；空格子保留为空，不填 0。",
        "所有图表有结论式标题、数据来源脚注、Alt 文本。",
        "页面级切片器不会导致某张图空白；跨页切片器已同步，重置按钮可用。",
        "发布后检查刷新历史；CSV 路径、凭据、列名稳定；分享权限符合要求。",
    ]
    for idx, text in enumerate(checks, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.45)
        p.paragraph_format.first_line_indent = Cm(-0.45)
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(f"□ {idx}. ")
        set_run_font(r1, size=10, bold=True, color=TEAL)
        r2 = p.add_run(text)
        set_run_font(r2, size=10)

    add_heading(doc, "附录 A：10 张图字段速查", 2)
    rows = [
        ("1 月度", "折线+柱", "月份；商品GMV；有效订单数", "—"),
        ("2 品类", "横向条形", "品类；商品GMV", "Top N 10"),
        ("3 支付", "环形", "支付方式；支付金额", "金额占比"),
        ("4 品类气泡", "散点", "商品GMV；评论分；有效订单数；品类", "迟到率分组"),
        ("5 州地图", "地图", "州/经纬度；商品GMV；迟到率", "—"),
        ("6 送达", "柱形/直方", "送达时长区间；订单数", "自定义排序"),
        ("7 箱线", "箱线", "品类；含运费金额", "Top 6"),
        ("8 Cohort", "矩阵热力", "首购月份；首购后月数；留存率", "条件格式"),
        ("9 帕累托", "折线+柱", "卖家排名；商品GMV；累计GMV占比", "Top 100"),
        ("10 雷达", "雷达", "州；5 个归一化指标", "Top 5"),
    ]
    add_table(doc, ["图", "视觉对象", "主要字段", "筛选/格式"], rows, [3.0, 3.0, 7.0, 4.0], font_size=8.5)

    add_heading(doc, "附录 B：本手册用到的文件", 2)
    rows = [
        ("report/tables_zh/*.csv", "中文图表底表", "快速版数据源"),
        ("data/processed_zh/*.csv", "中文明细表", "完整版事实/维度"),
        ("dashboard/olist_theme.json", "Power BI 主题", "颜色和字体"),
        ("report/Olist_10_charts.html", "目标效果", "对照 10 张图"),
        ("report/figures/", "PNG 图表", "汇报/对照"),
        ("report/analysis_guide.md", "口径说明", "字段和指标定义"),
    ]
    add_table(doc, ["文件", "内容", "用途"], rows, [6.0, 6.0, 5.0], font_size=8.8)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run("— 手册结束 —")
    set_run_font(r, size=9, color=GRAY)


def main():
    doc = setup_document()
    cover(doc)
    contents(doc)
    chapter_1(doc)
    chapter_2(doc)
    chapter_3(doc)
    chapter_4(doc)
    chapter_5(doc)
    chapter_6(doc)
    chapter_7(doc)
    chapter_8(doc)
    chapter_9(doc)
    chapter_10(doc)

    if PREVIEW.exists():
        doc.add_page_break()
        add_heading(doc, "目标效果预览", 1)
        add_para(doc, "下面是 4 张代表图的拼图预览；完整 10 张见 report/Olist_10_charts.html 和 report/figures/。")
        doc.add_picture(str(PREVIEW), width=Cm(16.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()