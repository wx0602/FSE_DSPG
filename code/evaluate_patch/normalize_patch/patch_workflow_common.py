from __future__ import annotations

import hashlib
import json
import re
import shlex
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


DEFAULT_REPO_ROOT = Path("/media/wql/办公/AVR_agent/downstream_dataset/resource_RQ!_sweagent")
DEFAULT_RAW_PATCH_ROOT = Path("/media/wql/办公/AVR_agent/sota/swe-agent/SWE-agent/output_cold/patches")
NORMALIZE_REPORT = "normalize_report.json"
APPLY_STATE = "apply_state.json"


@dataclass(frozen=True)
class SelectedPatch:
    path: Path
    data: bytes
    sha256: str
    duplicate_count: int
    candidate_count: int


@dataclass
class FileDiff:
    lines: list[str]
    paths: list[str] = field(default_factory=list)

    def add_path(self, path: str | None) -> None:
        if path and path not in self.paths:
            self.paths.append(path)

    @property
    def is_java(self) -> bool:
        return any(path.lower().endswith(".java") for path in self.paths)

    @property
    def is_test(self) -> bool:
        return any(is_test_path(path) for path in self.paths)

    @property
    def is_source_java(self) -> bool:
        return self.is_java and not self.is_test and not self.modifies_pom

    @property
    def modifies_pom(self) -> bool:
        return any(basename(path).lower() == "pom.xml" for path in self.paths)


@dataclass(frozen=True)
class PatchAnalysis:
    paths: list[str]
    pom_paths: list[str]
    java_diff_count: int
    kept_java_diff_count: int
    normalized_text: str


