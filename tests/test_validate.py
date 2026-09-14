"""通过损坏临时副本验证检查器，不改变真实模板。"""

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate", ROOT / "scripts/validate.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", "*.zip", "__pycache__"))

    def change(self, name, old, new):
        path = self.root / name
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new))

    def assert_failure(self, fragment):
        errors, _ = validator.validate(self.root)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_current_tree(self):
        errors, _ = validator.validate(self.root)
        self.assertEqual(errors, [])

    def test_missing_link_and_anchor(self):
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\n[缺失](absent.md)\n[锚点](README.md#absent)\n")
        self.assert_failure("链接目标不存在")
        self.assert_failure("缺少显式锚点")

    def test_extension_link_uses_destination(self):
        self.change("extensions/plan.md.template", "../../product.md", "../product.md")
        self.assert_failure("sample.md: 链接目标不存在")

    def test_shared_drift(self):
        self.change("templates/lite/docs/product.md", "# 产品目标与范围", "# 产品说明")
        self.assert_failure("共用文件不一致")

    def test_rules_drift(self):
        self.change("templates/lite/AGENTS.md", "不伪造运行结果", "不伪造任何运行结果")
        self.assert_failure("AGENTS 公共规则不一致")

    def test_document_check_rules_drift(self):
        self.change("templates/lite/AGENTS.md", "无需为更新基线单独制造零碎提交", "核对后立即提交")
        self.assert_failure("AGENTS 公共规则不一致")

    def test_invalid_state_and_missing_metadata(self):
        self.change("extensions/plan.md.template", "task_status: planned", "task_status: verified")
        self.assert_failure("非法 task_status")
        self.change("templates/lite/docs/product.md", "---\ntype: product\ndoc_status: draft\n---\n", "")
        self.assert_failure("缺少元信息")

    def test_duplicate_ids(self):
        for name in ("extensions/plan.md.template", "extensions/plan/README.md.template"):
            self.change(name, "PLAN-{{TASK_ID}}", "PLAN-SAME")
        self.assert_failure("重复 ID")

    def test_extra_preset_file(self):
        (self.root / "templates/lite/extra.md").write_text("# 不应默认导入\n")
        self.assert_failure("预设文件集合错误")

    def test_archive_move_requires_inbound_repair(self):
        files = {
            "README.md": "[任务](docs/plans/active/task.md)\n",
            "docs/plans/archive/task.md": "---\nid: PLAN-1\ntype: plan\ndoc_status: archived\ntask_status: done\n---\n[产品](../../product.md)\n",
            "docs/product.md": "---\ntype: product\ndoc_status: active\n---\n# 产品\n",
        }
        _, errors = validator.check_links(files, "归档")
        self.assertTrue(errors)
        files["README.md"] = "[任务](docs/plans/archive/task.md)\n"
        self.assertEqual(validator.check_links(files, "归档")[1], [])
        self.assertEqual(validator.check_metadata(files, "归档"), [])

    def test_missing_agents_is_reported(self):
        (self.root / "templates/lite/AGENTS.md").unlink()
        self.assert_failure("AGENTS 公共规则不一致或缺失")


if __name__ == "__main__":
    unittest.main()
