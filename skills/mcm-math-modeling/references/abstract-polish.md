# Summary Sheet（摘要）精品打磨指南

美赛评审中，Summary Sheet 的重要性怎么强调都不为过。大多数评委在 10 分钟内决定一篇论文的去留，而他们主要看的就是这一页。

## Summary 的硬信息清单

论文主体写完后，逐条提取以下内容，缺一条都不完整：

| 必须包含 | 说明 |
|---|---|
| 问题背景（1-2 句） | 点明题目重要性和你要解决的核心问题 |
| 每个子问题的方法 | 模型名或核心算法，一句话概括 |
| 每个子问题的关键结果 | **必须含具体数值和单位** |
| 模型验证/敏感性发现 | 至少 1 条关键结论 |
| 模型亮点或创新 | 1-2 条，让评委记住你 |

**铁律**：Summary 里的每个数值必须能追溯到正文/结果文件；每个子问题必须覆盖；不写复杂公式和引用。

## 结构模板（可直接套用）

```
[第 1 段] 问题背景和总体思路（1-2 句）
[第 2 段] 问题一：方法 + 模型 + 关键结果
[第 3 段] 问题二：方法 + 模型 + 关键结果（注意与问题一的递进关系）
[第 N 段] 问题 N：...
[倒数第 2 段] 模型检验与灵敏度分析关键发现
[最后 1 段] 模型特点与创新点总结
```

## 写作要求

- 不用 "本文"、"我们" 开头的空泛句子
- 不重述题面（假设评委已看过题目）
- 每个数值说清楚单位/含义
- 每个方法选择给出简短理由
- 多用短句，少用复杂从句（避免机器翻译感）
- 子问题之间要有递进词："Building on ...", "To further ...", "Finally, ..."

## 多版本打磨流程

### Step 1：生成初稿 V1
从信息清单直接翻译成英文，不纠结措辞。

### Step 2：六维评分

| 维度 | 满分 5 | 检查点 |
|---|---|---|
| 完整性 | ? | 每个子问题都有方法+模型+结果？ |
| 数值准确性 | ? | 数值与正文一致？单位标注？ |
| 逻辑连贯性 | ? | 子问题间有递进关系？ |
| 创新呈现 | ? | 亮点清晰、让人记住？ |
| 简洁性 | ? | 是否有冗余可删？ |
| 冲击力 | ? | 评委读完是否想继续看正文？ |

### Step 3：生成差异化版本

| 版本 | 策略 |
|---|---|
| V2 逻辑强化版 | 重点改进逻辑连贯性和子问题递进 |
| V3 亮点突出版 | 重点强化创新点和冲击力 |
| V4 精简版 | 压缩到最短篇幅同时保持信息完整 |

### Step 4：混合优化
取各版最优句子，拼成最终版，并标注每段来源。

### Step 5：替换与一致性检验

- 替换到论文 Summary Sheet
- 用下表核对摘要与正文数值一致：

| 检查项 | 摘要中的值 | 正文对应位置 | 是否一致 |
|---|---|---|---|
| 问题一误差 | ... | 第 X 节 | ✅ |
| 问题二最优值 | ... | 第 Y 节 | ✅ |

任何不一致必须修正。

## 常见问题对照

| 问题 | 坏例 | 好例 |
|---|---|---|
| 空泛开头 | With the development of ..., the problem is increasingly important. | We develop a differential-equation model to optimize the distribution of charging stations. |
| 只列方法不给结果 | AHP is used for evaluation. | The AHP evaluation ranks Scenario 3 highest (score 0.78). |
| 数值无单位 | The error is 3.2. | The prediction error is 3.2% (MAPE). |
| 子问题间无递进 | For problem 1, ... For problem 2, ... | Building on the optimal allocation from Problem 1, Problem 2 further introduces demand uncertainty. |
| 亮点淹没 | buried in the middle of a paragraph | Our key contributions are threefold: ... |
| 过度谦虚/自信 | relatively accurate / extremely perfect | The error is kept below 5%, meeting the required accuracy. |

## 篇幅与格式

- 美赛 Summary Sheet **严格限制 1 页**
- 建议字数：250-450 词
- 可适度加粗关键数值和结论句，帮助评委扫读
- 不要出现公式、表格、引用
