"""版本号工具：Agent / Prompt 发布时自增次版本号。"""

import re

_VERSION_PATTERN = re.compile(r"^v(\d+)\.(\d+)$")


def bump_version(version: str) -> str:
    """`v1.2` → `v1.3`；格式非法时回退到 `v0.2`。"""
    match = _VERSION_PATTERN.match(version.strip())
    if not match:
        return "v0.2"
    major, minor = match.groups()
    return f"v{major}.{int(minor) + 1}"
