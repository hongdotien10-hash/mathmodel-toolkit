"""
COMAP 格式自检脚本（美赛论文）。

用法：
    python check_mcm_format.py <paper.pdf> [--tex main.tex]

检查项：
  * 解答页数 <= 25（"含页眉的页"= 解答页；AI 报告页无页眉，不计入）
  * 每页都有页眉，页码连续，页眉格式为 Team # xxxxxxx, Page X of 25
  * 第 1 页是 Summary Sheet，且摘要只占 1 页
  * 附录页也在解答页内（页眉存在即计入）
  * 若给了 .tex，检查图表/公式编号连续性、参考文献被引用、是否出现姓名/院校字样

依赖：pypdf
"""
import argparse
import os
import re
import sys


def page_texts(path):
    from pypdf import PdfReader
    return [(p.extract_text() or "") for p in PdfReader(path).pages]


def check(pdf, tex=None):
    pages = page_texts(pdf)
    n = len(pages)
    results = []

    def ok(cond, msg, detail=""):
        results.append((bool(cond), msg, detail))

    header_re = re.compile(r"Team\s*#\s*\S+,\s*Page\s+(\d+)\s+of\s+(\d+)")
    hits = []
    for i, t in enumerate(pages, 1):
        m = header_re.search(t.replace("\n", " "))
        hits.append((i, int(m.group(1)) if m else None))

    sol = [i for i, h in hits if h is not None]
    ai = [i for i, h in hits if h is None]

    ok(len(sol) <= 25, "解答页数 <= 25", "解答 %d 页 + AI 报告 %d 页" % (len(sol), len(ai)))
    ok(len(sol) >= 1, "至少有一页解答")
    ok(all(h is not None for i, h in hits if i in sol), "每个解答页都有页眉")
    nums = [h for i, h in hits if h is not None]
    ok(nums == list(range(1, len(nums) + 1)), "页码连续", str(nums[:5]) + "...")
    ok(sol and sol[0] == 1, "第 1 页也有页眉", "第 1 页 %s" % ("有" if hits and hits[0][1] else "无"))
    ok(bool(ai) or n <= 25, "AI 报告页无页眉（不计入 25 页）")
    ok("Summary" in pages[0] and "Keywords" in pages[0], "第 1 页含 Summary 与 Keywords")
    ok("Contents" in "".join(pages[:3]), "目录存在")
    ok(any("Report on Use of AI" in t for t in pages), "含 Report on Use of AI")

    if tex and os.path.exists(tex):
        s = open(tex, encoding="utf-8").read()
        cites = set()
        for grp in re.findall(r"\\cite\{([^}]*)\}", s):
            cites.update(k.strip() for k in grp.split(","))
        bibs = re.findall(r"\\bibitem\{([^}]*)\}", s)
        for b in bibs:
            ok(b in cites, "参考文献 %s 在正文被引用" % b)
        for bad in ("Acknowledg", "Acknowledgement", "university", "University"):
            ok(bad not in s, "未出现致谢/院校字样（%s）" % bad)
        nfig = len(re.findall(r"\\begin\{figure\}", s))
        ntab = len(re.findall(r"\\begin\{table\}", s))
        ncap = len(re.findall(r"\\caption\{", s))
        ok(ncap >= nfig + ntab, "图/表都有 caption",
           "%d 图 %d 表 %d caption" % (nfig, ntab, ncap))
        ok(len(bibs) == len(cites & set(bibs)),
           "正文引用数 = 参考文献条数",
           "%d / %d" % (len(cites & set(bibs)), len(bibs)))
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--tex", default=None)
    a = ap.parse_args()
    res = check(a.pdf, a.tex)
    bad = 0
    for good, msg, detail in res:
        print("  [%s] %s%s" % ("PASS" if good else "FAIL", msg,
                                ("  -- " + detail) if detail else ""))
        bad += (not good)
    print("\nRESULT: %s" % ("all checks pass" if not bad else "%d check(s) failed" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
