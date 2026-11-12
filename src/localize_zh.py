"""Chinese display localisation for the generated analysis tables.

The English tables remain the canonical machine-readable outputs.  This module
creates Chinese display copies so charts, Excel pivots, and business users can
read headers and categorical values without changing the underlying joins.
"""

from __future__ import annotations

import re

import pandas as pd

# ---------------------------------------------------------------------------
# Column names
# ---------------------------------------------------------------------------
COLUMN_ZH: dict[str, str] = {
    # identifiers
    "order_id": "订单ID",
    "customer_id": "客户ID（订单级）",
    "customer_unique_id": "客户唯一ID",
    "product_id": "商品ID",
    "seller_id": "卖家ID",
    "order_item_id": "订单商品序号",
    "latest_review_id": "最新评论ID",
    "zip_code_prefix": "ZIP前缀",
    "customer_zip_code_prefix": "客户ZIP前缀",
    # dates
    "order_purchase_timestamp": "下单时间",
    "order_approved_at": "审核通过时间",
    "order_delivered_carrier_date": "交给承运商时间",
    "order_delivered_customer_date": "客户签收时间",
    "order_estimated_delivery_date": "预计送达日期",
    "shipping_limit_date": "最晚发货日期",
    "purchase_ts": "下单时间戳",
    "purchase_date": "下单日期",
    "purchase_month": "下单月份",
    "month": "月份",
    "first_order_ts": "首次下单时间",
    "last_order_ts": "最近下单时间",
    "first_purchase_ts": "首次购买时间",
    "cohort_month": "首购月份",
    "latest_review_creation_date": "最新评论创建日期",
    "latest_review_answer_timestamp": "最新评论回复时间",
    "latest_review_comment_title": "最新评论标题",
    "latest_review_comment_message": "最新评论内容",
    "review_comment_title": "评论标题",
    "review_comment_message": "评论内容",
    "review_creation_date": "评论创建日期",
    "review_answer_timestamp": "评论回复时间",
    "review_id": "评论ID",
    "analysis_start": "分析开始日期",
    "analysis_end": "分析结束日期",
    # dimensions and statuses
    "order_status": "订单状态",
    "payment_type": "支付方式",
    "primary_payment_type": "主要支付方式",
    "payment_types": "支付方式组合",
    "delivery_status": "配送状态",
    "customer_type": "客户类型",
    "rfm_segment": "RFM客群",
    "rfm_segment_cn": "RFM客群（中文）",
    "category": "品类",
    "product_category_name": "品类（葡萄牙语原名）",
    "product_category_english": "品类（英文）",
    "product_category_label": "品类（中文）",
    "state": "州",
    "customer_state": "客户所在州",
    "seller_state": "卖家所在州",
    "geo_state": "地理州",
    "customer_city": "客户城市",
    "seller_city": "卖家城市",
    "table": "数据表",
    "file": "文件",
    "check": "检查项",
    "status": "状态",
    "detail": "说明",
    # counts
    "orders": "订单数",
    "orders_all": "全部订单数",
    "orders_valid": "有效订单数",
    "orders_delivered": "已送达订单数",
    "orders_canceled": "已取消订单数",
    "orders_unavailable": "不可用订单数",
    "canceled_orders": "已取消订单数",
    "unavailable_orders": "不可用订单数",
    "delivered_orders": "已送达订单数",
    "delivered_with_dates": "有送达日期订单数",
    "late_orders": "迟到订单数",
    "on_time_orders": "准时订单数",
    "customers": "客户数",
    "customers_unique": "独立客户数",
    "new_customers": "新客户数",
    "repeat_customers": "复购客户数",
    "repeat_orders": "复购订单数",
    "items": "商品件数",
    "units": "销量（件）",
    "sellers": "卖家数",
    "categories": "品类数",
    "reviews": "评论订单数",
    "review_count": "评论数",
    "comments": "评论留言数",
    "comment_count": "评论留言数",
    "total_reviews": "评论总数",
    "low_review_orders": "差评订单数（1-2星）",
    "five_star_orders": "五星订单数",
    "payment_rows": "支付笔数",
    "payment_count": "支付笔数",
    "payment_method_count": "支付方式数",
    "installment_rows_gt1": "分期>1笔数",
    "orders_with_payment": "有支付订单数",
    "orders_without_payment": "无支付订单数",
    "orders_matching_within_0_01": "支付差额≤0.01订单数",
    "orders_mismatch": "支付差额>0.01订单数",
    "cohort_size": "同期客户数",
    "top_n_sellers": "前N个卖家",
    "customer_order_number": "客户订单序号",
    "period_number": "距首购月数",
    # ranks
    "category_rank": "品类排名",
    "state_rank": "州排名",
    "seller_rank": "卖家排名",
    "product_rank": "商品排名",
    # money
    "gmv": "商品GMV",
    "merchandise_value": "商品金额",
    "freight_value": "运费",
    "gross_order_value": "含运费订单总额",
    "gross_value": "含运费金额",
    "payment_value": "支付金额",
    "total_payment_value": "支付总额",
    "total_order_value": "订单总额",
    "total_gap": "支付差额合计",
    "payment_gap": "支付差额",
    "payment_gap_total": "支付差额合计",
    "potential_gross_value": "潜在订单总额",
    "aov": "客单价",
    "avg_order_value": "平均订单金额",
    "avg_item_value": "平均商品单价",
    "avg_price": "平均售价",
    "avg_freight": "平均运费",
    "avg_freight_per_order": "平均每单运费",
    "avg_merchandise_value": "平均商品金额",
    "avg_items_per_order": "平均每单件数",
    "avg_payment_value": "平均支付金额",
    "avg_installments": "平均分期数",
    "price": "商品单价",
    "item_total": "商品行总额",
    "revenue": "收入",
    "monetary": "消费金额",
    "avg_monetary": "平均消费金额",
    "revenue_per_cohort_customer": "同期客户人均收入",
    # rates and shares
    "cancel_rate": "取消/不可用率",
    "late_rate": "迟到率",
    "on_time_rate": "准时率",
    "delivered_rate": "送达率",
    "repeat_customer_rate": "复购客户率",
    "repeat_order_rate": "复购订单率",
    "repeat_rate": "复购率",
    "review_coverage": "评论覆盖率",
    "review_comment_rate": "评论留言率",
    "low_review_rate": "差评率（1-2星）",
    "positive_review_rate": "好评率（4-5星）",
    "comment_rate": "留言率",
    "five_star_rate": "五星率",
    "match_rate": "支付匹配率",
    "retention_rate": "留存率",
    "missing_cell_rate": "缺失率",
    "payment_match_rate": "支付匹配率",
    "gmv_share": "GMV占比",
    "orders_share": "订单占比",
    "order_share": "订单占比",
    "customer_share": "客户占比",
    "revenue_share": "收入占比",
    "freight_share": "运费占比",
    "cumulative_gmv_share": "累计GMV占比",
    "seller_share": "卖家数量占比",
    "share": "占比",
    "payment_value_share": "支付金额占比",
    "payment_value_share_of_type": "占该支付方式金额比",
    "payment_value_share_of_all": "占全部支付金额比",
    "installment_row_share_gt1": "分期>1笔占比",
    # scores / customer
    "review_score": "评论分",
    "avg_review_score": "平均评论分",
    "review_score_mean": "评论分均值",
    "review_comment_count": "评论留言数",
    "r_score": "R评分（最近购买）",
    "f_score": "F评分（购买频次）",
    "m_score": "M评分（消费金额）",
    "rfm_total_score": "RFM总分",
    "rfm_cell": "RFM组合",
    # delivery / time
    "delivery_days": "送达天数",
    "estimated_days": "预计送达天数",
    "delay_days": "相对预计延迟天数",
    "avg_delivery_days": "平均送达天数",
    "median_delivery_days": "送达天数中位数",
    "p90_delivery_days": "送达天数P90",
    "avg_delay_days": "平均提前/延迟天数",
    "recency_days": "最近购买距今天数",
    "avg_recency_days": "平均最近购买距今天数",
    "frequency": "购买频次",
    "avg_frequency": "平均购买频次",
    # buckets
    "delivery_days_bucket": "送达时长区间",
    "delay_bucket": "延迟区间",
    "order_value_band": "订单金额区间",
    "installment_bucket": "分期区间",
    # flags
    "is_valid_order": "是否有效订单",
    "is_delivered": "是否送达",
    "is_canceled": "是否取消",
    "is_unavailable": "是否不可用",
    "is_in_window": "是否在分析窗口",
    "is_late": "是否迟到",
    "has_items": "是否有商品明细",
    "is_first_purchase": "是否首次购买",
    "latest_review_has_comment": "最新评论是否有留言",
    # product attributes
    "product_name_length": "商品名称长度",
    "product_description_length": "商品描述长度",
    "product_photos_qty": "商品图片数",
    "product_weight_g": "商品重量（克）",
    "product_length_cm": "商品长度（厘米）",
    "product_height_cm": "商品高度（厘米）",
    "product_width_cm": "商品宽度（厘米）",
    "item_count": "商品件数",
    "product_count": "商品种类数",
    "seller_count": "卖家数",
    "category_count": "品类数",
    "payment_installments_max": "最大分期数",
    "customer_lat": "客户纬度",
    "customer_lng": "客户经度",
    "seller_lat": "卖家纬度",
    "seller_lng": "卖家经度",
    "geo_lat": "纬度",
    "geo_lng": "经度",
    "geo_points": "坐标点数",
    # quality / profile
    "rows": "行数",
    "columns": "列数",
    "bytes": "字节数",
    "duplicate_rows": "重复行数",
    "missing_cells": "缺失单元格数",
    "value": "数值",
}

