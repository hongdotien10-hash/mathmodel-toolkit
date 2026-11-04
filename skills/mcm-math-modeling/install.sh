#!/usr/bin/env bash
# 把 mcm-math-modeling 安装到本机智能体的 skills 目录。
#
#   ./install.sh              # 自动探测并安装到所有已存在的智能体
#   ./install.sh claude       # 只装到 Claude Code
#   ./install.sh workbuddy    # 只装到 WorkBuddy
#   ./install.sh --list       # 只列出识别到的智能体，不安装
#
# 安装方式为复制整个 mcm-math-modeling/ 目录（含 SKILL.md、references/、
# scripts/、assets/、icon.png），不改动源目录。

set -euo pipefail

SKILL_NAME="mcm-math-modeling"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${HOME}"

# agent 标识 -> skills 目录（相对 HOME）
AGENTS_claude="$HOME_DIR/.claude/skills"
AGENTS_workbuddy="$HOME_DIR/.workbuddy/skills"
AGENTS_workbuddy_intl="$HOME_DIR/.workbuddy-intl/skills"
AGENTS_codex="$HOME_DIR/.codex/skills"
AGENTS_cursor="$HOME_DIR/.cursor/skills"
AGENTS_gemini="$HOME_DIR/.gemini/skills"
AGENTS_opencode="$HOME_DIR/.config/opencode/skills"
AGENTS_windsurf="$HOME_DIR/.windsurf/skills"

list_agents() {
  local found=()
  for key in claude workbuddy workbuddy_intl codex cursor gemini opencode windsurf; do
    local var="AGENTS_${key}"
    local dir="${!var}"
    if [ -d "$dir" ]; then
      found+=("$key")
    fi
  done
  printf '%s\n' "${found[@]+"${found[@]}"}"
}

install_to() {
  local agent="$1"
  local var="AGENTS_${agent}"
  local target_root="${!var}"
  local target="$target_root/$SKILL_NAME"

  if [ ! -f "$SRC_DIR/SKILL.md" ]; then
    echo "错误：$SRC_DIR 下没有 SKILL.md，请在技能包根目录运行本脚本。" >&2
    exit 1
  fi

  mkdir -p "$target_root"
  if [ -e "$target" ]; then
    echo "  · 已存在，先移除旧版本：$target"
    rm -rf "$target"
  fi
  cp -r "$SRC_DIR" "$target"
  echo "  ✓ 已安装到 $target"
}

main() {
  local mode="${1:-auto}"

  if [ "$mode" = "--list" ] || [ "$mode" = "-l" ]; then
    echo "识别到的智能体："
    for a in $(list_agents); do
      var="AGENTS_${a}"
      printf '  · %-20s %s\n' "$a" "${!var}"
    done
    exit 0
  fi

  local targets=()
  if [ "$mode" = "auto" ]; then
    targets=($(list_agents))
    if [ ${#targets[@]} -eq 0 ]; then
      echo "未识别到任何智能体的 skills 目录。" >&2
      echo "请手动复制本目录到目标智能体的 skills 目录，或查看 README 的「手动安装」一节。" >&2
      exit 1
    fi
  else
    # eval 取间接变量值，避免 set -u 下 ${!var+x} 在部分 bash 版本报错
    local var_name="AGENTS_${mode}"
    if ! eval "[ -n \"\${${var_name}+x}\" ]"; then
      echo "未知智能体：$mode" >&2
      echo "可选：claude workbuddy workbuddy_intl codex cursor gemini opencode windsurf" >&2
      exit 1
    fi
    targets=("$mode")
  fi

  echo "安装 $SKILL_NAME ..."
  for a in "${targets[@]}"; do
    install_to "$a"
  done

  echo
  echo "依赖安装（绘图与求解器模板需要）："
  echo "  python -m pip install -r requirements.txt"
  echo
  echo "注意：部分依赖仅绘图/求解脚本需要；纯文档工作流（读题、建模、写作、验收）"
  echo "      只依赖 Python 标准库，verify_checkpoint.py 即为 stdlib only。"
}

main "$@"
