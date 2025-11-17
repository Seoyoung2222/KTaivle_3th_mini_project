# -*- coding: utf-8 -*-
import os
from __future__ import annotations

from typing import Dict, Any
from textwrap import dedent
from student.common.fs_utils import default_output_dir, safe_save_text

from datetime import datetime, timezone, timedelta
# --------- 본문 렌더러들 ---------
def render_day1(query: str, payload: Dict[str, Any]) -> str:
    web = payload.get("web_top", []) or []
    prices = payload.get("prices", []) or []
    profile = (payload.get("company_profile") or "").strip()
    profile_sources = payload.get("profile_sources") or []

    lines = [f"# 웹 리서치 리포트", f"- 질의: {query}", ""]

    # 1) 시세 스냅샷
    if prices:
        lines.append("## 시세 스냅샷")
        for p in prices:
            sym = p.get("symbol", "")
            cur = f" {p.get('currency')}" if p.get("currency") else ""
            if p.get("price") is not None:
                lines.append(f"- **{sym}**: {p['price']}{cur}")
            else:
                lines.append(f"- **{sym}**: (가져오기 실패) — {p.get('error','')}")
        lines.append("")

    # 2) 기업 정보 요약(발췌 + 출처)
    if profile:
        # 500자 정도로 길이 제한(가독)
        short = profile[:500].rstrip()
        if len(profile) > 500:
            short += "…"
        lines.append("## 기업 정보 요약")
        lines.append(short)
        if profile_sources:
            lines.append("")
            lines.append("**출처(기업 정보):**")
            for u in profile_sources[:3]:
                lines.append(f"- {u}")
        lines.append("")

    # 3) 상위 웹 결과(타이틀 + 메타 + 2줄 발췌)
    if web:
        lines.append("## 관련 링크 & 발췌")
        for r in web[:5]:
            title = r.get("title") or r.get("url") or "link"
            src = r.get("source") or ""
            date = r.get("published_date") or r.get("date") or ""
            url = r.get("url", "")
            tail = f" — {src}" + (f" ({date})" if date else "")
            lines.append(f"- [{title}]({url}){tail}")

            # 2줄 발췌: content > snippet > '' 우선순위
            raw = (r.get("content") or r.get("snippet") or "").strip().replace("\n", " ")
            if raw:
                excerpt = raw[:280].rstrip()
                if len(raw) > 280:
                    excerpt += "…"
                lines.append(f"  > {excerpt}")
        lines.append("")
    
    if payload.get("chart_paths"):
        md += "\n\n## 📈 주가 추이 그래프\n"
        for p in payload["chart_paths"]:
            md += f"![{os.path.basename(p)}]({p})\n"

    # 웹 결과가 전혀 없을 때 힌트
    if not (web or profile or prices):
        lines.append("_참고: 결과가 비어있습니다. 쿼리/도메인 제한/키워드 설정을 확인하세요._")
        lines.append("")

    return "\n".join(lines)


def render_day2(query: str, payload: dict) -> str:
    # 기존 요약/머리말 생성부는 유지
    lines = []
    lines.append(f"# Day2 – RAG 요약")
    lines.append("")
    lines.append(f"**질의:** {query}")
    lines.append("")

    # ── 추가: 초안(answer) 표시
    answer = (payload or {}).get("answer") or ""
    if answer:
        lines.append("## 초안 요약")
        lines.append("")
        lines.append(answer.strip())
        lines.append("")

    # ── 추가: 근거 상위 K 표
    contexts = (payload or {}).get("contexts") or []
    if contexts:
        lines.append("## 근거(Top-K)")
        lines.append("")
        lines.append("| rank | score | path | chunk_id | excerpt |")
        lines.append("|---:|---:|---|---:|---|")
        for i, c in enumerate(contexts, 1):
            score = f"{float(c.get('score', 0.0)):.3f}"
            path = str(c.get("path") or c.get("meta", {}).get("path") or "")

            # excerpt 후보(우선순위: text > chunk > content)
            raw = (
                c.get("text")
                or c.get("chunk")
                or c.get("content")
                or ""
            )
            excerpt = (str(raw).replace("\n", " ").strip())[:200]

            # chunk_id 후보(우선순위: id > meta.chunk > chunk_id > chunk_index)
            chunk_id = (
                c.get("id")
                or c.get("meta", {}).get("chunk")
                or c.get("chunk_id")
                or c.get("chunk_index")
                or ""
            )

            lines.append(f"| {i} | {score} | {path} | {chunk_id} | {excerpt} |")
        lines.append("")

    return "\n".join(lines)

def render_day3(query: str, payload: Dict[str, Any]) -> str:
    items = payload.get("items", [])
    lines = [f"# 공고 탐색 결과", f"- 질의: {query}", ""]
    if items:
        lines.append("| 제목 | 기관 | 공고번호 | 공고일 | 입찰 마감 | 예산 | 링크 |")
        lines.append("|---|---|---|---|---|---:|---|")
        for it in items[:20]:
            title = it.get("title","-")
            agency = it.get("agency","-")
            bid_no = it.get("bid_no","")
            ann = it.get("announce_date","")
            close = it.get("close_date","")
            budget = it.get("budget","-")
            url = it.get("url","")
            link = f"[바로가기]({url})" if url else "-"
            lines.append(f"| {title} | {agency} | {bid_no} | {ann} | {close} | {budget} | {link} |")
    else:
        lines.append("관련 공고를 찾지 못했습니다.")
    return "\n".join(lines)

def _compose_envelope(kind: str, query: str, body_md: str, saved_path: str) -> str:
    header = dedent(f"""\
    ---
    output_schema: v1
    type: markdown
    route: {kind}
    saved: {saved_path}
    query: "{query.replace('"','\\\"')}"
    ---

    """)
    footer = dedent(f"""\n\n---\n> 저장 위치: `{saved_path}`\n""")
    return header + body_md.strip() + footer

def render_enveloped(kind: str, query: str, payload: Dict[str, Any], saved_path: str) -> str:
    if kind == "day1":
        body = render_day1(query, payload)
    elif kind == "day2":
        body = render_day2(query, payload)
    elif kind in ("day3", "pps"):   # ✅ pps도 day3 렌더 사용
        body = render_day3(query, payload)
    else:
        body = f"### 결과\n\n(알 수 없는 kind: {kind})"
    return _compose_envelope(kind, query, body, saved_path)


KST = timezone(timedelta(hours=9))

def save_markdown(kind: str, query: str, payload: Dict[str, Any], fname_prefix: str) -> str:
    """
    kind(day1/day2/day3/pps 등), query, payload를 받아
    data/processed 아래에 안전하게 저장하고 절대경로를 반환합니다.
    """
    outdir = default_output_dir()
    ts = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in (query or "query").strip())
    fname = f"{ts}__{kind}__{fname_prefix or safe_query}.md"
    abspath = (outdir / fname).resolve()

    # 본문을 writer 레이어에서 구성
    body_md = render_enveloped(kind, query, payload, saved_path=str(abspath))
    safe_save_text(abspath, body_md)
    return str(abspath)