# Table-specific header overrides where the same English word has a different
# meaning (for example ``category`` in the quality report).
TABLE_COLUMN_OVERRIDES: dict[str, dict[str, str]] = {
    "data_quality_report": {
        "category": "检查类别",
        "check": "检查项",
        "value": "数值",
        "status": "状态",
        "detail": "说明",
    },
    "raw_file_profile": {
        "table": "数据表",
        "file": "文件",
        "rows": "行数",
        "columns": "列数",
        "bytes": "字节数",
        "duplicate_rows": "重复行数",
        "missing_cells": "缺失单元格数",
        "missing_cell_rate": "缺失率",
    },
    "review_distribution": {
        "review_score": "评分（1-5）",
    },
}

# ---------------------------------------------------------------------------
# Categorical values
# ---------------------------------------------------------------------------
ORDER_STATUS_ZH = {
    "delivered": "已送达",
    "shipped": "已发货",
    "canceled": "已取消",
    "unavailable": "不可用",
    "invoiced": "已开票",
    "processing": "处理中",
    "created": "已创建",
    "approved": "已审核",
}

PAYMENT_TYPE_ZH = {
    "credit_card": "信用卡",
    "boleto": "银行票据",
    "voucher": "代金券",
    "debit_card": "借记卡",
    "not_defined": "未定义",
}

