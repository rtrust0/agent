"""版本号工具：Agent / Prompt 发布时基于历史版本自增，避免回滚后重复版本号。"""

import re
from collections.abc import Iterable

_VERSION_PATTERN = re.compile(r"^v(\d+)\.(\d+)$")


def parse_version(version: str | None) -> tuple[int, int] | None:
    if not version:
        return None
    match = _VERSION_PATTERN.match(version.strip())
    if not match:
        return None
    major, minor = match.groups()
    return int(major), int(minor)


def bump_version(version: str) -> str:
    """`v1.2` → `v1.3`；格式非法时回退到 `v0.2`。"""
    parsed = parse_version(version)
    if not parsed:
        return "v0.2"
    major, minor = parsed
    return f"v{major}.{minor + 1}"


def next_version(existing: Iterable[str | None], fallback: str = "v0.1") -> str:
    """在全部历史版本（含当前版本）之上取下一个版本号。

    回滚后再次发布时，不会与历史版本重号。
    """
    candidates = [parsed for parsed in (parse_version(item) for item in existing) if parsed]
    if not candidates:
        return bump_version(fallback)
    major, minor = max(candidates)
    return f"v{major}.{minor + 1}"
