# -*- coding: utf-8 -*-
"""제미나이 정성 분석 생성 모듈 (멀티모델 폴백 + 포맷 가드레일)

1. gemini-2.5-flash -> gemini-2.0-flash -> gemini-2.5-flash-lite 3단계 모델 서버풀 폴백으로
   특정 모델 503 과부하 시에도 실패 없이 리포트를 생성합니다.
2. 모든 시도 실패 시 에러 텍스트를 마크다운 파일에 오염시키지 않고 예외(RuntimeError)를 발생시켜
   재시도 및 토요일 자동 복구(Self-Heal) 워크플로우가 정확히 감지하도록 합니다.
3. 날짜 기준점 명시, 허구 출처('(가상)', '(가정)') 금지, 86KB 공백 패딩 폭주 제거 후처리를 수행합니다.
"""
import os
import re
import time
from datetime import datetime, timedelta
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


def clean_markdown_output(text: str) -> str:
    """생성된 마크다운에서 중복 날짜 헤더와 비정상 공백 패딩 폭주를 제거합니다."""
    # uploader.py가 상단에 '## 🗓️ YYYY-MM-DD'를 삽입하므로 본문 내 중복 생성 헤더 제거
    text = re.sub(r'^\s*##\s*🗓️.*$', '', text, flags=re.MULTILINE)
    # 마크다운 표 셀 내부 등에서 발생하는 수만 칸 공백 패딩 폭주 차단
    text = re.sub(r'[ \t]{4,}', '  ', text)
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


def generate_analysis(
    category_id: str,
    category_name: str,
    quant_summary: str,
    news_results: list,
    prompt_template: str,
    prev_report: str = "",
) -> str:
    """멀티모델 폴백 체인을 통해 주간 정성 분석 리포트를 생성합니다."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)

    today_dt = datetime.now()
    today_str = today_dt.strftime('%Y-%m-%d')
    week_ago_str = (today_dt - timedelta(days=7)).strftime('%Y-%m-%d')

    # 뉴스 결과 포맷팅 (날짜 + 매체 + 제목 명시)
    news_text = "(이번 주 검색된 실시간 뉴스가 없습니다. 정량 데이터와 확인된 사실만 기술하세요.)"
    if news_results:
        news_lines = []
        for i, n in enumerate(news_results, 1):
            pub_dt = n.get('date') or today_str
            src = n.get('source', 'News')
            news_lines.append(f"{i}. [{pub_dt} | {src}] {n['title']}")
            if n.get('snippet'):
                news_lines.append(f"   → {n['snippet']}")
        news_text = '\n'.join(news_lines)

    # 이전 유효 리포트 컨텍스트 (최대 1800자)
    prev_context = "첫 주차 분석이거나 직전 참고 리포트가 없습니다. 이번 주 현황 중심으로 작성하세요."
    if prev_report:
        prev_context = (
            "아래는 과거 직전 리포트 요약입니다(과거 시점 참고용이며, 이번 주 날짜 계산에 사용하지 마세요):\n"
            f"{prev_report[:1800]}"
        )

    full_prompt = f"""{prompt_template}

---
## 분석 기준 시점 및 대상 (절대 준수)
- 오늘 날짜(분석 기준일): **{today_str}**
- 이번 주 분석 대상 기간: **{week_ago_str} ~ {today_str}**
- 카테고리: [{category_id}] {category_name}

## ⚠️ 데이터 무결성 및 포맷 엄수 규칙
1. **날짜 정확성**: 오늘 날짜는 {today_str}입니다. 과거 리포트의 날짜에 7일을 더하는 식으로 날짜를 추측하지 말고, 반드시 제공된 실시간 뉴스 날짜({week_ago_str}~{today_str})와 정량 데이터의 실제 관측일을 표기하세요.
2. **허구 출처 절대 금지**: `(가상)`, `(가정)` 같은 가짜 출처나 확인되지 않은 이벤트를 절대 창작하지 마세요.
3. **중복 날짜 헤더 금지**: 본문 내에 `## 🗓️` 날짜 제목을 출력하지 마세요(시스템이 상단에 자동 삽입합니다).
4. **간결한 표 포맷**: 마크다운 표는 열(Column) 개수를 **최대 4열 이내**로 구성하고, 셀 내부에 불필요한 연속 공백 패딩을 절대 넣지 마세요.

## 이번 주 정량 데이터 요약 (실측치)
{quant_summary if quant_summary else "(이 카테고리는 별도 시계열 정량 지표가 없으므로 뉴스·정책 팩트 분석에 집중하세요. '3. 정량 지표 추이' 섹션은 핵심 정책/시장 수치 개조식 요약으로 대체하세요.)"}

## 이번 주 주요 실시간 뉴스 (최근 7일 검증 피드)
{news_text}

## 직전 리포트 참고 (연속성 비교용)
{prev_context}

---
위 데이터를 기반으로 [{category_id} {category_name}] 주간 분석 리포트를 한국어로 작성하세요.
리포트 첫 줄은 반드시 `# [{category_id}] {category_name} — 주간 분석 리포트`로 시작하세요.
"""

    model_fallback_chain = [
        ("Primary-2.5-Flash", "gemini-2.5-flash", 15),
        ("Retry-2.5-Flash", "gemini-2.5-flash", 25),
        ("Fallback-2.0-Flash", "gemini-2.0-flash", 15),
        ("Fallback-2.0-Flash-Retry", "gemini-2.0-flash", 20),
        ("Fallback-2.5-Flash-Lite", "gemini-2.5-flash-lite", 15),
        ("Fallback-2.5-Flash-Lite-Retry", "gemini-2.5-flash-lite", 0),
    ]

    last_err = None
    for idx, (stage_name, model_name, wait_sec) in enumerate(model_fallback_chain, 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8192,
                    http_options=types.HttpOptions(timeout=90000),
                ),
            )
            cleaned = clean_markdown_output(response.text or "")
            if len(cleaned) < 250:
                raise ValueError(f"생성된 응답 길이가 너무 짧습니다 ({len(cleaned)}자)")
            print(f"  ✓ [{stage_name} | {model_name}] 생성 성공 ({len(cleaned)}자)")
            return cleaned
        except Exception as e:
            last_err = e
            print(f"  ⚠️ [{idx}/{len(model_fallback_chain)} {stage_name} | {model_name}] 에러: {str(e)[:110]}")
            if wait_sec > 0:
                time.sleep(wait_sec)

    raise RuntimeError(f"[{category_id}] 모든 모델 폴백 시도 실패: {last_err}")
