# 项目可视化与可解释性指南

本页用思维导图、数据流、指标树、业务决策树和现有看板截图解释 DataCo 项目的分析逻辑。图中的业务结果均来自仓库当前 README，原始数据需要在本地重新下载。

## 图 1：项目能力思维导图

```mermaid
flowchart TD
    ROOT((DataCo 供应链分析))
    ROOT --> DATA[数据处理]
    ROOT --> MODEL[星型模型]
    ROOT --> KPI[指标体系]
    ROOT --> BI[Power BI 看板]
    ROOT --> INSIGHT[业务结论]

    DATA --> D1[180,519 行订单明细]
    DATA --> D2[PII 字段剔除]
    DATA --> D3[日期与延迟派生]
    DATA --> D4[取消/欺诈标记]

    MODEL --> M1[dim_date]
    MODEL --> M2[dim_customer]
    MODEL --> M3[dim_product]
    MODEL --> M4[fact_order_items]

    KPI --> K1[销售额与利润]
    KPI --> K2[客单价与利润率]
    KPI --> K3[延迟交付率]
    KPI --> K4[亏损订单占比]

    BI --> B1[经营总览]
    BI --> B2[交付绩效]
    BI --> B3[品类利润]
    BI --> B4[区域市场]

    INSIGHT --> I1[Europe / LATAM / Pacific Asia]
    INSIGHT --> I2[First Class 延迟率 100%]
    INSIGHT --> I3[亏损订单约 18.7% 且分布广泛]
```

## 图 2：ETL 与星型模型

```mermaid
flowchart LR
    CSV[DataCoSupplyChainDataset.csv] --> CLEAN[Pandas 清洗]
    CLEAN --> PII[剔除 PII 列]
    CLEAN --> DATE[解析日期]
    CLEAN --> FLAG[取消 / 延迟 / 发货偏差]
    PII --> DIM[维度表]
    DATE --> DIM
    FLAG --> FACT[事实表]
    DIM --> DD[dim_date]
    DIM --> DC[dim_customer]
    DIM --> DP[dim_product]
    FACT --> FO[fact_order_items]
    DD --> PBI[Power BI]
    DC --> PBI
    DP --> PBI
    FO --> PBI
```

`order_day` 使用纯日期与 `dim_date[date]` 关联，避免带时间的 datetime 无法命中日期维度。

## 图 3：指标口径与可解释性树

```mermaid
flowchart TD
    SALES[有效销售额] --> SALES1[剔除取消和欺诈订单]
    PROFIT[有效利润] --> PROFIT1[按订单利润字段汇总]
    AOV[平均客单价] --> AOV1[有效销售额 / 有效订单数]
    MARGIN[利润率] --> MARGIN1[有效利润 / 有效销售额]
    LATE[延迟交付率] --> LATE1[已发货订单中 is_late = TRUE]
    LOSS[亏损订单占比] --> LOSS1[有效订单中 profit_per_order < 0]

    SALES1 --> CAVEAT[Power BI 筛选器必须保持口径一致]
    LATE1 --> CAVEAT
    LOSS1 --> CAVEAT
```

## 图 4：四页看板的业务决策树

```mermaid
flowchart LR
    Q[经营问题] --> Q1[整体规模怎样]
    Q --> Q2[为什么交付差]
    Q --> Q3[利润为什么偏低]
    Q --> Q4[市场如何分配资源]

    Q1 --> P1[经营总览页]
    Q2 --> P2[交付绩效页]
    Q3 --> P3[品类利润页]
    Q4 --> P4[区域市场页]

    P2 --> A1[运输方式 × 区域矩阵]
    P2 --> A2[延迟率趋势与地图]
    P3 --> A3[折扣率 × 利润散点]
    P3 --> A4[部门亏损分布]
```

## 图 5：核心结论与风险地图

```mermaid
flowchart TD
    ROOT((核心结论))
    ROOT --> S1[规模]
    ROOT --> S2[交付]
    ROOT --> S3[利润]
    ROOT --> S4[区域]

    S1 --> S1A[销售额约 35.2M / 利润约 3.8M]
    S2 --> S2A[延迟率约 57.2%]
    S2 --> S2B[First Class 延迟率 100%]
    S3 --> S3A[亏损订单占比约 18.7%]
    S3 --> S3B[各部门亏损分布接近]
    S4 --> S4A[三大市场合计约 80%]

    S2B --> RISK1[承诺时效与实际产能错配假设]
    S3B --> RISK2[全局定价和折扣策略问题]
    S4A --> RISK3[区域集中带来资源和风险集中]
```

## 既有看板截图

### 经营总览

![经营总览](images/page1_overview.png)

解释：用于观察销售额、利润、客户结构和市场分布，是后续页面的总体基线。

### 交付绩效

![交付绩效](images/page2_delivery.png)

解释：这是核心业务故事页，展示运输方式与延迟率的关系以及区域/时间维度下的履约差异。

### 品类与利润

![品类利润](images/page3_profit.png)

解释：通过分解树和散点图定位亏损品类，用于验证“亏损是否集中在单一部门”的假设。

### 区域市场

![区域市场](images/page4_market.png)

解释：展示三大市场的收入贡献和区域分布，为资源分配与市场策略提供依据。

## 视觉阅读顺序

1. 图 1 先确认数据、模型、指标和看板模块。
2. 图 2 理解 ETL 与星型模型。
3. 图 3 解释每个指标的过滤口径。
4. 图 4 看清四页看板如何对应经营问题。
5. 图 5 和四张截图用于解释结论、风险与业务行动建议。