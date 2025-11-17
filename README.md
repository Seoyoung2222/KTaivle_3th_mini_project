## 🚀 AI Multi-Agent System for Web Search · RAG · Government / PPS Analysis  
### 산업 맞춤형 AI 에이전트 시스템

본 프로젝트는 **웹 검색(WebAgent)**, **문서 기반 RAG(RagAgent)**,  
**정부지원사업 분석(GovAgent)**, **조달청(PPS) 입찰 공고 분석(PpsAgent)** 을 통합한  
**멀티 에이전트 기반 자동 분석 시스템**입니다.

사용자가 질의를 입력하면, 시스템은 산업별 상황을 분석해  
가장 적합한 에이전트를 자동 선택하여 **검색 → 분석 → 요약 → 문서화**까지 End-to-End로 처리합니다.

---

## 🧭 프로젝트 구조(Project Overview)

```
apps/
 └─ root_app/          # Root Orchestrator (전체 라우팅)

student/
 ├─ common/            # 공통 스키마, writer, 파일 유틸
 ├─ day1/              # WebAgent (웹검색·기업정보·주가 분석)
 ├─ day2/              # RagAgent (FAISS 기반 RAG)
 └─ day3/
     └─ impl/          
          ├─ GovAgent  # 정부지원사업 공고 분석
          └─ PpsAgent  # 조달청(PPS) 입찰 분석

data/
 ├─ raw/               # 원본 문서
 └─ processed/         # 전처리된 문서

indices/
 └─ day2/              # RAG 임베딩 인덱스 (FAISS)
```

---

## 🎯 프로젝트 목표 (Goals)

✔ 웹 검색·문서·정부·조달 데이터를 통합해 **산업 맞춤형 분석 자동화** 구현  
✔ 자연어 질의 기반 → **근거 기반 요약 + 표준화된 Markdown 리포트 자동 생성**  
✔ ADK 기반 **멀티 에이전트 구조 설계**  
✔ RAG Confidence 기반 **자동 백업 웹 검색 호출**  
✔ 기업/정부 실무 문서 자동화에 활용 가능한 형태

---

## 🔥 핵심 기능 (Core Features)

### 🟦 Day1 — WebAgent  
웹 검색 + 기업 정보 + 주가 분석 에이전트

- Tavily 웹 검색 API 사용  
- Firecrawl 기반 텍스트 크롤링  
- yfinance 기반 주가/기업 재무 요약  
- 웹 + 공식 문서 + 뉴스 **3중 요약 시스템**  
- Markdown 보고서 자동 생성

---

### 🟩 Day2 — RAGAgent  
PDF/문서 기반 **근거 기반 답변 시스템**

- PDF ingestion → Chunking → Embedding 자동화  
- FAISS 벡터 DB 기반 유사도 검색  
- MMR 기반 재랭킹  
- Confidence Score 낮으면 → WebAgent 자동 보조 호출  
- 근거 패시지 포함 Markdown 보고서 생성

---

### 🟧 Day3 — GovAgent  
정부지원사업 공고 자동 분석

- Bizinfo·NIPA 등 다수 공고 페이지 크롤링  
- 지원대상·지원내용·기관·일정 자동 정규화  
- 중요도 기반 우선순위 랭킹  
- Markdown 표 자동 생성

---

### 🟥 Day3 — PpsAgent  
조달청(PPS) 입찰 공고 자동 분석

- PPS API 기반 입찰 공고 수집  
- 공고명 / 예가 / 기관 / 마감일 정규화  
- 입찰 주요 지표 자동 추출  
- 비교 테이블 Markdown 생성

---


### 🟨 Root Orchestrator (핵심 통합 모듈)

사용자 요청을 분석해 에이전트 자동 라우팅:

- **“정부/지원/바우처” → GovAgent**  
- **“PPS/입찰” → PpsAgent**  
- **“문서/근거/FAISS” → RAGAgent**  
- **“웹/뉴스/주가” → WebAgent**  

추가 기능:

- RAG 신뢰도 낮으면 WebAgent 보조 호출  
- 최종 Markdown 리포트 생성

---

## 🔧 사용 방법 (Usage)

### 설치
```bash
uv sync
```

### 실행
```bash
adk web apps
```

### 입력 예시

```text
헬스케어 AI 기술 동향 요약해줘
```

```text
2025년 AI 바우처 지원사업 요약해줘
```

```text
조달청 PPS에서 의료기기 관련 입찰 찾아줘
```

---


## 🧑‍💻 기술 스택 (Tech Stack)

- Python 3.12  
- OpenAI ADK  
- FAISS  
- Tavily Search API  
- Firecrawl  
- yfinance  
- Pydantic  
- Mermaid Diagram  