DELIVERY_STATUS_ZH = {
    "On time": "准时",
    "Late": "迟到",
}

DELIVERY_DAY_BUCKET_ZH = {
    "0-3": "0-3天",
    "4-7": "4-7天",
    "8-14": "8-14天",
    "15-21": "15-21天",
    "22-30": "22-30天",
    "31-60": "31-60天",
    "60+": "60天以上",
}

DELAY_BUCKET_ZH = {
    "On time or early": "准时或提前",
    "1-3 days late": "迟到1-3天",
    "4-7 days late": "迟到4-7天",
    "8-14 days late": "迟到8-14天",
    "15+ days late": "迟到15天以上",
}

ORDER_VALUE_BAND_ZH = {
    "0-50": "0-50雷亚尔",
    "50-100": "50-100雷亚尔",
    "100-200": "100-200雷亚尔",
    "200-500": "200-500雷亚尔",
    "500-1000": "500-1000雷亚尔",
    "1000+": "1000雷亚尔以上",
}

INSTALLMENT_BUCKET_ZH = {
    "0": "0期",
    "1": "1期",
    "2-3": "2-3期",
    "4-6": "4-6期",
    "7-12": "7-12期",
    "13+": "13期以上",
}

RFM_SEGMENT_ZH = {
    "Champions": "冠军客户",
    "Loyal": "忠诚客户",
    "Potential Loyalist": "潜力客户",
    "New": "新客户",
    "Need Attention": "需关注",
    "At Risk": "流失风险",
    "Hibernating": "沉睡客户",
    "Others": "其他",
}

