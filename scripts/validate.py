#!/usr/bin/env python3
"""只读检查本仓库固定模板约定；仅依赖 Python 标准库。"""

import argparse
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
BASE_FILES = {"README.md", "AGENTS.md", ".gitignore", ".editorconfig", "package.sh",
              "docs/product.md", "docs/architecture.md"}
STANDARD_FILES = {"docs/README.md", "docs/development.md", "docs/testing.md"}
SHARED = ("docs/product.md", "docs/architecture.md", ".gitignore", ".editorconfig", "package.sh")
EXTENSIONS = {
    "roadmap.md": "docs/roadmap.md",
    "spec.md": "docs/specs/sample.md",
    "plan.md": "docs/plans/active/sample.md",
    "plan/README.md": "docs/plans/active/sample-dir/README.md",
    "plan/design.md": "docs/plans/active/sample-dir/design.md",
    "plan/verification.md": "docs/plans/active/sample-dir/verification.md",
    "version/README.md": "docs/versions/v1/README.md",
    "version/design.md": "docs/versions/v1/design.md",
    "version/architecture-snapshot.md": "docs/versions/v1/architecture-snapshot.md",
    "decision.md": "docs/decisions/001-sample.md",
    "deployment.md": "docs/deployment.md",
    "reference.md": "docs/references/sample.md",
    "large/module-AGENTS.md": "packages/sample/AGENTS.md",
    "large/domain-architecture.md": "docs/architecture/sample.md",
    "large/environment.md": "docs/development/environment.md",
}
DOC_STATES = {"draft", "active", "superseded", "archived"}
TASK_STATES = {"planned", "in_progress", "blocked", "done", "cancelled"}
TYPES = {"product", "architecture", "development", "testing", "roadmap", "spec",
         "plan", "version", "design", "verification", "decision",
         "architecture-snapshot", "deployment", "reference"}


def prose(text):
    """跳过 fenced code；模板占位路径和示例命令不视为真实链接。"""
    return re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", text)


def check_links(files, label):
    errors = []
    count = 0
    for name, text in files.items():
        for href in re.findall(r"\[[^\]\n]*\]\(([^\s)]+)\)", prose(text)):
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            count += 1
            path = unquote(url.path)
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name), path)) if path else name
            if path.startswith("/") or target == ".." or target.startswith("../"):
                errors.append(f"{label}/{name}: 链接越出项目: {href}")
            elif target not in files:
                errors.append(f"{label}/{name}: 链接目标不存在: {href}")
            elif url.fragment:
                anchors = re.findall(r'\bid=[\"\']([^\"\']+)[\"\']', files[target])
                if unquote(url.fragment) not in anchors:
                    errors.append(f"{label}/{name}: 缺少显式锚点: {href}")
    return count, errors


def check_metadata(files, label):
    errors = []
    ids = set()
    for name, text in files.items():
        required = name.startswith("docs/") and not name.endswith("/README.md")
        if not text.startswith("---\n"):
            if required:
                errors.append(f"{label}/{name}: 缺少元信息")
            continue
        parts = text.split("---\n", 2)
        if len(parts) != 3:
            errors.append(f"{label}/{name}: 元信息未闭合")
            continue
        fields = {}
        for line in parts[1].splitlines():
            match = re.fullmatch(r"([a-z_]+):\s+(.+)", line)
            if not match:
                errors.append(f"{label}/{name}: 不支持的元信息行: {line}")
                continue
            key, value = match.groups()
            if key in fields:
                errors.append(f"{label}/{name}: 重复字段 {key}")
            fields[key] = value.strip('\"\'')
        kind = fields.get("type")
        if kind not in TYPES or fields.get("doc_status") not in DOC_STATES:
            errors.append(f"{label}/{name}: 非法 type 或 doc_status")
        if kind in {"plan", "spec", "decision"}:
            identifier = fields.get("id")
            if not identifier or identifier in ids:
                errors.append(f"{label}/{name}: 缺失或重复 ID: {identifier}")
            ids.add(identifier)
        if kind == "plan":
            state = fields.get("task_status")
            if state not in TASK_STATES:
                errors.append(f"{label}/{name}: 非法 task_status")
            if "/archive/" in name and (state not in {"done", "cancelled"} or fields.get("doc_status") != "archived"):
                errors.append(f"{label}/{name}: 归档任务状态不一致")
        if kind == "version" and (not fields.get("version") or fields.get("version_status") not in {"planned", "in_progress", "released", "cancelled"}):
            errors.append(f"{label}/{name}: 非法版本字段")
        if kind == "design" and "/versions/" in name and not fields.get("baseline_ref"):
            errors.append(f"{label}/{name}: 缺少 baseline_ref")
        if kind == "architecture-snapshot" and not fields.get("release_ref"):
            errors.append(f"{label}/{name}: 缺少 release_ref")
    return errors


