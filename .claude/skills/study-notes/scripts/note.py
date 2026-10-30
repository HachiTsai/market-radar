#!/usr/bin/env python3
"""
Study Notes CLI - 跨專案通用學習筆記管理工具
支援自動同步至 Google Drive 的 Agent_Study_Notes 目錄（按 repo名 存放）。
所有存入 Google Drive 的檔案一律採用 Google 原生文件格式 (Google Docs 📄, Sheets 📊, Slides 📽️)。
支援 gdrive CLI 與本地端雙模同步。
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_LOCAL_PATH = (
    Path.home()
    / "Library"
    / "CloudStorage"
    / "GoogleDrive-hachi.tsai@gmail.com"
    / "我的雲端硬碟"
    / "00_Claude"
    / "Agent_Study_Notes"
)
DEFAULT_FOLDER_ID = "1Xlj49hpabV47WMzctSNS29_Vuuh6ddHn"

# Google Workspace 原生 MIME 類型映射
WORKSPACE_MIME_TYPES = {
    "doc": "application/vnd.google-apps.document",
    "sheet": "application/vnd.google-apps.spreadsheet",
    "slide": "application/vnd.google-apps.presentation",
}

WORKSPACE_TYPE_NAMES = {
    "application/vnd.google-apps.document": "Google Doc 📄",
    "application/vnd.google-apps.spreadsheet": "Google Sheet 📊",
    "application/vnd.google-apps.presentation": "Google Slide 📽️",
    "application/vnd.google-apps.folder": "Google Folder 📁",
}


def get_current_repo_name() -> str:
    """自動偵測當前 Git Repository 名稱，若不在 git 內則回傳 'Common'"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()).name
    except Exception:
        pass
    return "Common"