CUSTOMER_TYPE_ZH = {
    "Repeat": "复购客户",
    "One-time": "单次客户",
}

STATE_ZH = {
    "AC": "阿克里州",
    "AL": "阿拉戈斯州",
    "AM": "亚马孙州",
    "AP": "阿马帕州",
    "BA": "巴伊亚州",
    "CE": "塞阿拉州",
    "DF": "联邦区",
    "ES": "圣埃斯皮里图州",
    "GO": "戈亚斯州",
    "MA": "马拉尼昂州",
    "MG": "米纳斯吉拉斯州",
    "MS": "南马托格罗索州",
    "MT": "马托格罗索州",
    "PA": "帕拉州",
    "PB": "帕拉伊巴州",
    "PE": "伯南布哥州",
    "PI": "皮奥伊州",
    "PR": "巴拉那州",
    "RJ": "里约热内卢州",
    "RN": "北里奥格兰德州",
    "RO": "朗多尼亚州",
    "RR": "罗赖马州",
    "RS": "南里奥格兰德州",
    "SC": "圣卡塔琳娜州",
    "SE": "塞尔希培州",
    "SP": "圣保罗州",
    "TO": "托坎廷斯州",
}

CATEGORY_ZH = {
    "Agro Industry And Commerce": "农业与工商业",
    "Air Conditioning": "空调",
    "Art": "艺术",
    "Arts And Craftmanship": "手工艺",
    "Audio": "音频设备",
    "Auto": "汽车用品",
    "Baby": "母婴",
    "Bed Bath Table": "床品浴品餐桌",
    "Books General Interest": "大众书籍",
    "Books Imported": "进口书籍",
    "Books Technical": "技术书籍",
    "Cds Dvds Musicals": "音乐CD/DVD",
    "Christmas Supplies": "圣诞用品",
    "Cine Photo": "影像摄影",
    "Computers": "电脑",
    "Computers Accessories": "电脑配件",
    "Consoles Games": "游戏主机",
    "Construction Tools Construction": "建筑工具",
    "Construction Tools Lights": "照明工具",
    "Construction Tools Safety": "安全防护工具",
    "Cool Stuff": "潮流好物",
    "Costruction Tools Garden": "园艺工具",
    "Costruction Tools Tools": "工具",
    "Diapers And Hygiene": "纸尿裤与卫生",
    "Drinks": "饮料",
    "Dvds Blu Ray": "蓝光DVD",
    "Electronics": "电子产品",
    "Fashio Female Clothing": "女装",
    "Fashion Bags Accessories": "时尚箱包配饰",
    "Fashion Childrens Clothes": "童装",
    "Fashion Male Clothing": "男装",
    "Fashion Shoes": "时尚鞋履",
    "Fashion Sport": "运动时尚",
    "Fashion Underwear Beach": "内衣泳装",
    "Fixed Telephony": "固定电话",
    "Flowers": "花卉",
    "Food": "食品",
    "Food Drink": "食品饮料",
    "Furniture Bedroom": "卧室家具",
    "Furniture Decor": "家具装饰",
    "Furniture Living Room": "客厅家具",
    "Furniture Mattress And Upholstery": "床垫与软装",
    "Garden Tools": "园艺工具",
    "Health Beauty": "美妆个护",
    "Home Appliances": "家电",
    "Home Appliances 2": "家电（二类）",
    "Home Comfort 2": "家居舒适（二类）",
    "Home Confort": "家居舒适",
    "Home Construction": "家装建材",
    "Housewares": "家居用品",
    "Industry Commerce And Business": "工业与商业用品",
    "Kitchen Dining Laundry Garden Furniture": "厨房餐厨/洗衣/花园家具",
    "La Cuisine": "法式厨具",
    "Luggage Accessories": "箱包配件",
    "Market Place": "市场平台",
    "Music": "音乐",
    "Musical Instruments": "乐器",
    "Office Furniture": "办公家具",
    "Party Supplies": "派对用品",
    "Pc Gamer": "PC游戏",
    "Perfumery": "香水",
    "Pet Shop": "宠物用品",
    "Portateis Cozinha E Preparadores De Alimentos": "便携厨房食品处理器",
    "Security And Services": "安保服务",
    "Signaling And Security": "标识与安防",
    "Small Appliances": "小家电",
    "Small Appliances Home Oven And Coffee": "家用烤箱与咖啡机",
    "Sports Leisure": "运动休闲",
    "Stationery": "文具",
    "Tablets Printing Image": "平板与打印影像",
    "Telephony": "手机通信",
    "Toys": "玩具",
    "Unknown": "未知",
    "Watches Gifts": "手表礼品",
}

