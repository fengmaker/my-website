"""Offline quality checks for the Markdown files in this MkDocs repository."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import html
import os
import re
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml
from mkdocs.config import load_config


@dataclass
class ScanReport:
    markdown_files: int = 0
    nav_targets: int = 0
    tagged_files: int = 0
    image_references: int = 0
    duplicate_groups: list[list[str]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _front_matter(content: str) -> tuple[str | None, str]:
    """Return (front matter, body); only recognize a block at the file start."""
    content = content.removeprefix("\ufeff")
    match = re.match(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", content, re.DOTALL)
    if not match:
        return None, content
    return match.group(1), content[match.end():]


def check_tags(content: str, display_path: str) -> tuple[bool, list[str]]:
    """Validate tags in YAML front matter; return whether tags were present and errors."""
    front, _ = _front_matter(content)
    if front is None:
        return False, []
    try:
        metadata = yaml.safe_load(front) or {}
    except yaml.YAMLError as exc:
        return False, [f"{display_path}: invalid YAML front matter: {exc.__class__.__name__}"]
    if not isinstance(metadata, dict) or "tags" not in metadata:
        return False, []

    tags = metadata["tags"]
    errors: list[str] = []
    if not isinstance(tags, list):
        return True, [f"{display_path}: tags must be a non-empty list of strings"]
    if not tags:
        errors.append(f"{display_path}: tags must not be an empty list")
    seen: set[str] = set()
    for index, tag in enumerate(tags, start=1):
        if not isinstance(tag, str) or not tag.strip():
            errors.append(f"{display_path}: tags[{index}] must be a non-empty string")
            continue
        normalized = tag.strip()
        if normalized in seen:
            errors.append(f"{display_path}: duplicate tag {normalized!r}")
        seen.add(normalized)
    return True, errors


def _without_code(text: str) -> str:
    """Blank fenced, indented, and inline code so examples do not count as images."""
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    fence_char: str | None = None
    fence_size = 0
    for line in lines:
        fence = re.match(r"^ {0,3}(?:> ?)*(`{3,}|~{3,})", line)
        if fence_char is not None:
            close = re.match(
                rf"^ {{0,3}}(?:> ?)*{re.escape(fence_char)}{{{fence_size},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            if close:
                fence_char = None
                fence_size = 0
            result.append("\n" if line.endswith("\n") else "")
            continue
        if fence:
            fence_char = fence.group(1)[0]
            fence_size = len(fence.group(1))
            result.append("\n" if line.endswith("\n") else "")
        elif re.match(r"^ {0,3}(?:> ?)* {4,}", line) or re.match(r"^ {0,3}(?:> ?)*\t", line):
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(line)
    text = "".join(result)
    # Inline code spans use matching runs of backticks, including multiline spans.
    return re.sub(r"(`+)(.*?)\1", lambda m: " " * len(m.group(0)), text, flags=re.DOTALL)


def _unescape_markdown(value: str) -> str:
    value = html.unescape(value.strip())
    return re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])", r"\1", value)


def _inline_image_destination(text: str, open_paren: int) -> tuple[str, int] | None:
    """Read a Markdown image destination and return it with the closing position."""
    start = open_paren + 1
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text):
        return None
    if text[start] == "<":
        end = start + 1
        while end < len(text):
            if text[end] == ">" and (end == 0 or text[end - 1] != "\\"):
                destination = text[start + 1:end]
                close = text.find(")", end + 1)
                return (destination, close) if close >= 0 else None
            end += 1
        return None

    depth = 0
    escaped = False
    end = start
    while end < len(text):
        char = text[end]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        end += 1
    if end >= len(text):
        return None
    destination = text[start:end].strip()
    # A quoted title is not part of the path. Spaces in bare paths are retained.
    destination = re.sub(r"\s+[\"'].*[\"']\s*$", "", destination)
    return destination, end


def _image_destinations(markdown: str) -> list[str]:
    text = _without_code(markdown)
    destinations: list[str] = []
    definitions: dict[str, str] = {}
    definition_re = re.compile(r"(?m)^ {0,3}\[([^\]]+)\]:\s*(<[^>]*>|\S+)(?:\s+.*)?$")
    for match in definition_re.finditer(text):
        label = " ".join(match.group(1).split()).casefold()
        raw = match.group(2)
        definitions[label] = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw

    image_start_re = re.compile(r"!\[([^\]]*)\]")
    for match in image_start_re.finditer(text):
        pos = match.end()
        while pos < len(text) and text[pos].isspace() and text[pos] != "\n":
            pos += 1
        if pos < len(text) and text[pos] == "(":
            parsed = _inline_image_destination(text, pos)
            if parsed is not None:
                destinations.append(_unescape_markdown(parsed[0]))
        elif pos < len(text) and text[pos] == "[":
            close = text.find("]", pos + 1)
            if close >= 0:
                label = text[pos + 1:close] or match.group(1)
                destination = definitions.get(" ".join(label.split()).casefold())
                if destination is not None:
                    destinations.append(_unescape_markdown(destination))
        else:
            destination = definitions.get(" ".join(match.group(1).split()).casefold())
            if destination is not None:
                destinations.append(_unescape_markdown(destination))

    class ImageTagParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.sources: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag.casefold() == "img":
                for name, value in attrs:
                    if name.casefold() == "src" and value:
                        self.sources.append(value)

    parser = ImageTagParser()
    parser.feed(text)
    destinations.extend(_unescape_markdown(item) for item in parser.sources)
    return destinations


def _is_external(destination: str) -> bool:
    parsed = urlsplit(destination.strip())
    return bool(parsed.scheme or parsed.netloc)


def check_images(markdown: str, page: Path, docs_dir: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    destinations = _image_destinations(markdown)
    for destination in destinations:
        if not destination or _is_external(destination):
            continue
        relative = unquote(urlsplit(destination).path)
        if not relative:
            continue
        target = docs_dir / relative.lstrip("/") if relative.startswith("/") else page.parent / relative
        if not target.is_file():
            errors.append(f"{page.relative_to(docs_dir).as_posix()}: missing image {destination!r}")
    return len(destinations), errors


def _nav_values(nav: object):
    if isinstance(nav, str):
        yield nav
    elif isinstance(nav, list):
        for value in nav:
            yield from _nav_values(value)
    elif isinstance(nav, dict):
        for value in nav.values():
            yield from _nav_values(value)


def check_navigation(config_path: Path, docs_dir: Path) -> tuple[int, list[str]]:
    config = load_config(config_file=str(config_path))
    targets = list(_nav_values(config.get("nav") or []))
    errors: list[str] = []
    seen: dict[str, str] = {}
    for target in targets:
        path_text = unquote(urlsplit(target).path)
        if not path_text or _is_external(target):
            continue
        path = docs_dir / path_text.lstrip("/") if path_text.startswith("/") else docs_dir / path_text
        resolved = Path(os.path.normcase(str(path.resolve(strict=False))))
        normalized = str(resolved)
        if normalized in seen:
            errors.append(f"duplicate navigation target {target!r} (also {seen[normalized]!r})")
        else:
            seen[normalized] = target
        if not path.is_file():
            errors.append(f"navigation target does not exist: {target!r}")
    return len(targets), errors


def _normalized_article(content: str) -> str:
    _, body = _front_matter(content)
    body = unicodedata.normalize("NFC", body.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [line.rstrip() for line in body.split("\n")]
    normalized: list[str] = []
    for line in lines:
        if not line.strip() and normalized and not normalized[-1]:
            continue
        normalized.append(line)
    return "\n".join(normalized).strip()


def find_duplicate_articles(files: list[Path], docs_dir: Path) -> list[list[str]]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in files:
        normalized = _normalized_article(path.read_text(encoding="utf-8"))
        if not normalized:
            continue
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        by_hash[digest].append(path.relative_to(docs_dir).as_posix())
    return sorted((sorted(paths) for paths in by_hash.values() if len(paths) > 1), key=lambda group: group[0])


def check_tag_policy(policy_path: Path, files: list[Path], docs_dir: Path) -> list[str]:
    """Require controlled tags only within the explicitly configured content scope."""
    if not policy_path.is_file():
        return []
    try:
        policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise ValueError("expected a mapping")
        for key in ("required", "exclude", "allowed"):
            values = policy.get(key)
            if not isinstance(values, list) or not all(isinstance(v, str) and v.strip() for v in values):
                raise ValueError(f"{key} must be a list of non-empty strings")
        if not policy["allowed"] or len(set(policy["allowed"])) != len(policy["allowed"]):
            raise ValueError("allowed must contain unique tag names")
        aliases = policy.get("aliases", {})
        if not isinstance(aliases, dict):
            raise ValueError("aliases must be a mapping")
        for alias, canonical in aliases.items():
            if (not isinstance(alias, str) or not alias.strip() or alias != alias.strip()
                    or alias in policy["allowed"] or not isinstance(canonical, str)
                    or canonical not in policy["allowed"]):
                raise ValueError("aliases must map non-canonical names to allowed tag names")
    except (yaml.YAMLError, ValueError) as exc:
        return [f"{policy_path.name}: invalid tag policy: {exc}"]

    errors: list[str] = []
    allowed = set(policy["allowed"])
    for path in files:
        relative = path.relative_to(docs_dir)
        if not any(fnmatch.fnmatchcase(relative.as_posix(), pattern) for pattern in policy["required"]):
            continue
        if any(fnmatch.fnmatchcase(relative.as_posix(), pattern) for pattern in policy["exclude"]):
            continue
        display = relative.as_posix()
        front, _ = _front_matter(path.read_text(encoding="utf-8"))
        try:
            metadata = yaml.safe_load(front) if front is not None else {}
        except yaml.YAMLError:
            continue  # check_tags already reports malformed front matter.
        tags = metadata.get("tags") if isinstance(metadata, dict) else None
        if not tags:
            errors.append(f"{display}: tags required by {policy_path.name}")
        elif isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str) and tag not in allowed:
                    if tag in aliases:
                        errors.append(f"{display}: non-canonical tag {tag!r}; use {aliases[tag]!r}")
                    else:
                        errors.append(f"{display}: unknown tag {tag!r}; update {policy_path.name} deliberately")
    return errors


def scan(root: Path) -> ScanReport:
    root = root.resolve()
    docs_dir = root / "docs"
    config_path = root / "mkdocs.yml"
    files = sorted(docs_dir.rglob("*.md"))
    report = ScanReport(markdown_files=len(files))

    try:
        report.nav_targets, nav_errors = check_navigation(config_path, docs_dir)
        report.errors.extend(nav_errors)
    except Exception as exc:  # A config parse error is actionable and should fail the check.
        report.errors.append(f"cannot load {config_path.name}: {exc}")

    for path in files:
        content = path.read_text(encoding="utf-8")
        has_tags, tag_errors = check_tags(content, path.relative_to(root).as_posix())
        report.tagged_files += int(has_tags)
        report.errors.extend(tag_errors)
        count, image_errors = check_images(content, path, docs_dir)
        report.image_references += count
        report.errors.extend(image_errors)

    report.errors.extend(check_tag_policy(root / "config" / "tags.yml", files, docs_dir))
    report.duplicate_groups = find_duplicate_articles(files, docs_dir)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run offline checks on this MkDocs documentation tree.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    parser.add_argument("--report", action="store_true", help="include scan counters")
    args = parser.parse_args(argv)

    report = scan(args.root)
    if args.report:
        print(f"Markdown files: {report.markdown_files}")
        print(f"Navigation targets: {report.nav_targets}")
        print(f"Files with tags: {report.tagged_files}")
        print(f"Image references: {report.image_references}")
    for error in report.errors:
        print(f"ERROR: {error}")
    for group in report.duplicate_groups:
        print("HINT: exact duplicate article body: " + " | ".join(group))
    print(f"Result: {len(report.errors)} error(s), {len(report.duplicate_groups)} exact-duplicate hint(s)")
    print("Scope: local files only; external URL validity and general Markdown links are not checked.")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
