# 美赛（MCM/ICM）论文写作完整指南

## 评分维度（评审视角）

美赛评审两轮：Triaging（粗评，~10 分钟/篇，主要看 Summary + 图）→ Final judging。获奖（M 奖以上）论文共性：

1. **Summary 惊艳**：粗评阶段几乎只看 Summary 和图表，决定是否晋级
2. **故事线闭环**：Problem → Assumptions → Model → Validation → Conclusion，环环相扣
3. **图表专业**：一眼看上去像期刊论文，不像课程作业
4. **回答了所有问题**：逐条对照原题的每个 requirement
5. **有模型验证**：敏感性分析、误差分析、与现实数据对比，三选一以上

## Summary Sheet 写作公式（最重要的一页）

长度：2/3 页～1 页。结构：

1. **开头段（2-3 句）**：一句话点明问题重要性 + 一句话概括做了什么
   - 模板："We develop a [方法] model to [目标]. Our model addresses [问题核心] by [关键创新点]."
2. **分问题概述（每问 2-4 句）**：用了什么模型 → 得到什么关键结果（**必须含具体数值**）
   - 忌：只写方法不写结果。评委要看数字。
3. **亮点段**：模型的创新点、验证方法、关键结论
4. **结尾句**：一句政策建议或最终 takeaway

要点：
- Summary 最后写（全文完成后再提炼）
- 加粗关键词（**Key results:** ...）帮助评委扫读
- 不出现公式、不出现引用
- 自查：把 Summary 单独给一个不知情的人看，能否看懂全部工作？

## 各章节写法

### 1. Introduction（1.5-2 页）
- **Background**：从宏观到具体，3-4 句背景 + 问题严重性（可引数据）
- **Problem Restatement**：用自己的话重述问题，列出要回答的 3-4 个子问题
- **Literature/Approach Overview**（可选）：简述已有方法的不足
- **Our Work**：分点列出做了什么（"First, we ... Second, we ... Finally, we ..."），**强烈建议配一张框架流程图**（Framework diagram）
- 段末可加论文结构说明（"The remainder of this paper is organized as follows..."）

### 2. Assumptions and Justifications
- 每条假设 = 假设陈述 + 一句 justification（为什么合理）
- 用编号列表，5-8 条为宜
- 好假设：简化问题但不损失本质；坏假设：为凑数而写
- 常见句型："To simplify the problem, we assume that ... This is reasonable because ..."

### 3. Notations
- 用三线表（booktabs）：Symbol | Definition | Units
- 只列全文通用的符号；局部符号在使用处定义

### 4. Model Establishment（核心，6-10 页）
每个子模型的叙事模板：
1. **动机**：为什么需要这个模型？解决哪个子问题？
2. **预备/假设**：本模型特有的假设
3. **推导**：公式逐步建立，每步配文字解释（"The first term represents ..."）
4. **求解方法**：解析解/数值算法/仿真，说明工具与参数
5. **结果**：数值结果 + 图表 + 解读

写作技巧：
- 公式居中编号，重要变量斜体
- 每放一个公式，后面跟一句解释物理/实际意义
- 模型间的衔接要有过渡句（"Having determined X, we now model Y ..."）

### 5. Sensitivity / Robustness Analysis（获奖分水岭）
- 选 2-3 个关键参数，做参数扰动（±10%、±20%）
- 呈现方式：敏感性曲线图、热图、蜘蛛图（tornado plot）
- 结论句型："Our model remains stable when [参数] varies within [范围], indicating robustness. However, it is sensitive to [参数], which suggests ..."
- 也可做：改变某个假设看结论是否翻转（assumption relaxation）

### 6. Strengths and Weaknesses
- 各 3-4 条，bullet list
- Strengths 要具体（"The model incorporates spatial heterogeneity, which previous approaches ignored"）
- Weaknesses 要诚实但要带补救（"Although we assume constant X, this could be addressed by ..."）

### 7. Conclusion
- 1 页以内：回顾问题 → 主要结论（带数值）→ 意义与展望
- 不引入新内容

### 8. Memo / Letter（ICM 常要求）
- 给非技术读者（政策制定者、管理者），1-2 页
- 零公式、零术语，直接给建议和数字
- 语气：自信、简洁、可执行

### 9. References & Appendices
- 引用格式统一（APA 或编号制），8-15 条为宜
- 附录放关键代码（核心部分即可，不必全放）

## 学术英语要点

### 时态规则
- 普遍真理/模型描述 → 现在时（"The model assumes that ..."）
- 本文做了什么 → 现在时或过去时均可，全文统一（推荐现在时："we develop", "we simulate"）
- 引用他人工作 → 过去时（"Smith et al. proposed ..."）

### 高频句型
- 引出模型："To capture [现象], we model [对象] as ..."
- 解释参数："where $k$ denotes the rate of ..., and $T$ is ..."
- 呈现结果："As shown in Figure 3, ... increases monotonically with ..."
- 讨论含义："This suggests that ...", "A plausible explanation is ..."
- 承接："Building on this result, we further ..."

### 常见错误（要避免）
- 中式长句：一句超过 3 行必拆
- 口语化：a lot of → substantial；big → significant；get → obtain
- 主语滥用 "it"：指代不清时重复名词
- 图引用大小写：句中 "Figure 2"（大写 F）

## 排版建议
> 详细的 COMAP 硬规则、篇幅预算表与**易错清单**见 `mcm-format-rules.md`——那是格式落地的唯一依据。

- LaTeX 首选（模板：官方 mcmthesis 或 easymcm）；Word 亦可但公式与交叉引用费时
- 页边距 ≥ 1 inch，11-12pt 字体，单栏
- 页眉含 Team Control Number + 页码（"Team # 26xxxxx  Page 5 of 24"），**每页都有，第 1 页也有**
- **不能出现学校、姓名等身份信息**
- 2026 起必须附 `Report on Use of AI`（同一 PDF、25 页之后、不计入页数），正文另需内联披露 + 参考文献条目

## Final Checklist（提交前逐项打钩）

- [ ] Summary 独立成篇、含关键数值结果、无公式引用
- [ ] 原题的每个 requirement 都在正文中有明确对应的章节/段落
- [ ] 每条假设有 justification
- [ ] 符号表完整，符号前后一致
- [ ] 有敏感性或鲁棒性分析（含图）
- [ ] 有模型验证（与现实数据对比/案例检验/误差分析）
- [ ] Strengths & Weaknesses 各 ≥ 3 条
- [ ] 所有图表：有编号、有 caption、被正文引用、Nature 风格、高分辨率
- [ ] 有框架流程图（Introduction 处）
- [ ] 结论含具体数值，不是空话
- [ ] 全文语法检查通过，时态统一
- [ ] 页数 ≤ 25，页眉信息正确，无身份信息
- [ ] 2026：正文有 AI 披露段 + 参考文献有 AI 条目 + 同一 PDF 末尾附 Report on Use of AI
- [ ] 每条参考文献都在正文被引用过（零引用 = 凑数）
- [ ] 公式从 (1) 连续编号（不要按章跳号）、表格三线表无竖线
- [ ] 跑过 `scripts/check_mcm_format.py`，全部 PASS
- [ ] 参考文献格式统一