QUALITY_CATEGORY_ZH = {
    "Key integrity": "主键完整性",
    "Referential integrity": "关联完整性",
    "Coverage": "覆盖率",
    "Value validity": "数值有效性",
    "Time validity": "时间有效性",
    "Analysis scope": "分析范围",
}

QUALITY_STATUS_ZH = {
    "PASS": "通过",
    "WARN": "警告",
    "FAIL": "失败",
    "INFO": "提示",
}

QUALITY_CHECK_ZH = {
    "orders_unique_order_id": "订单主键唯一",
    "customers_unique_customer_id": "客户ID唯一",
    "customers_unique_person_id": "客户唯一ID重复",
    "products_unique_product_id": "商品主键唯一",
    "sellers_unique_seller_id": "卖家主键唯一",
    "order_items_unique_order_item": "订单商品序号唯一",
    "payments_unique_order_sequence": "支付序号唯一",
    "reviews_duplicate_review_id": "重复评论ID",
    "reviews_duplicate_order_id": "重复订单评论",
    "order_items_orphan_orders": "订单商品无法关联订单",
    "payments_orphan_orders": "支付无法关联订单",
    "reviews_orphan_orders": "评论无法关联订单",
    "orders_orphan_customers": "订单无法关联客户",
    "order_items_orphan_products": "订单商品无法关联商品",
    "order_items_orphan_sellers": "订单商品无法关联卖家",
    "orders_without_items": "无商品明细订单",
    "orders_without_payment": "无支付订单",
    "review_coverage_in_scope": "分析窗口评论覆盖率",
    "customer_geo_coverage": "客户地理覆盖率",
    "seller_geo_coverage": "卖家地理覆盖率",
    "geolocation_outliers_removed": "剔除的境外坐标点",
    "product_category_missing": "缺失品类商品数",
    "product_category_untranslated": "未翻译品类数",
    "order_items_price_nonpositive": "非正商品价格",
    "order_items_freight_negative": "负运费",
    "payments_value_nonpositive": "非正支付金额",
    "payment_gap_abs_gt_001": "支付差额>0.01订单数",
    "payment_gap_total": "支付差额合计",
    "delivered_missing_delivery_date": "已送达但缺少送达时间",
    "negative_delivery_days": "负送达时长",
    "delivery_before_estimate_extreme": "极早送达订单",
    "orders_outside_analysis_window": "分析窗口外订单",
    "analysis_months": "分析月份数",
    "orders_all_in_window": "窗口内全部订单",
    "orders_valid_in_window": "窗口内有效订单",
    "gross_order_value_in_window": "窗口内含运费订单总额",
    "late_rate_delivered": "已送达订单迟到率",
}

TABLE_NAME_ZH = {
    "orders": "订单主表",
    "order_items": "订单商品明细",
    "payments": "支付记录",
    "reviews": "评论",
    "customers": "客户",
    "products": "商品",
    "sellers": "卖家",
    "geolocation": "地理位置",
    "category_translation": "品类翻译",
}

