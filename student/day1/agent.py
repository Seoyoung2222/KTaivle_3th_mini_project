# -*- coding: utf-8 -*-
"""
Day1: 웹+주가+기업개요 에이전트 (강사용/답지 버전)
- 역할: 사용자 질의를 받아 Day1 본체 호출 → 결과 렌더 → 파일 저장(envelope) → 응답
- 본 파일은 "UI용 래퍼"로, 실질적인 수집/요약 로직은 impl/agent.py 등에 있음.
- 주의: 학생용과 동일한 TODO 마커/설명을 유지하되, 아래에 '정답 구현'을 채워 넣었습니다.
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List
import os
import re

from google.genai import types
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

from student.common.schemas import Day1Plan
from student.common.writer import render_day1, render_enveloped
from student.common.fs_utils import save_markdown
from student.day1.impl.agent import Day1Agent
from student.day1.impl.web_search import looks_like_ticker

# ------------------------------------------------------------------------------
# TODO[DAY1-A-01] 모델 선택
#  목적:
#    - Day1 래퍼에서 간단한 텍스트 가공(필요 시)나 메타 로직에 쓰일 수 있는 경량 LLM을 지정.
#    - 주 로직은 impl에 있으므로, 여기서는 가벼운 모델이면 충분.
#  지침:
#    - LiteLlm(model="openai/gpt-4o-mini")와 같이 할당.
#    - 모델 문자열은 환경/과금에 맞춰 수정 가능.
# ------------------------------------------------------------------------------
# 정답 구현(예시):
MODEL = LiteLlm(model="openai/gpt-4o-mini")


def _extract_tickers_from_query(query: str) -> List[str]:
    """
    사용자 질의에서 '티커 후보'를 추출합니다.
    예시:
      - "AAPL 주가 알려줘"      → ["AAPL"]
      - "삼성전자 005930 분석"  → ["005930"]
      - "NVDA/TSLA 비교"       → ["NVDA", "TSLA"]
    구현 포인트:
      1) 두 타입 모두 잡아야 함
         - 영문 대문자 1~5자 (미국 티커 일반형) + 선택적 .XX (예: BRK.B 처럼 도메인 일부가 있을 수 있으나, 여기선 단순히 대문자 1~5자를 1차 타깃)
         - 숫자 6자리 (국내 종목코드)
      2) 중복 제거(순서 유지)
      3) 불필요한 특수문자 제거 후 패턴 매칭
    """
    # ----------------------------------------------------------------------------
    # TODO[DAY1-A-02] 구현 지침
    #  - re.findall을 이용해 패턴을 두 번 찾고(영문/숫자), 순서대로 합친 뒤 중복 제거하세요.
    #  - 영문 패턴 예: r"\b[A-Z]{1,5}\b"
    #  - 숫자 패턴 예: r"\b\d{6}\b"
    #  - 반환: ['AAPL', '005930'] 형태의 리스트
    # ----------------------------------------------------------------------------
    # 정답 구현:
    # 공백/구분자 정리 (슬래시, 콤마 등은 공백으로 치환하여 매칭 안정화)
    cleaned = re.sub(r"[\/,\|]", " ", query.upper())

    alpha_hits = re.findall(r"\b[A-Z]{1,5}\b", cleaned)   # 예: AAPL, NVDA, TSLA
    digit_hits = re.findall(r"\b\d{6}\b", cleaned)        # 예: 005930

    merged = alpha_hits + digit_hits  # 지침에 따라 두 번 찾은 뒤 순차 결합
    # 중복 제거(앞쪽 우선 유지)
    deduped: List[str] = []
    seen = set()
    for sym in merged:
        if sym not in seen:
            deduped.append(sym)
            seen.add(sym)
    return deduped


def _normalize_kr_tickers(tickers: List[str]) -> List[str]:
    """
    한국식 6자리 종목코드에 '.KS'를 붙여 yfinance 호환 심볼로 보정합니다.
    예:
      ['005930', 'AAPL'] → ['005930.KS', 'AAPL']
    구현 포인트:
      1) 각 원소가 6자리 숫자면 뒤에 '.KS'를 붙임
      2) 이미 확장자가 붙은 경우(예: '.KS')는 그대로 둠
    """
    # ----------------------------------------------------------------------------
    # TODO[DAY1-A-03] 구현 지침
    #  - 숫자 6자리 탐지: re.fullmatch(r"\d{6}", sym)
    #  - 맞으면 f"{sym}.KS" 로 변환
    #  - 아니면 원본 유지
    # ----------------------------------------------------------------------------
    # 정답 구현:
    normalized: List[str] = []
    for sym in tickers:
        if re.fullmatch(r"\d{6}", sym):
            normalized.append(f"{sym}.KS")
        else:
            normalized.append(sym)
    return normalized


def _handle(query: str) -> Dict[str, Any]:
    """
    Day1 전체 흐름(오케스트레이션):
      1) 키 준비: os.getenv("TAVILY_API_KEY", "")
      2) 티커 추출 → 한국형 보정
      3) Day1Plan 구성
         - do_web=True (웹 검색은 기본 수행)
         - do_stocks=True/False (티커가 존재하면 True)
         - web_keywords: [query] (필요시 키워드 가공 가능)
         - tickers: 보정된 티커 리스트
      4) Day1Agent(tavily_api_key=...) 인스턴스 생성
      5) agent.handle(query, plan) 호출 → payload(dict) 수신
    반환:
      merge된 표준 스키마 dict (impl/merge.py 참고)
    """
    # ----------------------------------------------------------------------------
    # TODO[DAY1-A-04] 구현 지침
    #  - 1) api_key = os.getenv("TAVILY_API_KEY","")
    #  - 2) tickers = _normalize_kr_tickers(_extract_tickers_from_query(query))
    #       * 보강: looks_like_ticker()로 실제 티커처럼 생긴 것만 남기기
    #         (예: "NIPA", "바우처" 같은 일반 단어가 주가 조회로 가지 않도록)
    #  - 3) plan = Day1Plan(
    #         do_web=True,
    #         do_stocks=bool(tickers),
    #         web_keywords=[query],
    #         tickers=tickers,
    #         output_style="report",
    #       )
    #  - 4) agent = Day1Agent(tavily_api_key=api_key, web_topk=6, request_timeout=20)
    #  - 5) return agent.handle(query, plan)
    # ----------------------------------------------------------------------------
    # 정답 구현:
    import os
    from student.day1.impl.web_search import looks_like_ticker

    # 1) API 키
    api_key = os.getenv("TAVILY_API_KEY", "")

    # 2) 티커 추출 → 한국형 보정 → 실제 티커처럼 보이는 것만 남김
    raw = _extract_tickers_from_query(query)
    normalized = _normalize_kr_tickers(raw)
    tickers = [t for t in normalized if looks_like_ticker(t)]

    # 3) 계획 구성
    plan = Day1Plan(
        do_web=True,
        do_stocks=bool(tickers),
        web_keywords=[query],
        tickers=tickers,
        output_style="report",
    )

    # 4) 에이전트 생성
    agent = Day1Agent(
        tavily_api_key=api_key,
        web_topk=6,
        request_timeout=20,
    )

    # 5) 실행
    return agent.handle(query, plan)



def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
    **kwargs,
) -> Optional[LlmResponse]:
    """
    UI 엔트리포인트:
      1) llm_request.contents[-1]에서 사용자 메시지 텍스트(query) 추출
      2) _handle(query) 호출 → payload 획득
      3) 본문 마크다운 렌더: render_day1(query, payload)
      4) 저장: save_markdown(query, route='day1', markdown=본문MD) → 경로
      5) envelope: render_enveloped('day1', query, payload, saved_path)
      6) LlmResponse로 반환
      7) 예외시 간단한 오류 텍스트 반환
    """
    # ----------------------------------------------------------------------------
    # TODO[DAY1-A-05] 구현 지침
    #  - last = llm_request.contents[-1]; last.role == "user" 인지 확인
    #  - query = last.parts[0].text
    #  - payload = _handle(query)
    #  - body_md = render_day1(query, payload)
    #  - saved = save_markdown(query=query, route="day1", markdown=body_md)
    #  - md = render_enveloped(kind="day1", query=query, payload=payload, saved_path=saved)
    #  - return LlmResponse(content=types.Content(parts=[types.Part(text=md)], role="model"))
    #  - 예외시: "Day1 에러: {e}"
    # ----------------------------------------------------------------------------
    # 정답 구현:
    try:
        last = llm_request.contents[-1]
        if last.role == "user":
            query = last.parts[0].text
            payload = _handle(query)

            body_md = render_day1(query, payload)
            saved_path = save_markdown(query=query, route="day1", markdown=body_md)
            enveloped_md = render_enveloped(
                kind="day1",
                query=query,
                payload=payload,
                saved_path=saved_path,
            )

            return LlmResponse(
                content=types.Content(
                    parts=[types.Part(text=enveloped_md)],
                    role="model",
                )
            )
    except Exception as e:
        # 강사용: 에러 원인을 바로 확인할 수 있도록 간결 메시지 반환
        return LlmResponse(
            content=types.Content(
                parts=[types.Part(text=f"Day1 에러: {e}")],
                role="model",
            )
        )
    return None


# ------------------------------------------------------------------------------
# TODO[DAY1-A-06] Agent 메타데이터 다듬기
#  - name: 영문/숫자/언더스코어만 (하이픈 금지)
#  - description: 에이전트 기능 요약
#  - instruction: 출력 형태/톤/근거표시 등 지침
# ------------------------------------------------------------------------------
# 정답 구현:
day1_web_agent = Agent(
    name="Day1WebAgent",
    model=MODEL,
    description=(
        "웹 검색과 주가, 기업 개요, 시장 리포트를 분석해 종합 요약 보고서를 생성하는 에이전트. "
        "결과는 표와 구체적인 수치, 시점 정보(날짜·기간·단위)를 명확히 포함하며, "
        "단순 나열이 아닌 인사이트 중심으로 정리한다. "
        "그래프나 시각화 요청이 있더라도 실제 이미지를 첨부하지 않고, "
        "대신 데이터의 변화를 서술적으로 요약한다."
    ),
    instruction=(
        "1. 웹 검색 및 주가 데이터를 결합하여 구조화된 Markdown 보고서를 작성한다.\n"
        "2. 보고서는 반드시 다음 섹션을 포함한다:\n"
        "   - 📌 핵심 요약: 2~3문장으로 전체 내용 요약\n"
        "   - 📰 주요 뉴스/리포트: 최신 3~5개 요약 (출처와 날짜 포함)\n"
        "   - 💹 주가 및 기업 동향: 주요 변화율, 기간, 시장 반응 서술\n"
        "   - 🧩 인사이트: 산업 전망, 기업 포지션, 시장 트렌드 비교 분석\n"
        "3. 수치, 날짜, 출처는 명시적으로 표기한다.\n"
        "4. '그래프'나 '시각화' 요청 시 실제 이미지를 첨부하지 말고, "
        "‘그래프 없이 데이터 추이 요약’ 형태로 텍스트로 서술한다.\n"
        "5. 가능한 한 문장 길이를 줄이고 핵심 정보 위주로 Markdown 표, 목록 등을 활용해 가독성을 높인다."
    ),
    tools=[],
    before_model_callback=before_model_callback,
)

