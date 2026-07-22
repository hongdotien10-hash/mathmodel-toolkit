"""子问题拆分器。

从题目文本中自动识别并拆分多个子问题。
"""

import re
from typing import Optional


class ProblemSplitter:
    """子问题拆分器。

    基于正则模式匹配识别题目标记，将长文本切分为独立的子问题。

    Usage::

        splitter = ProblemSplitter()
        sub_problems = splitter.split(problem_text)
        # [{"index": 1, "title": "问题1 ...", "content": "...", "start_line": 10}]
    """

    # 子问题标题匹配模式（按优先级排序）
    PATTERNS = [
        # 中文数字序号
        r"问题\s*([一二三四五六七八九十\d]+)\s*[：:\.\、\）\)]",
        r"第\s*([一二三四五六七八九十\d]+)\s*(?:小)?题\s*[：:\.\、]",
        r"\(([一二三四五六七八九十\d]+)\)\s*[^\n]{0,20}",
        # 英文数字
        r"(?:Problem|Question)\s*(\d+)\s*[：:\.\、]",
        r"^\s*(\d+)\s*[\.\、]\s+",
        # 括号数字
        r"（([一二三四五六七八九十\d]+)）",
    ]

    def __init__(self):
        self._compiled = [re.compile(p, re.MULTILINE) for p in self.PATTERNS]

    def split(self, text: str) -> list[dict]:
        """拆分题目文本为子问题列表。

        Args:
            text: 完整的题目文本

        Returns:
            list[dict]: 子问题列表，每个元素包含 index / title / content / start_line
        """
        lines = text.split("\n")

        # 第1步：扫描所有可能的子问题起始行
        candidates = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            for pat in self._compiled:
                m = pat.search(line_stripped)
                if m:
                    num = self._parse_number(m.group(1))
                    if num is not None:
                        candidates.append({
                            "number": num,
                            "line": i,
                            "title": line_stripped[:120],
                            "match_start": m.start(),
                        })
                        break  # 只匹配第一个模式

        # 排序：按行号
        candidates.sort(key=lambda c: c["line"])

        # 去重：相邻的相同序号只保留第一个
        deduped = []
        seen_nums = set()
        for c in candidates:
            if c["number"] not in seen_nums:
                deduped.append(c)
                seen_nums.add(c["number"])

        # 第2步：切分内容
        sub_problems = []
        for j, cand in enumerate(deduped):
            start = cand["line"]
            end = deduped[j + 1]["line"] if j + 1 < len(deduped) else len(lines)

            content = "\n".join(lines[start:end]).strip()
            sub_problems.append({
                "id": cand["number"],
                "title": cand["title"],
                "content": content,
                "start_line": start,
                "end_line": end - 1,
            })

        # 如果没找到子问题，返回整个文本作为一个问题
        if not sub_problems:
            # 尝试找 "问题重述" 后面的内容
            restatement_idx = None
            for i, line in enumerate(lines):
                if any(kw in line for kw in ["问题重述", "问题描述", "题目"]):
                    restatement_idx = i
                    break

            start_idx = restatement_idx + 1 if restatement_idx is not None else 0
            sub_problems = [{
                "id": 1,
                "title": "完整问题",
                "content": "\n".join(lines[start_idx:]).strip(),
                "start_line": start_idx,
                "end_line": len(lines) - 1,
            }]

        return sub_problems

    @staticmethod
    def _parse_number(s: str) -> Optional[int]:
        """解析中文/阿拉伯数字。"""
        s = s.strip()
        cn_map = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
        }
        if s in cn_map:
            return cn_map[s]
        try:
            return int(s)
        except ValueError:
            return None