def common_rules(text):
    sections = re.split(r"(?m)^## ", text)
    wanted = {"当前事实与目标", "实施与安全边界", "验证与交付", "文档核对与同步", "提交与推送"}
    return {section.splitlines()[0]: section for section in sections if section and section.splitlines()[0] in wanted}


def validate(root):
    files = {}
    errors = []
    details = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {".git", "__pycache__"} for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(f"不支持符号链接: {relative}")
            continue
        if not path.is_file() or not (path.suffix in {".md", ".template", ".py", ".sh"} or path.name in {".gitignore", ".editorconfig"}):
            continue
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except UnicodeError:
            errors.append(f"非 UTF-8 文件: {relative}")
            continue
        if b"\r" in raw or not raw.endswith(b"\n"):
            errors.append(f"换行格式错误: {relative}")
        files[relative.as_posix()] = text
    for name in ("README.md", "AGENTS.md", "package.sh", "docs/product.md", "docs/architecture.md", "scripts/validate.py", "tests/test_validate.py"):
        if name not in files:
            errors.append(f"缺少项目文件: {name}")
    for name in SHARED:
        if files.get(f"templates/lite/{name}") != files.get(f"templates/standard/{name}"):
            errors.append(f"共用文件不一致: {name}")
    if files.get("package.sh") != files.get("templates/lite/package.sh"):
        errors.append("根打包脚本与模板不一致")
    lite_rules = common_rules(files.get("templates/lite/AGENTS.md", ""))
    standard_rules = common_rules(files.get("templates/standard/AGENTS.md", ""))
    if len(lite_rules) != 5 or lite_rules != standard_rules:
        errors.append("AGENTS 公共规则不一致或缺失")
    source_docs = {name: text for name, text in files.items() if not name.endswith(".template")}
    # 目标存在性允许链接到模板源文件；不在源路径检查扩展正文。
    count, issues = check_links({name: text if name.endswith(".md") else "" for name, text in files.items()}, "源码")
    errors.extend(issues)
    details.append(f"源码链接 {count} 处")
    errors.extend(check_metadata({name: text for name, text in source_docs.items() if name.startswith("docs/")}, "项目"))
    expected_extensions = {f"extensions/{name}.template" for name in EXTENSIONS}
    actual_extensions = {name for name in files if name.startswith("extensions/") and name.endswith(".template")}
    if actual_extensions != expected_extensions:
        errors.append("扩展集合与落位映射不一致")
    for preset in ("lite", "standard"):
        prefix = f"templates/{preset}/"
        instance = {name[len(prefix):]: text for name, text in files.items() if name.startswith(prefix)}
        expected = BASE_FILES | (STANDARD_FILES if preset == "standard" else set())
        if set(instance) != expected:
            errors.append(f"{preset}: 预设文件集合错误: {sorted(set(instance) ^ expected)}")
        for stage in ("基础", "扩展"):
            if stage == "扩展":
                for index, (source, target) in enumerate(EXTENSIONS.items()):
                    instance[target] = files.get(f"extensions/{source}.template", "").replace("{{TASK_ID}}", str(index))
                instance["CLAUDE.md"] = files.get("adapters/claude/CLAUDE.md.template", "")
                if instance["CLAUDE.md"].strip() != "@AGENTS.md":
                    errors.append("Claude 入口应只导入 @AGENTS.md")
            count, issues = check_links(instance, f"{preset}/{stage}")
            errors.extend(issues)
            errors.extend(check_metadata(instance, f"{preset}/{stage}"))
            details.append(f"{preset} {stage}链接 {count} 处")
    return errors, details


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="显示各阶段检查摘要")
    args = parser.parse_args()
    errors, details = validate(ROOT)
    if args.verbose:
        print("\n".join(details))
    for error in errors:
        print(f"失败: {error}", file=sys.stderr)
    print(f"模板检查{'失败：' + str(len(errors)) + ' 项问题' if errors else '通过'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
