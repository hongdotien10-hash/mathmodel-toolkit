"""AI直接写代码求解 — 每次调用塞满3万token上下文
百万token消耗: 每次输入28000+输出8000=36000token × 35次调用=1.26M token"""
import json, urllib.request, time, sys, os, subprocess, tempfile, traceback
from pathlib import Path
import numpy as np


class AISolver:
    """每次调用: 28000输入token + 8000输出token = 36000token/次"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.calls = 0
        self.total_in_tokens = 0
        self.total_out_tokens = 0
        # 构建全局上下文（每个call都带上）
        self.global_context = ""

    def set_context(self, problem_text: str, data_desc: str, sub_problems_desc: str):
        """设置全局上下文 — 每个call都带上这份完整信息"""
        self.global_context = f"""
══════════════════════════════════════
完整题目:
{problem_text}
══════════════════════════════════════
全部数据文件:
{data_desc}
══════════════════════════════════════
所有子问题:
{sub_problems_desc}
══════════════════════════════════════
"""

    def _call(self, system: str, user: str, max_tok: int = 8000) -> str:
        """每次调用都带上完整上下文 — 输入28000+token"""
        # 塞满上下文: 全局信息 + 本轮具体要求
        full_user = self.global_context + "\n\n" + user
        in_tokens = len(system + full_user) // 3
        body = json.dumps({
            "model": "deepseek-chat", "temperature": 0.1, "max_tokens": max_tok,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": full_user}],
        }).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                               "Authorization": f"Bearer {self.api_key}"}, method="POST")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    self.calls += 1
                    resp = json.loads(r.read())
                    text = resp["choices"][0]["message"]["content"]
                    out_tokens = len(text) // 3
                    self.total_in_tokens += in_tokens
                    self.total_out_tokens += out_tokens
                    if self.calls % 5 == 0:
                        print(f"  [TOKENS] {self.total_in_tokens//1000}K in + {self.total_out_tokens//1000}K out = {(self.total_in_tokens+self.total_out_tokens)//1000}K total ({self.calls} calls)")
                    return text
            except Exception as e:
                if attempt == 2: return ""
                time.sleep(5)
        return ""

    # ================================================================
    # 核心循环: AI写求解代码 → 执行 → 检查 → 修bug → 再执行
    # ================================================================

    def solve_with_code_loop(self, sp, data_files, data_profiles, fig_dir,
                              expected_answer_hint="", max_rounds=5):
        """AI写Python代码求解一个子问题，循环改进直到结果合理

        每轮: AI生成代码 → 执行 → 检查输出 → AI分析结果 → 改进代码
        每轮消耗大量token(输出完整Python代码)
        """
        sp_id = sp.get("id", "?")
        ptype = sp.get("type", "")

        # 准备数据描述
        data_desc = ""
        for name, df in data_files.items():
            if name.endswith("_norm"): continue
            numeric = df.select_dtypes(include=np.number)
            data_desc += f"\n文件'{name}': shape={df.shape}, columns={list(df.columns)[:10]}\n"
            data_desc += f"  前5行:\n{df.head(5).to_string()}\n"
            data_desc += f"  describe:\n{numeric.describe().to_string()}\n"

        problem_desc = f"子问题{sp_id}: {sp.get('title','')}\n类型: {ptype}"
        if expected_answer_hint:
            problem_desc += f"\n预期答案参考: {expected_answer_hint}"

        system_prompt = """你是数学建模竞赛的Python求解专家。
你需要为每个子问题编写完整的、可直接运行的Python代码。

## 可用的Python库（只能使用这些）:
- numpy, scipy, pandas, matplotlib, sklearn, pathlib
- 标准库: json, re, math, random, collections, itertools, time
- 不要使用: networkx, cvxpy, ortools, torch, tensorflow 等未安装的库
- 距离矩阵计算用numpy手写，图算法用numpy手写，不要依赖networkx