def sanitize_filename(name: str) -> str:
    """清理檔名中的非法字元"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name


def find_gdrive_bin() -> Optional[str]:
    """尋找 gdrive CLI 執行檔路徑"""
    custom_bin = Path.home() / ".gemini" / "antigravity" / "bin" / "gdrive"
    if custom_bin.exists() and os.access(custom_bin, os.X_OK):
        return str(custom_bin)
    system_bin = shutil.which("gdrive")
    if system_bin:
        return system_bin
    return None


class StorageBackend:
    def add(
        self,
        repo: str,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        doc_format: str = "doc",
    ) -> Tuple[str, str]:
        """新增筆記，回傳 (狀態訊息, 檔案路徑或ID或URL)"""
        raise NotImplementedError

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        """檢索筆記"""
        raise NotImplementedError

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        """讀取筆記內容"""
        raise NotImplementedError

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        """列出筆記"""
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _format_content(
        self, repo: str, category: str, title: str, content: str, tags: List[str]
    ) -> str:
        today = datetime.date.today().isoformat()
        tags_str = ", ".join(f'"{t.strip()}"' for t in tags if t.strip())
        frontmatter = (
            f"---\n"
            f'title: "{title}"\n'
            f'repo: "{repo}"\n'
            f'category: "{category}"\n'
            f"date: {today}\n"
            f"tags: [{tags_str}]\n"
            f"---\n\n"
        )
        return frontmatter + content.strip() + "\n"

    def add(
        self,
        repo: str,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        doc_format: str = "doc",
    ) -> Tuple[str, str]:
        repo_dir = self.root_dir / sanitize_filename(repo)
        repo_dir.mkdir(parents=True, exist_ok=True)

        clean_cat = sanitize_filename(category)
        clean_raw_title = sanitize_filename(title)
        if clean_raw_title.startswith(f"{clean_cat}_"):
            clean_title = clean_raw_title
        else:
            clean_title = f"{clean_cat}_{clean_raw_title}"

        filename = f"{clean_title}.md"
        target_path = repo_dir / filename
        formatted_content = self._format_content(
            repo, category, title, content, tags
        )

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        return (
            f"成功寫入本機筆記備份: {filename}",
            str(target_path),
        )

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        notes = []
        if repo:
            target_dirs = [self.root_dir / sanitize_filename(repo)]
        else:
            target_dirs = [p for p in self.root_dir.iterdir() if p.is_dir()]

        for r_dir in target_dirs:
            if not r_dir.exists():
                continue
            for file_path in r_dir.glob("*.md"):
                try:
                    stat = file_path.stat()
                    notes.append(
                        {
                            "repo": r_dir.name,
                            "filename": file_path.name,
                            "type": "Markdown 📝",
                            "path": str(file_path),
                            "modified": datetime.datetime.fromtimestamp(
                                stat.st_mtime
                            ).strftime("%Y-%m-%d %H:%M:%S"),
                        }
                    )
                except Exception:
                    pass
        notes.sort(key=lambda x: (x["repo"], x["filename"]))
        return notes

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        all_notes = self.list_notes(repo)
        query_lower = query.lower()
        results = []

        for note in all_notes:
            file_path = Path(note["path"])
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                matched = False
                snippet = ""
                if query_lower in note["filename"].lower():
                    matched = True
                    snippet = "匹配檔名"
                elif query_lower in content.lower():
                    matched = True
                    idx = content.lower().find(query_lower)
                    start = max(0, idx - 40)
                    end = min(len(content), idx + 60)
                    snippet = "..." + content[start:end].replace("\n", " ") + "..."

                if matched:
                    res = dict(note)
                    res["snippet"] = snippet
                    results.append(res)
            except Exception:
                continue

        return results

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        target = Path(identifier)
        if target.exists() and target.is_file():
            with open(target, "r", encoding="utf-8") as f:
                return f.read()

        all_notes = self.list_notes(repo)
        for note in all_notes:
            if (
                note["filename"] == identifier
                or note["filename"].lower() == identifier.lower()
                or identifier.lower() in note["filename"].lower()
            ):
                with open(note["path"], "r", encoding="utf-8") as f:
                    return f.read()
        return None


class GDriveCliStorageBackend(StorageBackend):
    """
    透過 gdrive CLI 直接在雲端建立與管理 Google 原生文件格式 (Docs, Sheets, Slides)。
    """
    def __init__(self, gdrive_bin: str, folder_id: str):
        self.gdrive_bin = gdrive_bin
        self.folder_id = folder_id

    def _run_gdrive(self, args: List[str]) -> subprocess.CompletedProcess:
        cmd = [self.gdrive_bin] + args
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def _get_or_create_repo_folder(self, repo: str) -> str:
        res = self._run_gdrive(["readonly", "ls", self.folder_id, "--json"])
        if res.returncode == 0:
            try:
                items = json.loads(res.stdout.strip() or "[]")
                for item in items:
                    if item.get("name") == repo and item.get("mimeType") == "application/vnd.google-apps.folder":
                        return item["id"]
            except Exception:
                pass

        res_mkdir = self._run_gdrive(["mutate", "mkdir", repo, "--parent", self.folder_id, "--json"])
        if res_mkdir.returncode == 0:
            try:
                data = json.loads(res_mkdir.stdout.strip())
                if "id" in data:
                    return data["id"]
            except Exception:
                pass
        return self.folder_id

    def add(
        self,
        repo: str,
        category: str,
        title: str,
        content: str,
        tags: List[str],
        doc_format: str = "doc",
    ) -> Tuple[str, str]:
        repo_folder_id = self._get_or_create_repo_folder(repo)
        clean_cat = sanitize_filename(category)
        clean_raw_title = sanitize_filename(title)
        if clean_raw_title.startswith(f"{clean_cat}_"):
            clean_title = clean_raw_title
        else:
            clean_title = f"{clean_cat}_{clean_raw_title}"

        clean_ext = ".csv" if doc_format == "sheet" else ".md"
        temp_name = f"{clean_title}{clean_ext}"

        temp_dir = Path("/tmp/claude_notes")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / temp_name

        today = datetime.date.today().isoformat()
        tags_str = ", ".join(f'"{t.strip()}"' for t in tags if t.strip())
        formatted = (
            f"---\n"
            f'title: "{title}"\n'
            f'repo: "{repo}"\n'
            f'category: "{category}"\n'
            f"date: {today}\n"
            f"tags: [{tags_str}]\n"
            f"---\n\n"
            f"{content.strip()}\n"
        )
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(formatted)

        # 決定 Google Workspace MIME 類型
        target_mime = WORKSPACE_MIME_TYPES.get(doc_format, WORKSPACE_MIME_TYPES["doc"])

        # 上傳並要求 Google Drive 轉換為原生文件格式
        upload_cmd = [
            "mutate", "upload", str(temp_file),
            "--mime-type", target_mime,
            "--parent", repo_folder_id,
            "--json"
        ]
        res = self._run_gdrive(upload_cmd)

        if res.returncode != 0:
            return (
                f"上傳 Google Drive 失敗：{res.stderr.strip()}",
                str(temp_file),
            )

        # 從回傳中提取 File ID
        m = re.search(r"\(ID:\s*([^\)]+)\)", res.stdout)
        file_id = m.group(1) if m else ""

        if not file_id:
            try:
                data = json.loads(res.stdout.strip())
                file_id = data.get("id", "")
            except Exception:
                pass

        doc_url = ""
        if file_id:
            # 重新命名為無副檔名之 Google 文件標準標題
            self._run_gdrive(["mutate", "rename", file_id, clean_title])
            # 取得網頁檢視 URL
            url_res = self._run_gdrive(["readonly", "url", file_id])
            doc_url = url_res.stdout.strip()

        # 本機快照一律存放於系統快取目錄 (~/.cache/agent_study_notes)，絕不寫入 Google Drive 本機同步目錄以防自動上傳 .md
        cache_dir = Path.home() / ".cache" / "agent_study_notes" / sanitize_filename(repo)
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            local_cache = cache_dir / f"{clean_title}.md"
            with open(local_cache, "w", encoding="utf-8") as f:
                f.write(formatted)
        except Exception:
            pass

        type_label = WORKSPACE_TYPE_NAMES.get(target_mime, "Google 文件")
        link_str = doc_url or (f"https://docs.google.com/document/d/{file_id}/edit" if file_id else "")
        return (
            f"成功建立 {type_label} 並存入 Google Drive: {clean_title}\n連結: {link_str}",
            link_str or file_id,
        )

    def list_notes(self, repo: Optional[str] = None) -> List[Dict]:
        notes = []
        if repo:
            target_folders = [(repo, self._get_or_create_repo_folder(repo))]
        else:
            # 遍歷所有 repo 資料夾以列出真正的筆記文件
            target_folders = []
            res_root = self._run_gdrive(["readonly", "ls", self.folder_id, "--json"])
            if res_root.returncode == 0:
                try:
                    for item in json.loads(res_root.stdout.strip() or "[]"):
                        if item.get("mimeType") == "application/vnd.google-apps.folder":
                            target_folders.append((item.get("name"), item.get("id")))
                except Exception:
                    pass

        for r_name, f_id in target_folders:
            res = self._run_gdrive(["readonly", "ls", f_id, "--json"])
            if res.returncode == 0:
                try:
                    items = json.loads(res.stdout.strip() or "[]")
                    for item in items:
                        mime = item.get("mimeType", "")
                        if mime == "application/vnd.google-apps.folder":
                            continue
                        if mime in WORKSPACE_TYPE_NAMES or item.get("name", "").endswith(".md"):
                            type_name = WORKSPACE_TYPE_NAMES.get(mime, "Markdown 📝")
                            notes.append(
                                {
                                    "repo": r_name,
                                    "filename": item.get("name"),
                                    "type": type_name,
                                    "id": item.get("id"),
                                    "modified": item.get("modifiedTime", ""),
                                }
                            )
                except Exception:
                    pass
        notes.sort(key=lambda x: (x["repo"], x["filename"]))
        return notes

    def search(self, query: str, repo: Optional[str] = None) -> List[Dict]:
        res = self._run_gdrive(["readonly", "search", "--name-contains", query, "--json"])
        results = []
        if res.returncode == 0:
            try:
                items = json.loads(res.stdout.strip() or "[]")
                for item in items:
                    mime = item.get("mimeType", "")
                    type_name = WORKSPACE_TYPE_NAMES.get(mime, "檔案")
                    results.append(
                        {
                            "repo": repo or "Remote",
                            "filename": item.get("name"),
                            "type": type_name,
                            "id": item.get("id"),
                            "snippet": f"匹配 Drive {type_name}: {item.get('name')}",
                        }
                    )
            except Exception:
                pass
        return results

    def read(self, identifier: str, repo: Optional[str] = None) -> Optional[str]:
        temp_dir = Path("/tmp/claude_notes")
        temp_dir.mkdir(parents=True, exist_ok=True)
        out_file = temp_dir / "read_note.md"

        file_id = identifier

        # 優先從清單中依檔名或 ID 比對
        matched_id = None
        all_notes = self.list_notes(repo)

        # 1. 精確比對檔名或 ID
        for n in all_notes:
            if n["filename"] == identifier or n.get("id") == identifier:
                matched_id = n.get("id")
                break

        # 2. 忽略大小寫比對檔名
        if not matched_id:
            for n in all_notes:
                if n["filename"].lower() == identifier.lower():
                    matched_id = n.get("id")
                    break

        # 3. 部分比對檔名
        if not matched_id:
            for n in all_notes:
                if identifier.lower() in n["filename"].lower():
                    matched_id = n.get("id")
                    break

        if matched_id:
            file_id = matched_id

        # 優先嘗試以 export --format md 讀取 Google Doc
        res = self._run_gdrive(["readonly", "export", file_id, str(out_file), "--format", "md"])
        if res.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                return f.read()

        # 退回以 download 讀取普通檔案
        res_down = self._run_gdrive(["readonly", "download", file_id, "-o", str(out_file)])
        if res_down.returncode == 0 and out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                return f.read()

        return None


def select_backend() -> StorageBackend:
    """
    自動判定最適合的儲存後端。
    只要系統中具備已授權的 gdrive CLI，優先採用 GDriveCliStorageBackend 以確保建立 Google 原生文件格式。
    """
    gdrive_bin = find_gdrive_bin()
    folder_id = os.environ.get("AGENT_STUDY_NOTES_FOLDER_ID", DEFAULT_FOLDER_ID)
    if gdrive_bin:
        return GDriveCliStorageBackend(gdrive_bin, folder_id)

    env_dir = os.environ.get("AGENT_STUDY_NOTES_DIR")
    if env_dir:
        return LocalStorageBackend(Path(env_dir))

    if DEFAULT_LOCAL_PATH.exists() and DEFAULT_LOCAL_PATH.is_dir():
        return LocalStorageBackend(DEFAULT_LOCAL_PATH)

    fallback_dir = Path(".claude") / "notes"
    print(
        f"⚠️ 未偵測到 gdrive CLI，自動退回專案本地儲存: {fallback_dir}",
        file=sys.stderr,
    )
    return LocalStorageBackend(fallback_dir)


def main():
    parser = argparse.ArgumentParser(
        description="Study Notes CLI - 跨專案通用學習筆記管理工具 (支援 Google Docs/Sheets/Slides 原生格式)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    parser_add = subparsers.add_parser("add", help="新增一則學習筆記至 Google Drive")
    parser_add.add_argument("--category", "-c", required=True, help="筆記類別 (例: GCP, Architecture, BugFix)")
    parser_add.add_argument("--title", "-t", required=True, help="筆記標題 (例: Slack_Webhook_Fix)")
    parser_add.add_argument("--tags", help="標籤列表，以逗號分隔 (例: gcp,slack,webhook)")
    parser_add.add_argument("--content", help="筆記內文 (Markdown 格式)")
    parser_add.add_argument("--content-file", help="從指定的 Markdown 檔案讀取筆記內文")
    parser_add.add_argument("--repo", help="指定專案名稱 (預設自動偵測 Git repo)")
    parser_add.add_argument(
        "--format",
        choices=["doc", "sheet", "slide"],
        default="doc",
        help="Google Workspace 格式：doc (Google 文件 📄，預設), sheet (Google 試算表 📊), slide (Google 簡報 📽️)",
    )

    # Search command
    parser_search = subparsers.add_parser("search", help="搜尋既有筆記")
    parser_search.add_argument("query", help="搜尋關鍵字")
    parser_search.add_argument("--repo", help="限定在特定 repo 內搜尋")

    # Read command
    parser_read = subparsers.add_parser("read", help="讀取筆記內容")
    parser_read.add_argument("identifier", help="筆記標題、檔名或 Drive File ID")
    parser_read.add_argument("--repo", help="指定專案名稱")

    # List command
    parser_list = subparsers.add_parser("list", help="列出所有筆記")
    parser_list.add_argument("--repo", help="限定特定 repo")

    args = parser.parse_args()
    backend = select_backend()
    repo_name = args.repo or get_current_repo_name()

    if args.command == "add":
        content = ""
        if args.content_file:
            path = Path(args.content_file)
            if not path.exists():
                print(f"錯誤: 找不到內容檔案 {args.content_file}", file=sys.stderr)
                sys.exit(1)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        elif args.content:
            content = args.content
        else:
            print("錯誤: 必須提供 --content 或 --content-file", file=sys.stderr)
            sys.exit(1)

        tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
        msg, doc_id = backend.add(
            repo=repo_name,
            category=args.category,
            title=args.title,
            content=content,
            tags=tags,
            doc_format=args.format,
        )
        print(msg)

    elif args.command == "search":
        results = backend.search(args.query, repo=args.repo)
        if not results:
            print(f"未找到匹配關鍵字 '{args.query}' 的筆記。")
            return
        print(f"🔍 搜尋 '{args.query}' 結果 ({len(results)} 筆):")
        for idx, item in enumerate(results, 1):
            ftype = item.get("type", "檔案")
            print(f"  {idx}. [{item.get('repo', '')}] {item.get('filename', '')} ({ftype})")
            if "snippet" in item:
                print(f"     內文: {item['snippet']}")
            if "id" in item:
                print(f"     Link: https://docs.google.com/document/d/{item['id']}/edit")

    elif args.command == "read":
        text = backend.read(args.identifier, repo=args.repo)
        if text is None:
            print(f"錯誤: 找不到筆記 '{args.identifier}'", file=sys.stderr)
            sys.exit(1)
        print(text)

    elif args.command == "list":
        notes = backend.list_notes(repo=args.repo)
        if not notes:
            target = f"專案 {args.repo}" if args.repo else "所有專案"
            print(f"目前 {target} 中沒有筆記。")
            return
        print(f"📚 學習筆記清單 ({len(notes)} 筆):")
        for idx, item in enumerate(notes, 1):
            ftype = item.get("type", "Google 文件 📄")
            link_hint = f" | ID: {item.get('id')}" if "id" in item else ""
            print(f"  {idx}. [{item.get('repo', '')}] {item.get('filename', '')} [{ftype}] ({item.get('modified', '')}){link_hint}")


if __name__ == "__main__":
    main()
