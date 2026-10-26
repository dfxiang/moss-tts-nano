"""演示数据的生成参数（集中管理，生成与校验共用同一套口径）。

调整演示数据的规模与趋势时只改本文件；``generate_mock_data.py`` 负责按这些参数造数，
``verify_database.py`` 用同样的参数校验结果。

常用命令行动态覆盖（无需改本文件）：

    python generate_mock_data.py --seed 20260101 \
        --start-date 2023-01-01 --end-date 2025-12-31

各字段含义：

* ``SEED``            —— 随机种子，固定种子可复现同一批数据；
* ``START_DATE`` / ``END_DATE`` —— 演示数据区间（当前为 2022-01-01 ~ 2026-07-31，约四年半）；
* ``YEAR_TARGET``     —— 每年的**年化**销售目标（元/年，用于对齐「完整年度约 500 亿元」口径），
  实际区间的目标按覆盖天数折算；
* ``CATEGORY_SHARE``  —— 各大类销售占比（合计 1.0）；
* ``CATEGORY_MARGIN`` —— 各大类毛利率，综合毛利率约 17%（对应年毛利约 80 亿元）；
* ``MONTH_WEIGHT`` / ``DOW_WEIGHT`` —— 月度季节系数与星期系数（周末订单减少）；
* ``MAX_LINES``       —— 单张销售订单最多明细行数；
* ``EMPLOYEE_COUNT`` / ``CUSTOMER_COUNT`` —— 员工与客户规模目标，
  分别由 ``generate_mock_data.py`` 中的 ``DEPT_PLAN`` / ``CUSTOMER_TYPE_PLAN`` 汇总得到。
"""

from datetime import date

SEED = 20260829
START_DATE = date(2022, 1, 1)
END_DATE = date(2026, 7, 31)

# 完整年度销售目标（元）：未在 YEAR_TARGET 中列出的年份按此折算
FULL_YEAR_TARGET = 500e8

# 年度销售目标（元/年，年化口径）。2026 只覆盖 01-01 ~ 07-31（212 天）且为冲量
# 较高的半年，年化目标按 306 亿元折算：306e8 * 365 / 212 ≈ 527 亿元。
YEAR_TARGET = {
    2022: 490e8,
    2023: 500e8,
    2024: 506e8,
    2025: 512e8,
    2026: 306e8 * 365 / 212,
}

# 各分类销售占比（合计 1.0）与毛利率
CATEGORY_SHARE = {
    "CAT-VAC": 0.14,    # 疫苗 ~70亿
    "CAT-DRUG": 0.28,   # 化学药品 ~140亿
    "CAT-BIO": 0.06,    # 生物制品 ~30亿
    "CAT-TCM": 0.06,    # 中成药 ~30亿
    "CAT-HIGH": 0.28,   # 高值耗材 ~140亿
    "CAT-LOW": 0.10,    # 低耗材 ~50亿
    "CAT-EQUIP": 0.08,  # 医疗设备 ~40亿
}
CATEGORY_MARGIN = {
    "CAT-VAC": 0.31, "CAT-DRUG": 0.15, "CAT-BIO": 0.23, "CAT-TCM": 0.19,
    "CAT-HIGH": 0.13, "CAT-LOW": 0.19, "CAT-EQUIP": 0.09,
}

# 月度季节系数（流感季/年末冲量高，春节低）
MONTH_WEIGHT = {
    1: 0.82, 2: 0.70, 3: 0.95, 4: 0.92, 5: 0.96, 6: 1.10,
    7: 1.02, 8: 1.00, 9: 1.12, 10: 1.05, 11: 1.10, 12: 1.28,
}
DOW_WEIGHT = {0: 1.08, 1: 1.08, 2: 1.08, 3: 1.08, 4: 1.08, 5: 0.62, 6: 0.50}

MAX_LINES = 18

# 规模目标（生成脚本会校验与计划表一致，改动计划表时同步修改）
EMPLOYEE_COUNT = 500
CUSTOMER_COUNT = 1650


def year_target(year: int, start: date = START_DATE, end: date = END_DATE) -> float:
    """返回数据区间内某年的销售目标（元）。

    年化目标取自 ``YEAR_TARGET``（缺省 ``FULL_YEAR_TARGET``），再按该年实际被
    数据区间覆盖的天数折算；所以默认区间下 2026 年（半年）的目标约 306 亿元，
    自定义区间（如只要一个季度）也会按比例缩放。
    """
    y_start = max(start, date(year, 1, 1))
    y_end = min(end, date(year, 12, 31))
    if y_start > y_end:
        return 0.0
    annual = YEAR_TARGET.get(year, FULL_YEAR_TARGET)
    covered = (y_end - y_start).days + 1
    days_in_year = (date(year, 12, 31) - date(year, 1, 1)).days + 1
    return annual * covered / days_in_year


def years(start: date = START_DATE, end: date = END_DATE) -> list:
    """返回数据区间覆盖的年份列表。"""
    return list(range(start.year, end.year + 1))
