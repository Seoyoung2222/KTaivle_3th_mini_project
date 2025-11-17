# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

def get_project_root(hint: Optional[Path] = None) -> Path:
    """
    프로젝트 루트 추정:
    - uv.lock / pyproject.toml / apps / student / .git 중 하나라도 보이면 그 위치를 루트로 간주
    - 실패 시 현재 작업 디렉토리(CWD)
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
    """
    경로를 만들어두고 안전하게 텍스트 저장 (윈도우 한글 경로 대응)
    """
    ensure_dir(path.parent)
    with open(path, "w", encoding=encoding, newline="\n") as f:
        f.write(text)

def default_output_dir() -> Path:
    """
    .env의 OUTPUT_DIR이 있으면 우선 사용.
    없으면 <PROJECT_ROOT>/data/processed 반환.
    """
    env_dir = os.getenv("OUTPUT_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    root = get_project_root()
    return (root / "data" / "processed").resolve()
