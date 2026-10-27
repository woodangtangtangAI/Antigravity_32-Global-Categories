# -*- coding: utf-8 -*-
"""웹 뉴스 검색 모듈 (Serper.dev API + Google News RSS 무결점 폴백)

카테고리별 최근 7일 이내 실시간 뉴스를 검색하여 Gemini 분석의 팩트 입력 데이터로 사용합니다.
Serper API 키 만료·크레딧 소진(HTTP 400/403 등) 발생 시 서킷브레이커가 즉시 작동하여
무료·무제한 Google News RSS(when:7d) 피드로 자동 전환됩니다.
"""
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
import requests

SERPER_API_URL = "https://google.serper.dev/news"
_SERPER_DISABLED = False


def _normalize_keyword_year(keyword: str) -> str:
    """키워드 내 하드코딩된 연도(2026 등)를 현재 연도에 맞게 자동 보정합니다."""
    current_year = str(datetime.now().year)
    return re.sub(r'\b202[5-9]\b', current_year, keyword)


def _format_pub_date(raw_date: str) -> str:
    """RSS pubDate 문자열을 YYYY-MM-DD 형식으로 변환합니다."""
    if not raw_date:
        return datetime.now().strftime('%Y-%m-%d')
    try:
        dt = parsedate_to_datetime(raw_date)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return raw_date[:16].strip()


def _search_google_news_rss(keyword: str, num_results: int = 4) -> list:
    """Google News RSS(최근 7일)에서 검증된 최신 뉴스 헤드라인·출처·날짜를 수집합니다."""
    results = []
    q = _normalize_keyword_year(keyword)
    # 한글 포함 여부에 따라 로케일 자동 선택
    has_korean = bool(re.search(r'[가-힣]', q))
    hl, gl, ceid = ("ko", "KR", "KR:ko") if has_korean else ("en-US", "US", "US:en")

    encoded = urllib.parse.quote(f"{q} when:7d")
    url = f"https://news.google.com/rss/search?q={encoded}&hl={hl}&gl={gl}&ceid={ceid}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=12) as resp:
            xml_bytes = resp.read()
        root = ET.fromstring(xml_bytes)
        for item in root.findall('.//item')[:num_results]:
            raw_title = (item.findtext('title') or '').strip()
            source = (item.findtext('source') or 'News').strip()
            # Google News 제목 끝의 ' - 매체명' 중복 제거
            suffix = f" - {source}"
            title = raw_title[:-len(suffix)].strip() if raw_title.endswith(suffix) else raw_title
            pub_date = _format_pub_date(item.findtext('pubDate') or '')
            link = (item.findtext('link') or '').strip()
            if title:
                results.append({
                    'title': title,
                    'snippet': '',
                    'link': link,
                    'date': pub_date,
                    'source': source,
                })
    except Exception as e:
        print(f"  [RSS WARNING] '{q}': {e}")
    return results


def search_news(keywords: list, num_results: int = 5) -> list:
    """Serper.dev API를 우선 시도하고, 실패/부족 시 Google News RSS(최근 7일)로 자동 보완합니다."""
    global _SERPER_DISABLED
    api_key = os.environ.get('SERPER_API_KEY')
    all_results = []

    if api_key and not _SERPER_DISABLED:
        for keyword in keywords:
            q = _normalize_keyword_year(keyword)
            try:
                headers = {
                    'X-API-KEY': api_key,
                    'Content-Type': 'application/json',
                }
                payload = {
                    'q': q,
                    'num': num_results,
                    'tbs': 'qdr:w',
                }
                response = requests.post(SERPER_API_URL, json=payload, headers=headers, timeout=10)
                if response.status_code in (400, 401, 402, 403):
                    _SERPER_DISABLED = True
                    print(f"  [INFO] Serper API 비활성/한도초과(HTTP {response.status_code}) 감지 → Google News RSS 모드로 전환합니다.")
                    break
                response.raise_for_status()
                data = response.json()
                for item in data.get('news', []):
                    all_results.append({
                        'title': item.get('title', '').strip(),
                        'snippet': item.get('snippet', '').strip(),
                        'link': item.get('link', '').strip(),
                        'date': item.get('date', '').strip(),
                        'source': item.get('source', 'News').strip(),
                    })
            except Exception as e:
                print(f"  [SEARCH WARNING] '{q}': {e}")
                continue

    # Serper 결과가 부족하거나 비활성화된 경우 Google News RSS로 실시간 최근 7일 뉴스 확보
    if len(all_results) < num_results:
        for keyword in keywords:
            all_results.extend(_search_google_news_rss(keyword, num_results=4))

    # 중복 제거 (정규화된 제목 앞 45자 기준)
    seen_keys = set()
    unique_results = []
    for r in all_results:
        key = re.sub(r'\s+', ' ', r.get('title', '')).strip().lower()[:45]
        if key and key not in seen_keys:
            seen_keys.add(key)
            unique_results.append(r)

    max_return = max(12, num_results * 2)
    return unique_results[:max_return]
