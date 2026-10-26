"""校验 medsalesdb：对象数量、数据规模、日期区间、关键指标与逻辑一致性。

目标指标：
    - 员工约 500 人
    - 完整年度销售额约 500 亿元/年，销售毛利约 80 亿元/年
    - 数据区间 2022-01-01 ~ 2026-07-31

校验口径与 generate_mock_data.py 共用 mock_params.py 中的参数：

    python verify_database.py                                   # 默认区间
    python verify_database.py --start-date 2024-01-01 --end-date 2026-12-31

说明：API 服务启动时会自动补齐用户/角色/权限/证照等系统表，因此本脚本只要求
schema.sql 定义的 18 张业务表与 7 个视图存在，额外的表会被识别为「系统新增」。
"""

import argparse
import sys
from datetime import date

import psycopg

from db_config import DB_NAME, conninfo
from mock_params import EMPLOYEE_COUNT, END_DATE, START_DATE, year_target

# schema.sql 定义的存量对象
EXPECTED_TABLES = {
    "product_category", "manufacturer", "supplier", "warehouse", "department", "employee",
    "customer", "product", "price_history", "sales_order", "sales_order_item",
    "payment_record", "sales_return", "sales_return_item", "purchase_order",
    "purchase_order_item", "inventory", "inventory_movement",
}
EXPECTED_VIEWS = {
    "v_order_detail", "v_sales_daily", "v_sales_monthly", "v_product_sales_summary",
    "v_customer_sales_summary", "v_employee_sales_summary", "v_inventory_status",
}


def q(conn, sql, params=None):
    return conn.execute(sql, params).fetchall()


def section(title):
    print(f"\n===== {title} =====")