def list_projects(repo_root: Path, exclude_names: set[str] | None = None) -> list[Path]:
    if not repo_root.exists():
        raise FileNotFoundError(f"repo root does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise NotADirectoryError(f"repo root is not a directory: {repo_root}")
    excludes = exclude_names or set()
    return sorted(
        (path for path in repo_root.iterdir() if path.is_dir() and path.name not in excludes),
        key=lambda item: item.name,
    )


def timestamped_output_dir(base: Path | None = None) -> Path:
    base_dir = base or Path.cwd()
    return base_dir / time.strftime("normalized_patches_%Y%m%d_%H%M%S")


def latest_normalized_dir(base: Path | None = None) -> Path | None:
    base_dir = base or Path.cwd()
    candidates = [path for path in base_dir.glob("normalized_patches_*") if path.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_patch_files(patch_root: Path, project_name: str) -> list[Path]:
    if not patch_root.exists():
        raise FileNotFoundError(f"patch root does not exist: {patch_root}")

    if patch_root.is_file():
        return [patch_root]

    exact_candidates: list[Path] = []
    for name in (project_name, f"{project_name}.patch", f"{project_name}.diff"):
        candidate = patch_root / name
        if candidate.is_file():
            exact_candidates.append(candidate)

    project_dir = patch_root / project_name
    if project_dir.is_dir():
        exact_candidates.extend(iter_regular_files(project_dir))

    if exact_candidates:
        return unique_paths(exact_candidates)

    fallback_candidates: list[Path] = []
    project_name_lower = project_name.lower()
    for candidate in patch_root.iterdir():
        if candidate.is_file() and candidate.stem.lower() == project_name_lower:
            fallback_candidates.append(candidate)
        elif candidate.is_dir() and candidate.name.lower() == project_name_lower:
            fallback_candidates.extend(iter_regular_files(candidate))

    return unique_paths(fallback_candidates)


def iter_regular_files(root: Path) -> list[Path]:
    return sorted((path for path in root.rglob("*") if path.is_file()), key=lambda item: str(item.relative_to(root)))


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        result.append(path)
    return result


def choose_representative_patch(paths: list[Path]) -> SelectedPatch | None:
    if not paths:
        return None

    groups: dict[str, dict[str, object]] = {}
    for index, path in enumerate(paths):
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest not in groups:
            groups[digest] = {
                "first_index": index,
                "path": path,
                "data": data,
                "count": 0,
            }
        groups[digest]["count"] = int(groups[digest]["count"]) + 1

    selected = max(groups.values(), key=lambda item: (int(item["count"]), -int(item["first_index"])))
    return SelectedPatch(
        path=selected["path"],  # type: ignore[arg-type]
        data=selected["data"],  # type: ignore[arg-type]
        sha256=hashlib.sha256(selected["data"]).hexdigest(),  # type: ignore[arg-type]
        duplicate_count=int(selected["count"]),
        candidate_count=len(paths),
    )


def decode_patch(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def analyze_patch(text: str) -> PatchAnalysis:
    diffs = parse_file_diffs(text)
    paths = sorted({path for diff in diffs for path in diff.paths})
    pom_paths = sorted({path for diff in diffs if diff.modifies_pom for path in diff.paths})
    java_diffs = [diff for diff in diffs if diff.is_java]
    kept_diffs = [diff for diff in java_diffs if diff.is_source_java]
    normalized_text = "".join(line for diff in kept_diffs for line in diff.lines)
    if normalized_text and not normalized_text.endswith("\n"):
        normalized_text += "\n"
    return PatchAnalysis(
        paths=paths,
        pom_paths=pom_paths,
        java_diff_count=len(java_diffs),
        kept_java_diff_count=len(kept_diffs),
        normalized_text=normalized_text,
    )


def parse_file_diffs(text: str) -> list[FileDiff]:
    diffs: list[FileDiff] = []
    current: FileDiff | None = None

    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.startswith("diff --git "):
            if current is not None:
                diffs.append(current)
            current = FileDiff(lines=[line])
            old_path, new_path = parse_diff_git_paths(line)
            current.add_path(old_path)
            current.add_path(new_path)
            continue

        if current is None:
            if line.startswith("--- "):
                current = FileDiff(lines=[line])
                current.add_path(parse_unified_header_path(line[4:]))
            continue

        if starts_unified_file_header(lines, index, current):
            diffs.append(current)
            current = FileDiff(lines=[line])
            current.add_path(parse_unified_header_path(line[4:]))
            continue

        current.lines.append(line)
        if line.startswith("--- "):
            current.add_path(parse_unified_header_path(line[4:]))
        elif line.startswith("+++ "):
            current.add_path(parse_unified_header_path(line[4:]))
        elif line.startswith("rename from "):
            current.add_path(strip_git_prefix(line[len("rename from ") :].strip()))
        elif line.startswith("rename to "):
            current.add_path(strip_git_prefix(line[len("rename to ") :].strip()))

    if current is not None:
        diffs.append(current)
    return diffs


def starts_unified_file_header(lines: list[str], index: int, current: FileDiff | None) -> bool:
    if current is None:
        return False
    if index + 1 >= len(lines):
        return False
    if not lines[index].startswith("--- ") or not lines[index + 1].startswith("+++ "):
        return False
    if current.lines and current.lines[-1].startswith("diff --git "):
        return False
    return any(line.startswith("@@") for line in current.lines)


def parse_diff_git_paths(line: str) -> tuple[str | None, str | None]:
    payload = line[len("diff --git ") :].strip()
    try:
        parts = shlex.split(payload)
    except ValueError:
        parts = payload.split()
    if len(parts) < 2:
        return None, None
    return strip_git_prefix(parts[0]), strip_git_prefix(parts[1])


def parse_unified_header_path(value: str) -> str | None:
    raw = value.strip()
    if not raw:
        return None
    if raw.startswith('"'):
        try:
            parts = shlex.split(raw)
        except ValueError:
            parts = [raw]
        raw = parts[0] if parts else raw
    else:
        raw = raw.split("\t", 1)[0].split(" ", 1)[0]
    return strip_git_prefix(raw)


def strip_git_prefix(path: str | None) -> str | None:
    if not path:
        return None
    cleaned = path.strip().strip('"')
    if cleaned == "/dev/null":
        return None
    if cleaned.startswith("a/") or cleaned.startswith("b/"):
        cleaned = cleaned[2:]
    return cleaned


def basename(path: str) -> str:
    return re.split(r"[\\/]", path)[-1]


def is_test_path(path: str) -> bool:
    parts = [part.lower() for part in re.split(r"[\\/]+", path) if part]
    if any(part in {"test", "tests", "testsrc", "test-src"} for part in parts):
        return True
    for index, part in enumerate(parts[:-1]):
        if part == "src" and parts[index + 1] == "test":
            return True

    name = basename(path)
    if not name.lower().endswith(".java"):
        return False
    stem = name[:-5]
    lower_stem = stem.lower()
    if lower_stem in {"test", "tests"}:
        return True
    if stem.startswith("Test") and len(stem) > len("Test") and stem[len("Test")].isupper():
        return True
    if stem.endswith(("Test", "Tests", "TestCase", "IT", "ITCase")):
        return True
    return bool(re.search(r"(^test[_-]|[_-]tests?$|[_-]testcase$|[_-]it(case)?$)", lower_stem))
