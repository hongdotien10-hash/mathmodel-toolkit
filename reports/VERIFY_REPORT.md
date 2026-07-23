# 验证与验收报告

## 数值一致性校验

| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| Q1 最短距离 | 582 km | 582.0 km | ✅ 完全一致 |
| Q1 所有地点访问 | 14个 | 14个 | ✅ |
| Q1 回路闭合 | tour[0]==tour[-1] | True | ✅ |
| Q2 车辆距离 | <Q1值(无人机分担) | 370km | ✅ 合理 |
| Q4 分区不重叠 | 每个地点恰好1个集散点 | True | ✅ |

## 可复现性

```bash
cd code/
python problem1.py   # Q1: 582km
python problem2.py   # Q2+Q3
python problem4.py   # Q4: 选址
```

## 图表完整性

| 文件 | 类型 | 状态 |
|------|------|------|
| figures/q1_tsp_route.pdf | TSP路线图 | ✅ |
| figures/q2_drone_route.pdf | 车+无人机路线图 | ✅ |
| figures/q3_drone_route.pdf | 500kg方案图 | ✅ |
| figures/q4_depot_selection.pdf | 选址图 | ✅ |
| figures/comparison_all.pdf | 四问对比图 | ✅ |
| figures/fig_roadmap.pdf | 技术路线图 | ✅ |
| figures/fig_flow_q1.pdf | Q1算法流程图 | ✅ |
| figures/fig_roadmap.drawio | 路线图DrawIO源文件 | ✅ |
| figures/fig_flow_q1.drawio | 流程图DrawIO源文件 | ✅ |

## 论文编译

```bash
cd paper/
xelatex main.tex
xelatex main.tex  # 两遍解决交叉引用
```

## 已知限制

- DrawIO CLI未安装，流程图PDF由matplotlib生成
- 中文字体需系统安装（SimSun/SimHei）
- 附件2数据仅14地点（Q4需要30地点，当前用14地点演示算法）
- 无人机任务分配为简化贪心模型
