# -*- coding: utf-8 -*-
"""
root_agent.py — 루트 오케스트레이터
- Day1/Day2/Day3(정부공고) 에이전트 연결
- PPS(나라장터) 전용 에이전트(day3_pps_agent) 추가
"""

from __future__ import annotations
from typing import Optional
import os

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm

# 서브 에이전트
from student.day1.agent import day1_web_agent
from student.day2.agent import day2_rag_agent
from student.day3.agent import day3_gov_agent
from student.day3.pps_agent import day3_pps_agent

from .prompts import ORCHESTRATOR_DESC, ORCHESTRATOR_PROMPT

# LLM 설정(.env로 조정)
MODEL: Optional[LiteLlm] = LiteLlm(
    model=os.getenv("DAY4_INTENT_MODEL", "openai/gpt-4o-mini"),
    temperature=float(os.getenv("DAY4_TEMPERATURE", "0.2")),
    max_tokens=int(os.getenv("DAY4_MAX_TOKENS", "2000")),
)

root_agent = Agent(
    name="KT_AIVLE_Orchestrator",
    model=MODEL,
    description=ORCHESTRATOR_DESC,
    instruction=ORCHESTRATOR_PROMPT,
    tools=[
        AgentTool(agent=day1_web_agent),   # Day1: 웹/뉴스/시세
        AgentTool(agent=day2_rag_agent),   # Day2: RAG(로컬 인덱스)
        AgentTool(agent=day3_gov_agent),   # Day3(기존): 범용 정부공고
        AgentTool(agent=day3_pps_agent),   # Day3(신규): 나라장터/PPS
    ],
)