# Sheet names for the Chinese Excel workbook.
EXCEL_SHEETS_ZH = {
    "monthly_kpis": "月度趋势",
    "order_status_summary": "订单状态",
    "category_kpis": "品类",
    "category_monthly": "品类月度",
    "state_kpis": "地域",
    "state_monthly": "地域月度",
    "seller_kpis": "卖家",
    "seller_pareto": "卖家帕累托",
    "top_products": "商品Top100",
    "payment_type_kpis": "支付方式",
    "installment_distribution": "分期结构",
    "payment_reconciliation": "支付对账",
    "review_distribution": "评分分布",
    "review_monthly": "评分月度",
    "review_by_delivery": "配送与评分",
    "review_by_delay_bucket": "延迟与评分",
    "delivery_distribution": "送达时长",
    "delivery_delay_distribution": "延迟分布",
    "order_value_distribution": "订单金额",
    "rfm_segment_summary": "RFM客群",
    "rfm_score_matrix": "RFM矩阵",
    "customer_repeat_summary": "复购结构",
    "cohort_retention": "Cohort明细",
    "cohort_retention_wide": "Cohort留存",
    "data_quality_report": "数据质量",
    "raw_file_profile": "原始文件概况",
}

PERIOD_PATTERN = re.compile(r"^period_(\d+)$")


def _translate_payment_types(value):
    if pd.isna(value):
        return value
    parts = [part.strip() for part in str(value).split("|") if part.strip()]
    return " / ".join(PAYMENT_TYPE_ZH.get(part, part) for part in parts)


def _translate_rfm_cell(value):
    if pd.isna(value):
        return value
    text = str(value)
    match = re.fullmatch(r"(\d)(\d)(\d)", text)
    if match:
        return f"R{match.group(1)}-F{match.group(2)}-M{match.group(3)}"
    return text


def _column_name(table_name: str, column: str) -> str:
    if column in TABLE_COLUMN_OVERRIDES.get(table_name, {}):
        return TABLE_COLUMN_OVERRIDES[table_name][column]
    match = PERIOD_PATTERN.match(column)
    if match:
        return f"第{int(match.group(1))}月"
    return COLUMN_ZH.get(column, column)


def _value_mapping(table_name: str, column: str):
    if table_name == "data_quality_report":
        return {
            "category": QUALITY_CATEGORY_ZH,
            "status": QUALITY_STATUS_ZH,
            "check": QUALITY_CHECK_ZH,
        }.get(column)
    if table_name == "raw_file_profile" and column == "table":
        return TABLE_NAME_ZH
    if column == "order_status":
        return ORDER_STATUS_ZH
    if column == "payment_type":
        return PAYMENT_TYPE_ZH
    if column == "primary_payment_type":
        return PAYMENT_TYPE_ZH
    if column == "delivery_status":
        return DELIVERY_STATUS_ZH
    if column == "delivery_days_bucket":
        return DELIVERY_DAY_BUCKET_ZH
    if column == "delay_bucket":
        return DELAY_BUCKET_ZH
    if column == "order_value_band":
        return ORDER_VALUE_BAND_ZH
    if column == "installment_bucket":
        return INSTALLMENT_BUCKET_ZH
    if column == "rfm_segment":
        return RFM_SEGMENT_ZH
    if column == "customer_type":
        return CUSTOMER_TYPE_ZH
    if column in {"state", "customer_state", "seller_state", "geo_state"}:
        return STATE_ZH
    if column in {"category", "product_category_label"}:
        return CATEGORY_ZH
    return None


def localize_table(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Return a Chinese display copy of one generated table.

    Numeric columns are untouched.  Identifiers, dates, and filenames remain in
    their original form so they can still be used for joins and lookups.
    """

    out = df.copy()

    for column in list(out.columns):
        # Localise booleans to 是/否 while preserving missing values.
        if pd.api.types.is_bool_dtype(out[column]):
            out[column] = out[column].map({True: "是", False: "否"})
            continue

        if column == "payment_types":
            out[column] = out[column].map(_translate_payment_types)
            continue

        if column == "rfm_cell":
            out[column] = out[column].map(_translate_rfm_cell)
            continue

        mapping = _value_mapping(table_name, column)
        if mapping:
            out[column] = out[column].replace(mapping)

    out = out.rename(columns={column: _column_name(table_name, column) for column in out.columns})

    # Guard against accidental duplicate headers after translation.
    if len(set(out.columns)) != len(out.columns):
        duplicates = pd.Index(out.columns)[pd.Index(out.columns).duplicated()].tolist()
        raise ValueError(
            f"Chinese headers collide in {table_name}: {duplicates}. "
            "Add a table-specific override."
        )
    return out