# 方案

## 用户偏好

- 排版引擎：LaTeX (xelatex)
- 竞赛类型：电工杯（兼容国赛/美赛）
- 论文语言：中文
- 子问题数量：4个（Q1车辆配送、Q2车+无人机、Q3容量变化、Q4选址+路径）
- 正确答案参考：Q1最短路径约582km，配送时间约6.32h

## workflow

统一由 `skills/mcm-math-modeling` 单技能驱动，阶段细则见 `skills/mcm-math-modeling/references/stage-*.md`。

| step | 阶段 | 参考文档 | 作用 |
|------|------|----------|------|
| 0. 入口与偏好确认 | Stage 0 | `SKILL.md` | 确认排版引擎、竞赛、语言、子问题数，生成 plan.md 与 todo.md |
| 1. 赛题分析与建模设计 | Stage 1 | `references/stage-2-analysis-modeling.md` | 读取题面和数据，拆解4问，建数学模型 |
| 2. 编程实现和图表生成 | Stage 2 | `references/stage-3-coding-visual.md` | 写求解代码，跑结果，生成图表 |
| 3. 流程与架构图绘制 | Stage 3 | `references/stage-4-drawio.md` | 画技术路线图、算法流程图 |
| 4. 竞赛论文撰写 | Stage 4 | `references/stage-5-writing.md` | 基于真实结果写LaTeX论文 |
| 5. 验证和验收 | Stage 5 | `references/stage-6-verity.md` | 检查数值一致性、图表完整性 |

阶段推进由 `scripts/verify_checkpoint.py` 的 CP1/CP2/CP3 门禁强制校验，非零退出即阻断。
