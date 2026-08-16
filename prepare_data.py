"""
DataCo 供应链数据预处理: 星型模型建模
-------------------------------------
原始数据 180,519 行 × 53 列(订单明细级, 2015-2018)
清洗规则:
  - 剔除 PII 列(Email/Password/Street/Zipcode/姓名)
  - 日期解析与衍生(年/季/月/周)
  - 衍生交付指标: 实际发货天数 vs 计划发货天数差值
  - 分析口径: 销售/利润统计剔除取消订单; 交付绩效仅统计已发货订单
输出(Power BI 直接建模):
  dim_date / dim_customer / dim_product / fact_order_items

用法: python prepare_data.py
"""
import os
import pandas as pd

RAW = os.path.join("data", "raw", "DataCoSupplyChainDataset.csv")
OUT = os.path.join("data", "processed")
os.makedirs(OUT, exist_ok=True)

PII_COLS = ["Customer Email", "Customer Password", "Customer Street",
            "Customer Zipcode", "Order Zipcode", "Customer Fname",
            "Customer Lname", "Product Description", "Product Image"]


def main():
    df = pd.read_csv(RAW, encoding="latin-1")
    print(f"[load] {df.shape[0]} 行 × {df.shape[1]} 列")

    # ── 清洗 ──
    df = df.drop(columns=PII_COLS)
    df["order_date"] = pd.to_datetime(df["order date (DateOrders)"],
                                      format="%m/%d/%Y %H:%M")
    df["shipping_date"] = pd.to_datetime(df["shipping date (DateOrders)"],
                                         format="%m/%d/%Y %H:%M")
    df["ship_delay_days"] = (df["Days for shipping (real)"]
                             - df["Days for shipment (scheduled)"])
    df["is_canceled"] = df["Order Status"].isin(["CANCELED", "SUSPECTED_FRAUD"])
    df["is_late"] = df["Late_delivery_risk"].eq(1)

    # ── dim_date ──
    dates = pd.date_range(df["order_date"].min().normalize(),
                          df["order_date"].max().normalize(), freq="D")
    dim_date = pd.DataFrame({"date": dates})
    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
    dim_date["weekday"] = dim_date["date"].dt.day_name()
    dim_date.to_csv(os.path.join(OUT, "dim_date.csv"), index=False)

    # ── dim_customer ──
    dim_customer = (df[["Customer Id", "Customer Segment", "Customer City",
                        "Customer State", "Customer Country"]]
                    .drop_duplicates("Customer Id").reset_index(drop=True))
    dim_customer.to_csv(os.path.join(OUT, "dim_customer.csv"), index=False)

    # ── dim_product ──
    dim_product = (df[["Product Card Id", "Product Name", "Product Price",
                       "Category Id", "Category Name",
                       "Department Id", "Department Name"]]
                   .drop_duplicates("Product Card Id").reset_index(drop=True))
    dim_product.to_csv(os.path.join(OUT, "dim_product.csv"), index=False)

    # ── fact_order_items ──
    # order_day: 纯日期列, 用于与 dim_date 建关系
    # (带时间的 datetime 无法匹配纯日期维度, 这是 Power BI 建模常见坑)
    df["order_day"] = df["order_date"].dt.date
    fact = df[[
        "Order Item Id", "Order Id", "Order Customer Id", "Product Card Id",
        "order_day",
        "Order Item Quantity", "Order Item Product Price",
        "Order Item Discount", "Order Item Discount Rate",
        "Sales", "Order Item Total", "Benefit per order",
        "Order Profit Per Order",
        "Order Status", "Delivery Status", "Shipping Mode",
        "Order Region", "Order Country", "Order State", "Order City", "Market",
        "Latitude", "Longitude",
        "Days for shipping (real)", "Days for shipment (scheduled)",
        "ship_delay_days", "is_canceled", "is_late",
    ]].rename(columns={
        "Order Item Id": "order_item_id", "Order Id": "order_id",
        "Order Customer Id": "customer_id", "Product Card Id": "product_id",
        "Order Item Quantity": "quantity",
        "Order Item Product Price": "unit_price",
        "Order Item Discount": "discount",
        "Order Item Discount Rate": "discount_rate",
        "Sales": "sales", "Order Item Total": "order_total",
        "Benefit per order": "benefit_per_order",
        "Order Profit Per Order": "profit_per_order",
        "Order Status": "order_status", "Delivery Status": "delivery_status",
        "Shipping Mode": "shipping_mode",
        "Order Region": "order_region", "Order Country": "order_country",
        "Order State": "order_state", "Order City": "order_city",
        "Market": "market",
        "Latitude": "latitude", "Longitude": "longitude",
        "Days for shipping (real)": "ship_days_real",
        "Days for shipment (scheduled)": "ship_days_scheduled",
    })
    fact.to_csv(os.path.join(OUT, "fact_order_items.csv"), index=False)

    print(f"[done] dim_date {len(dim_date)} / dim_customer {len(dim_customer)} "
          f"/ dim_product {len(dim_product)} / fact {len(fact)}")
    print(f"[done] 输出目录: {os.path.abspath(OUT)}")

    # ── 核心指标速览(供 README 与简历引用) ──
    valid = fact[~fact["is_canceled"]]
    shipped = fact[fact["order_status"].isin(
        ["COMPLETE", "CLOSED", "SHIPPED", "PROCESSING"])]
    print("\n===== 核心指标 =====")
    print(f"总销售额: ${valid['sales'].sum():,.0f}")
    print(f"总利润:   ${valid['profit_per_order'].sum():,.0f}")
    print(f"订单数:   {valid['order_id'].nunique():,}")
    print(f"客户数:   {valid['customer_id'].nunique():,}")
    print(f"延迟交付率: {shipped['is_late'].mean():.1%}")
    print(f"取消+欺诈率: {fact['is_canceled'].mean():.1%}")
    print("\n按运输方式延迟率:")
    print(shipped.groupby("shipping_mode")["is_late"].mean()
          .round(3).to_string())
    print("\n按市场销售额:")
    print(valid.groupby("market")["sales"].sum()
          .sort_values(ascending=False).round(0).to_string())
    print("\n按部门销售额 Top5:")
    dep = (valid.merge(dim_product[["Product Card Id", "Department Name"]],
                       left_on="product_id", right_on="Product Card Id")
           .groupby("Department Name")["sales"].sum()
           .sort_values(ascending=False).head(5))
    print(dep.round(0).to_string())
    print("\n折扣率与利润相关性:", round(
        valid["discount_rate"].corr(valid["profit_per_order"]), 3))
    neg = valid[valid["profit_per_order"] < 0]
    print(f"亏损订单占比: {len(neg)/len(valid):.1%}, "
          f"亏损订单平均折扣率: {neg['discount_rate'].mean():.1%}, "
          f"整体平均折扣率: {valid['discount_rate'].mean():.1%}")


if __name__ == "__main__":
    main()
