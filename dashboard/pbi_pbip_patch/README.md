# data-test PBIP 修改补丁

## 为什么不是 PBIX

我先尝试直接改 `data-test.pbix`，但 Power BI 对 PBIX 内部报告做了完整性校验：

- 原文件能打开；
- 重新打包但**一个字节都不改**，能打开；
- 只改一个同长度字符（第 2 页 → 第 9 页），Power BI 就报：
  **“此文件已损坏，或使用无法识别的 Power BI Desktop 版本创建的，无法打开。”**

所以 **PBIX 不能这样直接在压缩包里改**。  
可行方式是：**先把 PBIX 另存为 Power BI 项目（PBIP），再替换报告定义文件**。PBIP 就是给外部编辑用的文本格式。

## 这个补丁做了什么

| 修改 | 说明 |
|---|---|
| 删除第 1 页试作页 | 原第 1 页是“有送达日期订单数 + 运费”的错误组合图 |
| 页面改名 | 01 月度趋势 / 02 品类结构 / 03 支付构成 / 04 品类规模与体验 / 05 州级地图 / 06 配送时效 / 07 箱线图与雷达 / 08 Cohort 留存 / 09 卖家集中度 |
| 打开页 | 改为 01 月度趋势 |
| 图 1 排序 | 改为按 `月份` 升序，不再按 `核心_商品GMV` 升序 |
| 图 6 排序 | `送达时长排序` 改为升序，不再 60 天以上在前 |
| 图 5 地图 | 增加 `Color` 角色（迟到率），并设置绿→红渐变 |
| 图 8 Cohort | 给 `留存率` 增加条件格式背景色 + 标题 |
| 图 7 箱线图 | 标题改为“Top 6 品类订单金额分布（静态图）” |
| 图 10 雷达 | 插入 `10_state_radar.png`，与箱线图同页 |
| 图 9 卖家帕累托 | 新增卖家页：`卖家排名` + `商品GMV` + `累计GMV占比`，Top 100 |

## 使用步骤

### 1. 先另存为 PBIP

1. 用 Power BI Desktop 打开原文件：`F:\power bi\data-test.pbix`
2. `文件` → `另存为`
3. 保存类型选 **Power BI 项目 (*.pbip)**
4. 保存到新文件夹，例如：

```text
F:\power bi\data-test-pbip\data-test.pbip
```

> 如果“另存为”里没有 `.pbip`：  
> `文件 → 选项和设置 → 选项 → 预览功能` → 勾选 **Power BI 项目 (.pbip)**，重启 Power BI。

### 2. 关闭 Power BI

应用补丁前必须关闭 Power BI，否则 PBIP 文件会被占用。

### 3. 运行补丁

在 PowerShell 里执行：

```powershell
cd "E:\workbuddy-space\ecommerce-analysis\dashboard\pbi_pbip_patch"
powershell -ExecutionPolicy Bypass -File .\apply_patch.ps1 -PbipPath "F:\power bi\data-test-pbip\data-test.pbip"
```

脚本会自动：

- 找到 `data-test.Report` 文件夹；
- 备份原 `definition` 和 `StaticResources` 到 `pbip_backup_时间戳`；
- 删除旧的第 1 页；
- 覆盖页面、视觉对象、`report.json`；
- 复制雷达图、箱线图、主题资源。

### 4. 打开 PBIP

用 Power BI Desktop 打开：

```text
F:\power bi\data-test-pbip\data-test.pbip
```

正常应该看到 9 页，打开页是「01 月度趋势」。

### 5. 如果打开报错

把备份目录里的 `definition` 和 `RegisteredResources` 覆盖回 `data-test.Report`，即可恢复原样。  
然后把报错截图发我，我按报错定位是哪一条 PBIR 配置不兼容。

## 补丁目录

```text
pbi_pbip_patch/
├─ apply_patch.ps1
├─ definition/
│  ├─ report.json
│  ├─ version.json
│  └─ pages/
│     ├─ pages.json
│     ├─ 03642f...（01 月度趋势）
│     ├─ 383f9d...（02 品类结构）
│     ├─ bbca9d...（03 支付构成）
│     ├─ f6d2d0...（04 品类规模与体验）
│     ├─ 03f462...（05 州级地图）
│     ├─ aa6ba3...（06 配送时效）
│     ├─ d7985b...（07 箱线图与雷达）
│     ├─ b2e307...（08 Cohort 留存）
│     └─ a4a3c3...（09 卖家集中度）
└─ StaticResources/
   └─ RegisteredResources/
      ├─ 07_category_boxplot...png
      ├─ 10_state_radar.png
      └─ Olist...json
```

## 说明

- 补丁只改**报告层**，不动 `DataModel`、度量值和数据源。
- 图 9 前提：模型里已有 `seller_kpis_zh`（我已从原 PBIX 的模型图确认存在）。
- 图 5 的颜色用了 `迟到率` 度量值；如果 PBIP 打开后地图颜色没生效，手动把 `迟到率` 拖到「颜色饱和度」即可。
- 图 8 的条件格式是 PBIR 的 `Conditional` 规则；如果 PBIP 报不兼容，把 `b2e307.../visual.json` 的 `objects.values` 去掉，再用 Power BI 手动设置渐变背景色即可。