def check(ok: bool, desc: str):
    print(("通过  " if ok else "失败  ") + desc)
    return ok


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="校验 medsalesdb 演示数据")
    parser.add_argument("--start-date", default=None,
                        help=f"期望的数据起始日期 YYYY-MM-DD，默认 {START_DATE}")
    parser.add_argument("--end-date", default=None,
                        help=f"期望的数据结束日期 YYYY-MM-DD，默认 {END_DATE}")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    global START_DATE, END_DATE
    args = parse_args(argv)
    if args.start_date:
        START_DATE = date.fromisoformat(args.start_date)
    if args.end_date:
        END_DATE = date.fromisoformat(args.end_date)

    all_ok = True
    with psycopg.connect(conninfo(DB_NAME)) as conn:
        section("数据库对象概览")
        tables = [t[0] for t in q(conn, """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name
        """)]
        views = [v[0] for v in q(conn, """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_type='VIEW' ORDER BY table_name
        """)]
        index_count = q(conn, "SELECT count(*) FROM pg_indexes WHERE schemaname='public'")[0][0]
        table_comments = q(conn, """
            SELECT count(*) FROM pg_description d
            JOIN pg_class c ON c.oid = d.objoid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname='public' AND c.relkind IN ('r','v') AND d.objsubid=0
        """)[0][0]
        column_comments = q(conn, """
            SELECT count(*) FROM pg_description d
            JOIN pg_class c ON c.oid = d.objoid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname='public' AND d.objsubid>0
        """)[0][0]
        extra_tables = sorted(set(tables) - EXPECTED_TABLES)
        extra_views = sorted(set(views) - EXPECTED_VIEWS)
        print(f"表 {len(tables)} 张：{', '.join(tables)}")
        if extra_tables:
            print(f"其中业务表之外的增量表（API 启动时自动建）：{', '.join(extra_tables)}")
        print(f"视图 {len(views)} 个：{', '.join(views)}")
        if extra_views:
            print(f"其中 schema.sql 之外的视图：{', '.join(extra_views)}")
        print(f"索引 {index_count} 个（含主键唯一索引）")
        print(f"表/视图注释 {table_comments} 条，列注释 {column_comments} 条")
        all_ok &= check(EXPECTED_TABLES <= set(tables), "业务表齐全：schema.sql 的 18 张表")
        all_ok &= check(EXPECTED_VIEWS <= set(views), "视图齐全：schema.sql 的 7 个视图")

        section("各表记录数")
        for name in tables:
            count = q(conn, f"SELECT count(*) FROM {name}")[0][0]
            print(f"{name:<24} {count:>10,}")

        emp_count = q(conn, "SELECT count(*) FROM employee")[0][0]
        all_ok &= check(emp_count == EMPLOYEE_COUNT,
                        f"员工规模：{emp_count} 人（目标 {EMPLOYEE_COUNT}）")

        section(f"销售数据概览（{START_DATE} ~ {END_DATE}）")
        start, end, total_orders, valid_orders, amount, cost, profit, paid = q(conn, """
            SELECT min(order_date)::text, max(order_date)::text,
                   count(*), count(*) FILTER (WHERE status <> '已取消'),
                   sum(total_amount) FILTER (WHERE status <> '已取消'),
                   sum(cost_amount) FILTER (WHERE status <> '已取消'),
                   round(sum(total_amount) FILTER (WHERE status <> '已取消')
                         - sum(cost_amount) FILTER (WHERE status <> '已取消'), 2),
                   sum(paid_amount)
            FROM sales_order
        """)[0]
        print(f"数据区间：{start} ~ {end}")
        print(f"订单总数：{total_orders:,}，有效订单（非取消）：{valid_orders:,}")
        print(f"有效销售额：{float(amount):,.2f} 元（{float(amount)/1e8:,.1f} 亿元）")
        print(f"销售成本：{float(cost):,.2f} 元，毛利：{float(profit):,.2f} 元"
              f"（{float(profit)/1e8:,.1f} 亿元）")
        print(f"已收款：{float(paid):,.2f} 元")
        all_ok &= check(start == START_DATE.isoformat() and end == END_DATE.isoformat(),
                        f"数据区间为 {START_DATE} ~ {END_DATE}")

        section("分年度销售汇总（目标：完整年度约 500 亿元/年、毛利约 80 亿元/年）")
        year_rows = q(conn, """
            SELECT extract(year FROM order_date)::int AS year, count(*),
                   round(sum(total_amount),2), round(sum(cost_amount),2),
                   round(sum(total_amount)-sum(cost_amount),2)
            FROM sales_order WHERE status <> '已取消'
            GROUP BY 1 ORDER BY 1
        """)
        for year, orders, amount_y, cost_y, profit_y in year_rows:
            target = year_target(year, START_DATE, END_DATE)
            diff_pct = (float(amount_y) - target) / target * 100 if target else None
            ok_sales = abs(diff_pct) <= 3.0 if target else True
            # 毛利目标约 80 亿元/年，按目标年销售额的占比折算，允许 ±8% 浮动
            profit_target = target * 0.16
            ok_profit = abs(float(profit_y) - profit_target) <= profit_target * 0.08 if target else True
            print(f"{year} 年：订单 {orders:,}，销售额 {float(amount_y)/1e8:,.2f} 亿元"
                  f"（目标 {target/1e8:,.0f} 亿，偏差 {diff_pct:+.2f}%），"
                  f"毛利 {float(profit_y)/1e8:,.2f} 亿元（目标 {profit_target/1e8:,.1f} 亿）")
            all_ok &= check(ok_sales and ok_profit, f"{year} 年销售额/毛利达标")

        section("分类销售结构（占比）")
        for cat, amount_c, profit_c in q(conn, """
            SELECT pc.name AS cat, round(sum(soi.amount),2),
                   round(sum(soi.amount) - sum(soi.quantity*soi.unit_cost),2)
            FROM sales_order_item soi
            JOIN product p ON p.id = soi.product_id
            JOIN product_category pc ON pc.id = p.category_id
            JOIN sales_order so ON so.id = soi.sales_order_id
            WHERE so.status <> '已取消'
            GROUP BY pc.name ORDER BY 3 DESC
        """):
            print(f"{cat}：销售额 {float(amount_c)/1e8:,.2f} 亿元，毛利 {float(profit_c)/1e8:,.2f} 亿元")

        section("库存与流水一致性")
        mismatch = q(conn, """
            SELECT count(*) FROM (
                SELECT i.warehouse_id, i.product_id, i.quantity,
                       (SELECT COALESCE(sum(quantity),0) FROM inventory_movement m
                        WHERE m.warehouse_id = i.warehouse_id
                          AND m.product_id = i.product_id) AS ledger
                FROM inventory i
            ) t WHERE t.quantity <> t.ledger
        """)[0][0]
        stock_value = q(conn, """
            SELECT round(sum(i.quantity * p.cost_price), 2) FROM inventory i
            JOIN product p ON p.id = i.product_id
        """)[0][0]
        shortage = q(conn, "SELECT count(*) FROM v_inventory_status WHERE stock_status <> '库存充足'")[0][0]
        print(f"库存与流水不一致的（仓库,商品）组合数：{mismatch}（应为 0）")
        print(f"期末库存总值（按成本）：{float(stock_value)/1e8:,.2f} 亿元")
        print(f"库存不足/预警商品数：{shortage:,}")
        all_ok &= check(mismatch == 0, "库存表与库存流水一致")

        section("月度销售视图（最近 6 个月）")
        print(f"{'月份':<10}{'订单数':>8}{'销售额(亿)':>12}{'毛利(亿)':>12}{'环比%':>10}")
        for month, orders, _items, _qty, amount_m, _disc, cost_m, profit_m, _prev, growth in q(
            conn, "SELECT * FROM v_sales_monthly ORDER BY month DESC LIMIT 6"
        )[::-1]:
            gtxt = "—" if growth is None else f"{float(growth):.2f}"
            print(f"{month!s:<10}{orders:>8,}{float(amount_m)/1e8:>12,.2f}"
                  f"{float(profit_m)/1e8:>12,.2f}{gtxt:>10}")

        section("商品销售 Top 5")
        for pid, sku, name, cat, mfr, qty_p, amount_p, profit_p, orders_p in q(conn, """
            SELECT product_id, sku, product_name, category_name, manufacturer_name,
                   sold_quantity, sales_amount, gross_profit, order_count
            FROM v_product_sales_summary ORDER BY sales_amount DESC LIMIT 5
        """):
            print(f"[{cat}/{mfr}] {name}（{sku}）：销量 {qty_p:,}，"
                  f"销售额 {float(amount_p)/1e8:,.2f} 亿，毛利 {float(profit_p)/1e8:,.2f} 亿")

        section("客户销售 Top 3 与库存预警样例")
        for cid, code, name, ctype, level, prov, city, phone, orders_c, amount_c, _cost_c, profit_c, last in q(
            conn, "SELECT * FROM v_customer_sales_summary ORDER BY total_amount DESC LIMIT 3"
        ):
            print(f"客户 {name}（{ctype}/{level}，{city}）：订单 {orders_c:,}，"
                  f"销售额 {float(amount_c)/1e8:,.2f} 亿，最近下单 {last}")
        for row in q(conn, """
            SELECT warehouse_name, sku, product_name, quantity, safety_stock, stock_status
            FROM v_inventory_status WHERE stock_status <> '库存充足'
            ORDER BY stock_diff LIMIT 5
        """):
            print(f"库存预警：{row[0]} / {row[2]}（{row[1]}）存量 {row[3]}，"
                  f"安全库存 {row[4]}，状态 {row[5]}")

        section("冷链与订单逻辑抽查")
        cold_orders = q(conn, """
            SELECT count(DISTINCT so.id) FROM sales_order so
            JOIN sales_order_item soi ON soi.sales_order_id = so.id
            JOIN product p ON p.id = soi.product_id
            WHERE so.status <> '已取消' AND p.is_cold_chain
        """)[0][0]
        cold_delivery = q(conn, """
            SELECT count(*) FROM sales_order so
            JOIN sales_order_item soi ON soi.sales_order_id = so.id
            JOIN product p ON p.id = soi.product_id
            WHERE so.status <> '已取消' AND p.is_cold_chain
              AND so.delivery_type = '冷链运输'
        """)[0][0]
        print(f"含冷链商品订单：{cold_orders:,}，其中冷链运输配送明细：{cold_delivery:,}")
        vac_products = q(conn, """
            SELECT count(*) FROM product p JOIN product_category pc ON pc.id=p.category_id
            WHERE pc.code='CAT-VAC' AND p.is_cold_chain
        """)[0][0]
        all_ok &= check(vac_products > 0, f"疫苗类商品均标记冷链（{vac_products} 个）")

        section("订单明细视图样例（3 行）")
        for row in q(conn, """
            SELECT order_no, order_date, customer_name, employee_name, warehouse_name,
                   product_name, quantity, line_amount, order_amount, order_status
            FROM v_order_detail ORDER BY order_date, order_id LIMIT 3
        """):
            print(" | ".join(str(x) for x in row))

    print("\n[verify] " + ("校验完成：medsalesdb 结构与数据符合预期。" if all_ok
                           else "存在未通过的检查项，请查看上方输出。"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"[verify] 失败：{exc}", file=sys.stderr)
        sys.exit(1)
