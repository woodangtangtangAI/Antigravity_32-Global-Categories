# -*- coding: utf-8 -*-
"""웹 뉴스 검색 모듈 (Serper.dev API)

카테고리별 최신 뉴스를 검색하여 Gemini 분석의 입력 데이터로 사용합니다.
"""
import os
import requests

SERPER_API_URL = "https://google.serper.dev/news"

def search_news(keywords: list, num_results: int = 5) -> list:
    """Serper.dev API를 통해 최신 뉴스를 검색합니다.
    
    Args:
        keywords: 검색 키워드 리스트
        num_results: 키워드당 검색 결과 수
    
    Returns:
        [{"title": ..., "snippet": ..., "link": ..., "date": ...}, ...]
    """
    api_key = os.environ.get('SERPER_API_KEY')
    if not api_key:
        print("  [WARNING] SERPER_API_KEY not set. Skipping news search.")
        return []
    
    all_results = []
    
    for keyword in keywords:
        try:
            headers = {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                'q': keyword,
                'num': num_results,
                'tbs': 'qdr:w'  # 최근 1주일
            }
            response = requests.post(SERPER_API_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('news', []):
                all_results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'date': item.get('date', ''),
                    'source': item.get('source', ''),
                })
        except Exception as e:
            print(f"  [SEARCH ERROR] '{keyword}': {e}")
            continue
    
    # 중복 제거 (제목 기준)
    seen_titles = set()
    unique_results = []
    for r in all_results:
        if r['title'] not in seen_titles:
            seen_titles.add(r['title'])
            unique_results.append(r)
    
    return unique_results[:num_results * 2]  # 최대 10개 반환
