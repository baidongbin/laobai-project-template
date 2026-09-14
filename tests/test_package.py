"""在隔离 Git 仓库验证归档、替换和旧包清理，不改真实项目产物。"""

import os
from pathlib import Path
import shutil
import shlex
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "sample project"
        self.root.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        # 测试使用隔离 HOME，避免宿主 Git 配置影响。
        self.env["HOME"] = str(self.base / "home")
        self.env["XDG_CONFIG_HOME"] = str(self.base / "config")
        Path(self.env["HOME"]).mkdir()
        shutil.copy2(ROOT / "package.sh", self.root / "package.sh")
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], env=self.env,
                              capture_output=True, check=True).stdout.decode().strip()

    def commit(self):
        self.git("add", "--", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
        return self.root / (self.root.name + "-" + self.git("rev-parse", "--short", "HEAD") + ".zip")

    def package(self):
        return subprocess.run(["sh", str(self.root / "package.sh")], cwd=self.base,
                              env=self.env, capture_output=True, text=True)

    def test_no_head_leaves_no_archive(self):
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(self.root.rglob("*.zip")), [])

    def test_archive_contains_only_committed_exportable_files(self):
        (self.root / "data.txt").write_text("committed\n")
        (self.root / "private.txt").write_text("fixture only\n")
        (self.root / ".gitattributes").write_text("private.txt export-ignore\n")
        output = self.commit()
        (self.root / "data.txt").write_text("dirty\n")
        (self.root / "untracked.txt").write_text("untracked\n")
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(output) as archive:
            prefix = self.root.name + "/"
            self.assertEqual(archive.read(prefix + "data.txt"), b"committed\n")
            self.assertNotIn(prefix + "private.txt", archive.namelist())
            self.assertNotIn(prefix + "untracked.txt", archive.namelist())

    def test_replace_same_name_and_keep_only_latest_project_package(self):
        (self.root / ".gitignore").write_text("/*.zip\n")
        output = self.commit()
        output.write_bytes(b"user content")
        other = output.parent / "other-project.zip"
        other.write_bytes(b"keep")
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(zipfile.is_zipfile(output))
        (self.root / "new.txt").write_text("new commit\n")
        latest = self.commit()
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(output.exists())
        self.assertTrue(zipfile.is_zipfile(latest))
        self.assertEqual(other.read_bytes(), b"keep")
        self.assertEqual(list(output.parent.glob(self.root.name + "-*.zip")), [latest])

    def test_archive_failure_preserves_previous_packages(self):
        output = self.commit()
        output.write_bytes(b"existing")
        old = output.parent / (self.root.name + "-abcd.zip")
        old.write_bytes(b"previous")
        real_git = shutil.which("git")
        binary = self.base / "bin"
        binary.mkdir()
        wrapper = binary / "git"
        wrapper.write_text('#!/bin/sh\nif [ "$1" = archive ]; then echo partial; exit 1; fi\nexec ' + shlex.quote(real_git) + ' "$@"\n')
        wrapper.chmod(0o755)
        self.env["PATH"] = str(binary) + os.pathsep + self.env["PATH"]
        self.assertNotEqual(self.package().returncode, 0)
        self.assertEqual(output.read_bytes(), b"existing")
        self.assertEqual(old.read_bytes(), b"previous")
        self.assertEqual(list(output.parent.glob(".package.*")), [])


if __name__ == "__main__":
    unittest.main()
