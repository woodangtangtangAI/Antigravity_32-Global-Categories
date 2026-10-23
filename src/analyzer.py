# -*- coding: utf-8 -*-
"""제미나이 정성 분석 생성 모듈"""
import os
import time
from google import genai
from google.genai import types

def load_prompt(prompt_dir: str, prompt_file: str) -> str:
    """프롬프트 템플릿 파일을 로드합니다."""
    base_path = os.path.join(prompt_dir, 'base_prompt.txt')
    group_path = os.path.join(prompt_dir, prompt_file)
    
    base_prompt = ""
    group_prompt = ""
    
    if os.path.exists(base_path):
        with open(base_path, 'r', encoding='utf-8') as f:
            base_prompt = f.read()
    
    if os.path.exists(group_path):
        with open(group_path, 'r', encoding='utf-8') as f:
            group_prompt = f.read()
    
    return f"{base_prompt}\n\n{group_prompt}"

def generate_analysis(
    category_id: str,
    category_name: str,
    quant_summary: str,
    news_results: list,
    prompt_template: str,
    prev_report: str = "",
) -> str:
    """Gemini 2.5 Flash API를 호출하여 주간 정성 분석 리포트를 생성합니다."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return f"# [{category_id}] {category_name} 주간 리포트\n\n> [!WARNING]\n> GEMINI_API_KEY가 설정되지 않아 AI 분석을 생성할 수 없습니다.\n"
    
    client = genai.Client(api_key=api_key)
    
    # 뉴스 결과 포맷팅
    news_text = "(이번 주 검색된 뉴스가 없습니다. 자체 지식 기반으로 분석하세요.)"
    if news_results:
        news_lines = []
        for i, n in enumerate(news_results, 1):
            news_lines.append(f"{i}. [{n.get('source', 'Unknown')}] {n['title']}")
            if n.get('snippet'):
                news_lines.append(f"   → {n['snippet']}")
        news_text = '\n'.join(news_lines)
    
    # 이전 리포트 요약 (토큰 절약을 위해 2000자로 제한)
    prev_context = "첫 주차 분석입니다. 지난주 대비 비교 없이 현황 중심으로 작성하세요."
    if prev_report:
        prev_context = f"아래는 지난주 분석 요약입니다. 변화를 비교하세요:\n{prev_report[:2000]}"
    
    # 프롬프트 조립
    full_prompt = f"""{prompt_template}

---
## 분석 대상
- 카테고리: [{category_id}] {category_name}

## 이번 주 정량 데이터
{quant_summary if quant_summary else "(이번 주 수집된 정량 데이터가 없습니다. 정성 분석에 집중하세요.)"}

## 이번 주 주요 뉴스 (검색 결과)
{news_text}

## 지난 주 분석 (연속성 참고)
{prev_context}

---
위 데이터를 기반으로 [{category_id} {category_name}] 주간 분석 리포트를 한국어로 작성하세요.
리포트 상단에 `# [{category_id}] {category_name} — 주간 분석 리포트`를 제목으로 넣으세요.
"""
    
    # 안정적인 2.5 Flash 모델 사용 및 최대 3회 재시도
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_prompt
            )
            if response.text and len(response.text.strip()) > 50:
                return response.text
            raise ValueError("Empty response or blocked by safety settings")
        except Exception as e:
            print(f"  [GEMINI ATTEMPT {attempt}/3] {category_id}: {e}")
            if attempt < 3:
                time.sleep(15)
            else:
                error_msg = f"# [{category_id}] {category_name} 주간 리포트\n\n> [!WARNING]\n> Gemini API 호출 중 에러 발생: {e}\n"
                print(f"  [GEMINI ERROR] {category_id}: {e}")
                return error_msg
