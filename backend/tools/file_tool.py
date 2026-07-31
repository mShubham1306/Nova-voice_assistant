"""
NOVA Tool — File Manager
Intelligent file operations: search, open, delete, rename, move, copy,
organize by type, find duplicates, folder management, and more.
"""

from __future__ import annotations

import os
import shutil
import datetime
from pathlib import Path
from typing import Any

from tools.base_tool import BaseTool, ToolResult, param


# Map file extensions → folder name for organize action
EXTENSION_MAP: dict[str, str] = {
    # Documents
    ".pdf": "PDFs", ".docx": "Word Documents", ".doc": "Word Documents",
    ".xlsx": "Excel Sheets", ".xls": "Excel Sheets",
    ".pptx": "Presentations", ".ppt": "Presentations",
    ".txt": "Text Files", ".md": "Markdown",
    # Images
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images",
    ".gif": "Images", ".bmp": "Images", ".svg": "Images", ".webp": "Images",
    # Videos
    ".mp4": "Videos", ".mkv": "Videos", ".avi": "Videos",
    ".mov": "Videos", ".wmv": "Videos",
    # Audio
    ".mp3": "Music", ".wav": "Music", ".flac": "Music", ".aac": "Music",
    # Code
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".html": "HTML", ".css": "CSS", ".json": "JSON", ".xml": "XML",
    ".java": "Java", ".cpp": "CPP", ".c": "C",
    # Archives
    ".zip": "Archives", ".rar": "Archives", ".7z": "Archives", ".tar": "Archives",
    # Executables
    ".exe": "Executables", ".msi": "Installers",
}

# Common folder name aliases → actual path resolution
FOLDER_ALIASES: dict[str, str] = {
    "downloads":    str(Path.home() / "Downloads"),
    "desktop":      str(Path.home() / "Desktop"),
    "documents":    str(Path.home() / "Documents"),
    "pictures":     str(Path.home() / "Pictures"),
    "music":        str(Path.home() / "Music"),
    "videos":       str(Path.home() / "Videos"),
    "appdata":      str(Path.home() / "AppData"),
    "home":         str(Path.home()),
}


