import tempfile
import unittest
from pathlib import Path
import sys

# 將 scripts 加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from note import (
    sanitize_filename,
    LocalStorageBackend,
    get_current_repo_name,
)


class TestStudyNotes(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.temp_dir.name)
        self.backend = LocalStorageBackend(self.root_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_current_repo_name(self):
        repo_name = get_current_repo_name()
        self.assertIsInstance(repo_name, str)
        self.assertTrue(len(repo_name) > 0)

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("GCP / Cloud: Function"), "GCP_Cloud_Function")
        self.assertEqual(sanitize_filename("test?name*"), "testname")

    def test_add_and_list_note(self):
        msg, path = self.backend.add(
            repo="TestRepo",
            category="GCP",
            title="Slack_Webhook",
            content="## 核心摘要\n修復了 Webhook URL。",
            tags=["gcp", "slack"],
        )
        self.assertTrue(Path(path).exists())
        self.assertIn("GCP_Slack_Webhook.md", path)

        notes = self.backend.list_notes(repo="TestRepo")
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["filename"], "GCP_Slack_Webhook.md")
        self.assertEqual(notes[0]["repo"], "TestRepo")

    def test_search_note_by_content_and_filename(self):
        self.backend.add(
            repo="RepoA",
            category="BugFix",
            title="Database_Connection",
            content="修復了連線逾時問題，使用連線池機制。",
            tags=["db", "sql"],
        )
        self.backend.add(
            repo="RepoB",
            category="Architecture",
            title="Microservices",
            content="微服務架構拆分指引與實踐。",
            tags=["arch"],
        )

        # 搜尋檔名
        res1 = self.backend.search("Database")
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]["repo"], "RepoA")

        # 搜尋內文
        res2 = self.backend.search("連線池")
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0]["repo"], "RepoA")
        self.assertIn("連線池", res2[0]["snippet"])

        # 搜尋微服務
        res3 = self.backend.search("微服務")
        self.assertEqual(len(res3), 1)
        self.assertEqual(res3[0]["repo"], "RepoB")

    def test_read_note(self):
        self.backend.add(
            repo="RepoC",
            category="Tips",
            title="Git_Branching",
            content="始終使用 Feature Branch 與 PR。",
            tags=["git"],
        )
        content = self.backend.read("Tips_Git_Branching.md", repo="RepoC")
        self.assertIsNotNone(content)
        self.assertIn("title: \"Git_Branching\"", content)
        self.assertIn("始終使用 Feature Branch 與 PR。", content)

    def test_add_doc_format(self):
        msg, path = self.backend.add(
            repo="RepoD",
            category="Metrics",
            title="Benchmark",
            content="time,val\n1,10",
            tags=["perf"],
            doc_format="sheet",
        )
        self.assertTrue(Path(path).exists())
        self.assertIn("Metrics_Benchmark.md", path)

    def test_gdrive_read_by_filename_lookup(self):
        from unittest.mock import MagicMock
        from note import GDriveCliStorageBackend
        import subprocess

        gdrive = GDriveCliStorageBackend("gdrive", "dummy_folder_id")
        # Mock list_notes
        gdrive.list_notes = MagicMock(return_value=[
            {
                "repo": "AI_IT_Go",
                "filename": "GCP_Billing_Threshold_Optimization_Guide",
                "type": "Google Doc 📄",
                "id": "1xKaHde6soD1GhMg5HJ6C8QQmFe6VhWp8PKURbl-Axqc",
                "modified": "2026-10-19T03:18:00Z"
            }
        ])

        def mock_run(args):
            if args[1] == "export":
                out_path = Path(args[3])
                out_path.write_text("# Mock Export Content", encoding="utf-8")
                return subprocess.CompletedProcess(args, 0, stdout="Exported", stderr="")
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="Error")

        gdrive._run_gdrive = MagicMock(side_effect=mock_run)

        # 測試使用長檔名讀取
        content = gdrive.read("GCP_Billing_Threshold_Optimization_Guide")
        self.assertEqual(content, "# Mock Export Content")
        # 驗證傳遞給 export 的是解析出來的 File ID 而非檔名
        called_args = gdrive._run_gdrive.call_args[0][0]
        self.assertEqual(called_args[2], "1xKaHde6soD1GhMg5HJ6C8QQmFe6VhWp8PKURbl-Axqc")


if __name__ == "__main__":
    unittest.main()

