# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
import re

from student.common.fs_utils import default_output_dir, safe_save_text
# 아래 함수는 기존 파일에 이미 있을 가능성이 큽니다.
# from student.common.writer import render_enveloped  # 이미 같은 파일에 있다면 생략

KST = timezone(timedelta(hours=9))

def _slugify(text: str) -> str:
    text = re.sub(r"\s+", "-", (text or "").strip())
    text = re.sub(r"[^0-9A-Za-z가-힣\-_]+", "", text)
    return text[:80] or "output"

def save_markdown(kind: str, query: str, payload: Dict[str, Any], fname_prefix: str = "") -> str:
    """
    권장 경로: kind(day1/day2/day3/pps 등), query, payload를 받아
    <ROOT or OUTPUT_DIR>/data/processed 에 안전 저장하고 절대경로를 반환.
    본문은 render_enveloped(kind, query, payload, saved_path)로 구성합니다.
    """
    outdir = default_output_dir()
    ts = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    base = _slugify(fname_prefix or query or "query")
    fname = f"{ts}__{_slugify(kind)}__{base}.md"
    abspath = (outdir / fname).resolve()

    # 기존에 writer.py에 있는 렌더러 사용
    body_md = render_enveloped(kind, query, payload, saved_path=str(abspath))
    safe_save_text(abspath, body_md)
    return str(abspath)

# (선택) 이전 시그니처 호환: "이미 완성된 markdown 문자열"을 저장하고 싶을 때
def save_markdown_from_text(route: str, query: str, markdown: str, fname_prefix: str = "") -> str:
    outdir = default_output_dir()
    ts = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    base = _slugify(fname_prefix or query or "query")
    fname = f"{ts}__{_slugify(route)}__{base}.md"
    abspath = (outdir / fname).resolve()
    safe_save_text(abspath, markdown)
    return str(abspath)

# ※ render_enveloped, render_day1/day2/day3, _compose_envelope 등은 기존 코드 유지
# def render_enveloped(kind: str, query: str, payload: Dict[str, Any], saved_path: str) -> str:
#     ...