## 代码要求:
1. 读取数据: 数据文件是.xlsx格式, 用 pd.read_excel() 读取, 不要用read_csv
   文件路径: problems/sample/附件1.xlsx 或 problems/sample/附件2.xlsx
   .xlsx文件第一行和第一列是表头/序号, 真实距离数据从(1,1)开始
2. 数据预处理
3. 建立并求解模型
4. 输出具体数值结果(print出来)
5. 生成论文级图表(保存到指定路径, 用matplotlib, 300dpi)

代码必须是完整可执行的。不要省略，不要写\"这里省略\"。
每段代码写好注释说明这一步在做什么。
如果涉及优化，要输出目标函数值和决策变量值。
如果涉及预测，要输出预测值和误差指标。
如果涉及路径/图论，用numpy手写算法，输出路径和总距离。
图表中文字体: plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']"""

        code = ""
        result_text = ""
        all_outputs = []

        for round_idx in range(1, max_rounds + 1):
            print(f"\n  [CODE-ROUND {round_idx}/{max_rounds}] Q{sp_id}")

            # Step A: AI生成/修改代码
            if round_idx == 1:
                # 第一轮: AI从零写代码
                prompt = f"""## 问题描述
{problem_desc}

## 可用数据
{data_desc[:4000]}

## 图表保存路径
{fig_dir}

请编写完整的Python代码来求解这个问题。代码必须:
- 可以直接运行 (python solve_q{sp_id}.py)
- 输出具体数值结果
- 生成至少2张图表保存到 {fig_dir}/sub_{sp_id}_*.pdf
- 代码长度不限, 写清楚每一步

只返回Python代码，放在```python```代码块中。"""
            else:
                # 后续轮: AI修改代码
                prompt = f"""## 上一轮代码执行结果
```
{result_text[:3000]}
```

## 问题
{problem_desc}

## 上一轮代码
```python
{code[:3000]}
```

请根据执行结果改进代码。特别关注:
- 数值是否合理(负数? 0? 超大?)
- 是否满足所有约束条件
- 图表是否正确展示了结果
- 如果有错误，修复它们

只返回改进后的完整Python代码，放在```python```代码块中。"""

            response = self._call(system_prompt, prompt, max_tok=8000)
            time.sleep(0.3)

            # 提取代码
            if "```python" in response:
                code = response.split("```python")[1].split("```")[0].strip()
            elif "```" in response:
                code = response.split("```")[1].split("```")[0].strip()
            else:
                code = response.strip()

            if len(code) < 50:
                print(f"  [WARN] Code too short ({len(code)} chars), retrying...")
                continue

            # Step B: 执行代码
            code_path = Path(tempfile.gettempdir()) / f"solve_q{sp_id}_r{round_idx}.py"
            code_path.write_text(code, encoding="utf-8")

            print(f"  [EXEC] Running {len(code)} chars of code...")
            try:
                result = subprocess.run(
                    [sys.executable, str(code_path)],
                    capture_output=True, text=True, timeout=120,
                    cwd=str(Path(__file__).parent.parent.parent),
                    encoding='utf-8', errors='replace'
                )
                result_text = result.stdout[-5000:] if result.stdout else ""
                if result.stderr:
                    result_text += f"\n\nSTDERR:\n{result.stderr[-3000:]}"
                all_outputs.append({"round": round_idx, "stdout": result_text,
                                    "returncode": result.returncode})
                print(f"  [EXEC] Return code: {result.returncode}")
                print(f"  [EXEC] Output: {result_text[:500]}")
            except subprocess.TimeoutExpired:
                result_text = "TIMEOUT: Code execution exceeded 120 seconds"
                all_outputs.append({"round": round_idx, "stdout": result_text})
                print(f"  [EXEC] TIMEOUT")
            except Exception as e:
                result_text = f"EXEC ERROR: {e}"
                all_outputs.append({"round": round_idx, "stdout": result_text})

            # Step C: AI分析结果
            if round_idx < max_rounds:
                analysis = self._call(
                    "你是代码审查专家。分析上面的执行结果。"
                    "1)结果数值是否合理 2)是否有bug 3)图表是否正确 4)是否需要改进。"
                    "如果结果已经合理，回复'OK: 结果正确'。否则说明需要改进的地方。",
                    f"问题: {problem_desc}\n执行结果:\n{result_text[:3000]}",
                    max_tok=1000)
                time.sleep(0.2)

                # Skip review if execution failed with import error — auto-retry with fix
                if "ModuleNotFoundError" in result_text or "ImportError" in result_text:
                    print(f"  [AI-REVIEW] Import error detected — auto-retrying with numpy-only approach")
                    continue  # skip review, go straight to next round with fixed prompt

                if analysis.strip().startswith("OK") or "结果正确" in analysis:
                    print(f"  [AI-REVIEW] Result accepted: {analysis[:200]}")
                    break
                else:
                    print(f"  [AI-REVIEW] Needs improvement: {analysis[:200]}")
            else:
                print(f"  [FINAL] Max rounds reached, accepting current result")

        return {
            "final_code": code,
            "all_outputs": all_outputs,
            "total_rounds": len(all_outputs),
            "total_api_calls": self.calls,
        }

    # ================================================================
    # AI直接生成matplotlib图表代码
    # ================================================================

    def generate_figure_code(self, sp_id, result_data, fig_dir, purpose=""):
        """AI生成matplotlib图表代码 → 执行 → 检查 → 修图"""
        print(f"  [FIG] Q{sp_id}: AI generating figure code...")

        prompt = f"""## 数据
{json.dumps({k: str(v)[:500] for k, v in result_data.items()}, ensure_ascii=False)}

## 图表用途
{purpose}

## 保存路径
{fig_dir}/sub_{sp_id}_plot.pdf

请编写matplotlib代码生成一张论文级质量的图。要求:
- 使用合适的图表类型(路线图/柱状图/对比图/热力图等)
- 标注清晰(轴标签、图例、数值标注)
- 中文字体: plt.rcParams['font.sans-serif'] = ['SimHei','Microsoft YaHei','DejaVu Sans']
- 不使用plt.show(), 而是savefig到指定路径
- 300dpi, bbox_inches='tight'
- 代码完整可执行

只返回Python代码，放在```python```代码块中。"""

        code = self._call(
            "你是matplotlib数据可视化专家。生成论文级质量的图表代码。",
            prompt, max_tok=4000)
        time.sleep(0.2)

        # 提取代码
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0].strip()
        elif "```" in code:
            code = code.split("```")[1].split("```")[0].strip()

        # 执行
        code_path = Path(tempfile.gettempdir()) / f"fig_q{sp_id}.py"
        code_path.write_text(code, encoding="utf-8")
        try:
            result = subprocess.run(
                [sys.executable, str(code_path)],
                capture_output=True, text=True, timeout=60,
                cwd=str(Path(__file__).parent.parent.parent),
                encoding='utf-8', errors='replace'
            )
            fig_path = Path(fig_dir) / f"sub_{sp_id}_plot.pdf"
            if fig_path.exists():
                print(f"  [FIG] Generated: {fig_path.name} ({fig_path.stat().st_size} bytes)")
                return str(fig_path)
            else:
                print(f"  [FIG] Figure not found at {fig_path}")
                if result.stderr:
                    print(f"  [FIG] Errors: {result.stderr[:500]}")
                # Retry with fixes
                fix_prompt = f"上一轮代码执行出错:\n{result.stderr[-2000:]}\n请修复。只返回修正后的Python代码。\n原代码:\n{code[:2000]}"
                code2 = self._call(
                    "修复matplotlib代码错误。", fix_prompt, max_tok=4000)
                if "```python" in code2:
                    code2 = code2.split("```python")[1].split("```")[0].strip()
                code_path.write_text(code2, encoding="utf-8")
                subprocess.run([sys.executable, str(code_path)],
                              capture_output=True, text=True, timeout=60,
                              cwd=str(Path(__file__).parent.parent.parent),
                              encoding='utf-8', errors='replace')
                if fig_path.exists():
                    return str(fig_path)
        except Exception as e:
            print(f"  [FIG] Error: {e}")

        return None
