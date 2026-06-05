# -*- coding: utf-8 -*-
"""Gemini 1.5 Pro 정성 분석 생성 모듈

정량 데이터와 뉴스 검색 결과를 기반으로 주간 분석 리포트를 작성합니다.
"""
import os
import google.generativeai as genai

def load_prompt(prompt_dir: str, prompt_file: str) -> str:
    """프롬프트 템플릿 파일을 로드합니다."""
    # 기본 프롬프트 로드
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
    """Gemini 1.5 Pro API를 호출하여 주간 정성 분석 리포트를 생성합니다.
    
    Args:
        category_id: 카테고리 코드 (예: "A-1")
        category_name: 카테고리 한글 이름
        quant_summary: 정량 데이터 텍스트 요약
        news_results: 뉴스 검색 결과 리스트
        prompt_template: 시스템 프롬프트 텍스트
        prev_report: 지난주 리포트 텍스트 (연속성 확보용)
    
    Returns:
        생성된 분석 리포트 마크다운 텍스트
    """
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return f"# [{category_id}] {category_name} 주간 리포트\n\n> [!WARNING]\n> GEMINI_API_KEY가 설정되지 않아 AI 분석을 생성할 수 없습니다.\n"
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')
    
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
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        error_msg = f"# [{category_id}] {category_name} 주간 리포트\n\n> [!WARNING]\n> Gemini API 호출 중 에러 발생: {e}\n"
        print(f"  [GEMINI ERROR] {category_id}: {e}")
        return error_msg
