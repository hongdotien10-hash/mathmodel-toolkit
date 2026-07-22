---
name: 编译论文
description: 使用xelatex编译LaTeX论文，自动修复编译错误，执行排版优化
trigger:
  - "编译论文"
  - "编译"
  - "生成PDF"
  - "xelatex"
---

# 编译论文

## 目的

使用 xelatex 编译论文 LaTeX 文件为 PDF，自动修复错误，直到编译成功且无任何问题。

## 编译流程

### Step 1：首次编译

```bash
cd 论文
xelatex -interaction=nonstopmode 论文.tex
xelatex -interaction=nonstopmode 论文.tex
```

### Step 2：检查错误

```bash
# 检查编译错误（必须为0）
grep -c 'Error' 论文.log

# 检查警告
grep -c 'Warning' 论文.log

# 检查溢出
grep 'Overfull\|Underfull\|Float too large' 论文.log
```

### Step 3：错误修复

| 错误类型 | 常见原因 | 修复方法 |
|----------|----------|----------|
| `Undefined control sequence` | 命令拼写错误或缺少包 | 检查拼写，添加必要包 |
| `Missing \begin{document}` | 正文前有输出内容 | 将内容移到 `\begin{document}` 后 |
| `File not found` | 引用文件不存在 | 检查路径和文件名 |
| `Font not found` | 缺少字体 | 检查 fonts/ 目录 |
| `Misplaced \noalign` | 表格中 `\\` 前有 `\centering` 干扰 | 确保 `>{\centering\arraybackslash}` 不省略 |
| 中文渲染警告 | 字体缺少字形 | 调整字体配置 |
| `Overfull \hbox` | 表格/段落过宽 | 缩短内容或调整宽度 |
| `Float too large` | 图表过大 | 调整尺寸 |

### Step 4：重编译

修复后重新执行：
```bash
xelatex -interaction=nonstopmode 论文.tex
xelatex -interaction=nonstopmode 论文.tex
```

重复直到 `grep -c 'Error' 论文.log` = 0。

## 排版优化（编译成功后自动执行）

### 检查项

```bash
grep 'Overfull\|Underfull\|Float too large' 论文.log
```

### 修复策略

| 问题类型 | 修复方法 |
|----------|----------|
| Overfull hbox | 缩短表格文字、调整 `p{}` 宽度 |
| Underfull hbox | 适当拉宽、调整断行 |
| Float too large | `width=0.75\textwidth` 等比缩小 |
| 大面积空白 | 调整段落密度、图片位置参数 |
| 图表位置不当 | 调整 `[ht]` / `[htb]` 参数 |

### 摘要一页验证

```bash
PAGE=$(grep 'abstract:end' 论文/论文.aux | grep -oE '\{[0-9]+\}' | head -1 | tr -d '{}')
if [ "$PAGE" -gt 1 ]; then
  echo "摘要超出一页（第${PAGE}页），需缩减"
fi
```

若 `PAGE > 1`：按比例缩减各问题段字数，重新编译直到 `PAGE=1`。

### 优化循环

```
修复 → xelatex ×2 → grep 检查 → 仍有问题则继续修复
直到日志干净：无 Error、无 Overfull、无 Underfull、排版紧密
```

## 最终验证清单

- [ ] `grep -c 'Error' 论文.log` = 0
- [ ] 摘要 ≤ 1 页
- [ ] 所有 `\cite{}` 对应 `\bibitem{}`
- [ ] 所有图表被正文引用
- [ ] 无 Overfull/Underfull
- [ ] 图表位置正常，无大面积空白
- [ ] 中文渲染正常

## 输出

编译成功的 `论文.pdf` 文件。全部自动执行，不询问用户。