# -*- coding: utf-8 -*-
from __future__ import annotations
import re, time
import os
from typing import Optional
from pathlib import Path

PROCESSED_DIR = Path("data/processed")

def _slugify(text: str) -> str:
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"[^0-9A-Za-z가-힣\-_]+", "", text)
    return text[:80] or "output"

def save_markdown(query: str, route: str, markdown: str) -> str:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    slug = _slugify(query)
    route = _slugify(route or "auto")
    f = PROCESSED_DIR / f"{ts}__{route}__{slug}.md"
    f.write_text(markdown, encoding="utf-8")
    return str(f)


def get_project_root(hint: Optional[Path] = None) -> Path:
    """
    프로젝트 루트를 추정:
    - uv.lock / pyproject.toml / apps / student 디렉토리 중 하나라도 보이면 거기서 멈춤
    - 못 찾으면 현재 작업 디렉토리(CWD) 반환
    """
    start = (hint or Path(__file__)).resolve()
    candidates = [start] + list(start.parents)
    markers = ("uv.lock", "pyproject.toml", "apps", "student", ".git")
    for p in candidates:
        try:
            for m in markers:
                if (p / m).exists():
                    return p
        except Exception:
            pass
    return Path.cwd().resolve()

def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def safe_save_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    ensure_dir(path.parent)
    # Windows 한글 경로/파일명도 안전하게 저장
    with open(path, "w", encoding=encoding, newline="\n") as f:
        f.write(text)

def default_output_dir() -> Path:
    """
    .env의 OUTPUT_DIR(있으면) 또는 <ROOT>/data/processed 반환
    """
    env_dir = os.getenv("OUTPUT_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    root = get_project_root()
    return (root / "data" / "processed").resolve()