class FileTool(BaseTool):
    name = "file_tool"
    description = (
        "Manages files and folders on the user's computer: search, open, delete, rename, "
        "move, copy, organize by type, find duplicates, create folders, and more."
    )
    actions = [
        "search_file",
        "open_file",
        "open_folder",
        "delete_file",
        "rename_file",
        "copy_file",
        "move_file",
        "create_folder",
        "organize_folder",
        "find_duplicates",
        "file_properties",
        "list_folder",
        "recent_files",
        "find_large_files",
    ]
    parameters = {
        "search_file": {
            "query": param("string", "File name or keyword to search for", required=True),
            "folder": param("string", "Folder to search in — e.g. 'downloads', 'desktop', or a full path. Defaults to user home."),
            "extension": param("string", "Filter by extension, e.g. '.pdf', '.docx', '.py'"),
        },
        "open_file": {
            "filename": param("string", "File name or path to open", required=True),
            "application": param("string", "Application to open with, e.g. 'word', 'chrome', 'notepad'. Leave blank for default."),
            "search_first": param("string", "Set to 'true' to search for the file before opening"),
        },
        "open_folder": {
            "folder": param("string", "Folder name or path to open, e.g. 'downloads', 'desktop', 'C:\\Users\\...'", required=True),
        },
        "delete_file": {
            "filename": param("string", "File name or path to delete", required=True),
            "permanent": param("string", "Set to 'true' for permanent delete; otherwise sends to Recycle Bin"),
        },
        "rename_file": {
            "filename": param("string", "Current file name or path", required=True),
            "new_name": param("string", "New file name", required=True),
        },
        "copy_file": {
            "source": param("string", "Source file path", required=True),
            "destination": param("string", "Destination folder path", required=True),
        },
        "move_file": {
            "source": param("string", "Source file path", required=True),
            "destination": param("string", "Destination folder path", required=True),
        },
        "create_folder": {
            "folder_name": param("string", "Name of the new folder", required=True),
            "parent": param("string", "Parent directory. Defaults to Desktop."),
        },
        "organize_folder": {
            "folder": param("string", "Folder to organize. Defaults to Downloads.", required=True),
        },
        "find_duplicates": {
            "folder": param("string", "Folder to scan for duplicate files"),
        },
        "file_properties": {
            "filename": param("string", "File name or path", required=True),
        },
        "list_folder": {
            "folder": param("string", "Folder path or alias to list", required=True),
            "extensions": param("string", "Comma-separated extensions to filter by, e.g. '.pdf,.docx'"),
        },
        "recent_files": {
            "count": param("integer", "Number of recent files to return (default 10)"),
            "folder": param("string", "Folder to scan (default Downloads)"),
        },
        "find_large_files": {
            "folder": param("string", "Folder to scan"),
            "min_size_mb": param("integer", "Minimum file size in MB (default 100)"),
        },
    }
    dangerous_actions = ["delete_file"]

    def __init__(self) -> None:
        from config import settings
        self._settings = settings

    def execute(self, action: str, params: dict[str, Any]) -> ToolResult:
        dispatch = {
            "search_file":      self._search_file,
            "open_file":        self._open_file,
            "open_folder":      self._open_folder,
            "delete_file":      self._delete_file,
            "rename_file":      self._rename_file,
            "copy_file":        self._copy_file,
            "move_file":        self._move_file,
            "create_folder":    self._create_folder,
            "organize_folder":  self._organize_folder,
            "find_duplicates":  self._find_duplicates,
            "file_properties":  self._file_properties,
            "list_folder":      self._list_folder,
            "recent_files":     self._recent_files,
            "find_large_files": self._find_large_files,
        }
        fn = dispatch.get(action)
        if fn is None:
            return self._not_implemented(action)
        return fn(params)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _resolve_folder(self, folder: str | None) -> Path:
        if not folder:
            return self._settings.USER_HOME
        folder_lower = folder.lower().strip()
        if folder_lower in FOLDER_ALIASES:
            return Path(FOLDER_ALIASES[folder_lower])
        p = Path(folder)
        return p if p.exists() else self._settings.USER_HOME

    def _search_files(self, root: Path, query: str, ext_filter: str | None = None) -> list[Path]:
        """Recursive file search."""
        results: list[Path] = []
        query_lower = query.lower()
        try:
            for item in root.rglob("*"):
                if not item.is_file():
                    continue
                if query_lower in item.name.lower():
                    if ext_filter and item.suffix.lower() != ext_filter.lower():
                        continue
                    results.append(item)
                    if len(results) >= 20:
                        break
        except PermissionError:
            pass
        return results

    # ── Actions ───────────────────────────────────────────────────────────────

    def _search_file(self, p: dict) -> ToolResult:
        query = p.get("query", "").strip()
        if not query:
            return ToolResult.fail("Please tell me what file to search for.")
        folder = self._resolve_folder(p.get("folder"))
        ext = p.get("extension", "").strip() or None
        results = self._search_files(folder, query, ext)
        if not results:
            return ToolResult.fail(f"No files matching '{query}' found in {folder}.")
        paths = [str(r) for r in results]
        msg = f"Found {len(results)} file(s) matching '{query}': {results[0].name}"
        if len(results) > 1:
            msg += f" and {len(results) - 1} more."
        return ToolResult.ok(msg, data={"files": paths, "count": len(results)})

    def _open_file(self, p: dict) -> ToolResult:
        filename = p.get("filename", "").strip()
        if not filename:
            return ToolResult.fail("Please specify which file to open.")
        application = p.get("application", "").strip().lower()
        search_first = str(p.get("search_first", "false")).lower() == "true"

        # Direct path?
        fp = Path(filename)
        if not fp.exists() and not fp.is_absolute():
            # Search for it
            results = self._search_files(self._settings.USER_HOME, filename)
            if results:
                fp = results[0]
            else:
                return ToolResult.fail(f"Could not find file '{filename}' on your computer.")

        if not fp.exists():
            return ToolResult.fail(f"File not found: {filename}")

        try:
            if application:
                app_path = self._settings.APP_PATHS.get(application, application)
                os.startfile(str(fp), f"open")
                subprocess.Popen([app_path, str(fp)], shell=True)
            else:
                os.startfile(str(fp))
            return ToolResult.ok(f"Opening {fp.name}.")
        except Exception as e:
            return ToolResult.fail(f"Could not open {fp.name}: {e}")

    def _open_folder(self, p: dict) -> ToolResult:
        folder = p.get("folder", "").strip()
        if not folder:
            return ToolResult.fail("Please specify which folder to open.")
        path = self._resolve_folder(folder)
        try:
            os.startfile(str(path))
            return ToolResult.ok(f"Opened {path.name} in File Explorer.")
        except Exception as e:
            return ToolResult.fail(f"Could not open folder: {e}")

    def _delete_file(self, p: dict) -> ToolResult:
        filename = p.get("filename", "").strip()
        permanent = str(p.get("permanent", "false")).lower() == "true"
        if not filename:
            return ToolResult.fail("Please specify which file to delete.")
        fp = Path(filename)
        if not fp.exists():
            results = self._search_files(self._settings.USER_HOME, filename)
            if results:
                fp = results[0]
            else:
                return ToolResult.fail(f"File '{filename}' not found.")
        try:
            if permanent:
                fp.unlink()
                return ToolResult.ok(f"Permanently deleted {fp.name}.")
            else:
                try:
                    import send2trash
                    send2trash.send2trash(str(fp))
                except ImportError:
                    fp.unlink()
                return ToolResult.ok(f"Moved {fp.name} to Recycle Bin.")
        except Exception as e:
            return ToolResult.fail(f"Could not delete {fp.name}: {e}")

    def _rename_file(self, p: dict) -> ToolResult:
        filename = p.get("filename", "").strip()
        new_name = p.get("new_name", "").strip()
        if not filename or not new_name:
            return ToolResult.fail("Please specify both the current file name and the new name.")
        fp = Path(filename)
        if not fp.exists():
            results = self._search_files(self._settings.USER_HOME, filename)
            if results:
                fp = results[0]
            else:
                return ToolResult.fail(f"File '{filename}' not found.")
        new_path = fp.parent / new_name
        try:
            fp.rename(new_path)
            return ToolResult.ok(f"Renamed {fp.name} to {new_name}.")
        except Exception as e:
            return ToolResult.fail(f"Could not rename file: {e}")

    def _copy_file(self, p: dict) -> ToolResult:
        source = Path(p.get("source", "").strip())
        dest = self._resolve_folder(p.get("destination"))
        if not source.exists():
            return ToolResult.fail(f"Source file '{source}' not found.")
        try:
            shutil.copy2(str(source), str(dest))
            return ToolResult.ok(f"Copied {source.name} to {dest}.")
        except Exception as e:
            return ToolResult.fail(f"Copy failed: {e}")

    def _move_file(self, p: dict) -> ToolResult:
        source = Path(p.get("source", "").strip())
        dest = self._resolve_folder(p.get("destination"))
        if not source.exists():
            return ToolResult.fail(f"Source file '{source}' not found.")
        try:
            shutil.move(str(source), str(dest))
            return ToolResult.ok(f"Moved {source.name} to {dest}.")
        except Exception as e:
            return ToolResult.fail(f"Move failed: {e}")

    def _create_folder(self, p: dict) -> ToolResult:
        name = p.get("folder_name", "").strip()
        if not name:
            return ToolResult.fail("Please specify a folder name.")
        parent = self._resolve_folder(p.get("parent")) or self._settings.PROJECTS_DIR
        new_dir = parent / name
        new_dir.mkdir(parents=True, exist_ok=True)
        return ToolResult.ok(f"Created folder '{name}' at {parent}.", data={"path": str(new_dir)})

    def _organize_folder(self, p: dict) -> ToolResult:
        folder = self._resolve_folder(p.get("folder") or "downloads")
        moved = 0
        errors = 0
        for item in folder.iterdir():
            if not item.is_file():
                continue
            category = EXTENSION_MAP.get(item.suffix.lower())
            if not category:
                category = "Other"
            target_dir = folder / category
            target_dir.mkdir(exist_ok=True)
            try:
                shutil.move(str(item), str(target_dir / item.name))
                moved += 1
            except Exception:
                errors += 1
        msg = f"Organized {folder.name}: moved {moved} files into category folders."
        if errors:
            msg += f" {errors} files could not be moved."
        return ToolResult.ok(msg, data={"moved": moved, "errors": errors, "folder": str(folder)})

    def _find_duplicates(self, p: dict) -> ToolResult:
        """Find duplicate files by size + name similarity."""
        folder = self._resolve_folder(p.get("folder") or "downloads")
        size_map: dict[int, list[Path]] = {}
        for item in folder.rglob("*"):
            if not item.is_file():
                continue
            try:
                sz = item.stat().st_size
                size_map.setdefault(sz, []).append(item)
            except Exception:
                continue
        dupes = {k: [str(f) for f in v] for k, v in size_map.items() if len(v) > 1}
        count = sum(len(v) - 1 for v in dupes.values())
        if count == 0:
            return ToolResult.ok(f"No duplicate files found in {folder.name}.")
        msg = f"Found {count} potential duplicate files in {folder.name}."
        return ToolResult.ok(msg, data={"duplicates": dupes, "count": count})

    def _file_properties(self, p: dict) -> ToolResult:
        filename = p.get("filename", "").strip()
        fp = Path(filename)
        if not fp.exists():
            results = self._search_files(self._settings.USER_HOME, filename)
            if results:
                fp = results[0]
            else:
                return ToolResult.fail(f"File '{filename}' not found.")
        stat = fp.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        msg = f"{fp.name}: {size_mb:.2f} MB, last modified {modified}."
        return ToolResult.ok(msg, data={"name": fp.name, "size_mb": round(size_mb, 2), "modified": modified, "path": str(fp)})

    def _list_folder(self, p: dict) -> ToolResult:
        folder = self._resolve_folder(p.get("folder"))
        ext_filter_raw = p.get("extensions", "")
        ext_filters = [e.strip().lower() for e in ext_filter_raw.split(",") if e.strip()] if ext_filter_raw else []
        items = []
        try:
            for item in sorted(folder.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                if ext_filters and item.is_file() and item.suffix.lower() not in ext_filters:
                    continue
                items.append({"name": item.name, "type": "file" if item.is_file() else "folder", "path": str(item)})
        except PermissionError:
            return ToolResult.fail(f"Permission denied to read {folder}.")
        msg = f"{folder.name} contains {len(items)} items."
        return ToolResult.ok(msg, data={"items": items[:50], "folder": str(folder)}, speak=False)

    def _recent_files(self, p: dict) -> ToolResult:
        count = int(p.get("count", 10))
        folder = self._resolve_folder(p.get("folder") or "downloads")
        files = []
        try:
            for item in folder.rglob("*"):
                if item.is_file():
                    try:
                        files.append((item.stat().st_mtime, item))
                    except Exception:
                        continue
        except Exception:
            pass
        files.sort(reverse=True)
        recent = [{"name": f.name, "path": str(f), "modified": datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")}
                  for t, f in files[:count]]
        msg = f"Most recent {len(recent)} files in {folder.name}: {', '.join(r['name'] for r in recent[:3])}"
        if len(recent) > 3:
            msg += f" and {len(recent) - 3} more."
        return ToolResult.ok(msg, data={"files": recent})

    def _find_large_files(self, p: dict) -> ToolResult:
        folder = self._resolve_folder(p.get("folder") or str(self._settings.USER_HOME))
        min_mb = int(p.get("min_size_mb", 100))
        min_bytes = min_mb * 1024 * 1024
        large = []
        try:
            for item in folder.rglob("*"):
                if item.is_file():
                    try:
                        sz = item.stat().st_size
                        if sz >= min_bytes:
                            large.append({"name": item.name, "path": str(item), "size_mb": round(sz / (1024 * 1024), 1)})
                    except Exception:
                        continue
        except Exception:
            pass
        large.sort(key=lambda x: x["size_mb"], reverse=True)
        if not large:
            return ToolResult.ok(f"No files larger than {min_mb} MB found.")
        msg = f"Found {len(large)} large files. Largest: {large[0]['name']} ({large[0]['size_mb']} MB)."
        return ToolResult.ok(msg, data={"files": large[:20]})
