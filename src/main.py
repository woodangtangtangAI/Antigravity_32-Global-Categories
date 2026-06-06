# -*- coding: utf-8 -*-
"""32개 글로벌 분석 카테고리 — 주간 자동화 실행 진입점

Usage:
    python src/main.py monday          # 월요일 카테고리 실행
    python src/main.py wednesday        # 수요일 카테고리 실행
    python src/main.py monday --dry-run # API 호출 없이 흐름만 확인
"""
import os
import sys
import json
import time
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 루트를 Python Path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CATEGORIES, SCHEDULE, COOLDOWN_SECONDS, MAX_RETRIES, TOP_NEWS_LIMIT
from src.fetcher import fetch_quantitative
from src.searcher import search_news
from src.analyzer import generate_analysis, load_prompt
from src.uploader import (
    get_drive_service, ensure_category_folder,
    upload_or_update_csv, append_text_to_file, get_previous_report
)

# Google Drive [세계 분석] 폴더 ID (실제 확인된 ID 고정)
GDRIVE_PARENT_FOLDER_ID = '1d7NsdNtejQ5zxaZRQPGBZGdWiDCQes0J'
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts')


def load_checkpoint(day: str) -> set:
    """체크포인트 파일에서 완료된 카테고리 목록을 로드합니다."""
    checkpoint_file = f"checkpoint_{day}.json"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            return set(json.load(f))
    return set()


def save_checkpoint(day: str, completed: set):
    """체크포인트 파일에 완료된 카테고리를 저장합니다."""
    checkpoint_file = f"checkpoint_{day}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump(list(completed), f)


def clear_checkpoint(day: str):
    """체크포인트 파일을 삭제합니다."""
    checkpoint_file = f"checkpoint_{day}.json"
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)


def run_category(cat_id: str, cat_config: dict, service, dry_run: bool = False):
    """단일 카테고리를 실행합니다."""
    cat_name = cat_config['name']
    cat_name_kr = cat_config['name_kr']
    group = cat_config['group']
    
    print(f"\n{'='*60}")
    print(f"[START] {cat_id}: {cat_name_kr}")
    print(f"{'='*60}")
    
    # 1단계: 정량 데이터 수집
    print("  📊 1단계: 정량 데이터 수집...")
    if dry_run:
        print("  [DRY-RUN] 정량 수집 건너뜀")
        quant_df = None
        quant_summary = "(드라이런 모드)"
    else:
        quant_df = fetch_quantitative(cat_config)
        quant_summary = quant_df.to_string(index=False) if not quant_df.empty else ""
        print(f"  → {len(quant_df)}건 수집 완료" if not quant_df.empty else "  → 정량 데이터 없음")
    
    # 2단계: 웹 뉴스 검색
    print("  📰 2단계: 웹 뉴스 검색...")
    if dry_run:
        print("  [DRY-RUN] 뉴스 검색 건너뜀")
        news = []
    else:
        keywords = cat_config.get('search_keywords', [])
        news = search_news(keywords, num_results=TOP_NEWS_LIMIT)
        print(f"  → {len(news)}건 뉴스 수집")
    
    # 3단계: Gemini Pro 정성 분석
    print("  🤖 3단계: Gemini 1.5 Pro 분석 생성...")
    if dry_run:
        print("  [DRY-RUN] AI 분석 건너뜀")
        report_md = f"# [{cat_id}] {cat_name_kr} — 드라이런 리포트\n\n테스트 모드입니다."
    else:
        # 프롬프트 로드
        prompt = load_prompt(PROMPTS_DIR, cat_config['prompt_file'])
        
        # 이전 리포트 가져오기 (연속성)
        folder_id = ensure_category_folder(service, GDRIVE_PARENT_FOLDER_ID, group, cat_id, cat_name)
        prev_report = get_previous_report(service, folder_id, cat_id, cat_name)
        
        report_md = generate_analysis(
            category_id=cat_id,
            category_name=cat_name_kr,
            quant_summary=quant_summary,
            news_results=news,
            prompt_template=prompt,
            prev_report=prev_report,
        )
        print(f"  → 리포트 생성 완료 ({len(report_md)}자)")
    
    # 4단계: Google Drive 업로드
    print("  ☁️ 4단계: Google Drive 업로드...")
    if dry_run:
        print("  [DRY-RUN] 업로드 건너뜀")
    else:
        folder_id = ensure_category_folder(service, GDRIVE_PARENT_FOLDER_ID, group, cat_id, cat_name)
        
        # CSV 업로드 (정량 데이터가 있는 경우)
        if quant_df is not None and not quant_df.empty:
            csv_name = f"{cat_id}_DB.csv"
            try:
                upload_or_update_csv(service, folder_id, csv_name, quant_df)
            except Exception as e:
                print(f"  [DRIVE SKIP] CSV 업로드 실패 (다음 주에 시도): {e}")
        
        # MD 업로드 (정성 리포트)
        today = datetime.now().strftime("%Y-%m-%d")
        report_name = f"{cat_id}_누적_리포트.md"
        try:
            append_text_to_file(service, folder_id, report_name, report_md, today)
        except Exception as e:
            print(f"  [DRIVE SKIP] MD 업로드 실패 (다음 주에 시도): {e}")
    
    print(f"[DONE] {cat_id}: {cat_name_kr} ✓")


def main():
    """메인 실행 함수."""
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <day_of_week> [--dry-run]")
        print("  day_of_week: monday, tuesday, wednesday, thursday, friday")
        sys.exit(1)
    
    day = sys.argv[1].lower()
    dry_run = '--dry-run' in sys.argv
    
    if day not in SCHEDULE:
        print(f"[ERROR] 알 수 없는 요일: {day}")
        print(f"  가능한 값: {', '.join(SCHEDULE.keys())}")
        sys.exit(1)
    
    categories_today = SCHEDULE[day]
    print(f"\n🚀 [{day.upper()}] 실행 시작 — {len(categories_today)}개 카테고리")
    print(f"   카테고리: {', '.join(categories_today)}")
    if dry_run:
        print("   ⚠️ 드라이런 모드 (API 호출 없음)")
    print()
    
    # Google Drive 서비스 초기화
    service = None
    if not dry_run:
        try:
            service = get_drive_service()
            print("✓ Google Drive 연결 성공")
        except Exception as e:
            print(f"✗ Google Drive 연결 실패: {e}")
            sys.exit(1)
    
    # 체크포인트 로드 (이전 실행에서 중단된 경우 이어받기)
    completed = load_checkpoint(day)
    if completed:
        print(f"📌 체크포인트 발견: {len(completed)}개 이미 완료 — 나머지만 실행")
    
    success_count = 0
    error_count = 0
    
    for cat_id in categories_today:
        if cat_id in completed:
            print(f"\n[SKIP] {cat_id}: 이미 완료됨 (체크포인트)")
            success_count += 1
            continue
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                run_category(cat_id, CATEGORIES[cat_id], service, dry_run)
                completed.add(cat_id)
                save_checkpoint(day, completed)
                success_count += 1
                break
            except Exception as e:
                print(f"  [RETRY {attempt}/{MAX_RETRIES}] {cat_id}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(10)  # 재시도 전 10초 대기
                else:
                    print(f"  [FAILED] {cat_id}: {MAX_RETRIES}회 시도 후 실패")
                    error_count += 1
        
        # Rate Limit 대기 (마지막 카테고리가 아닌 경우)
        if cat_id != categories_today[-1] and not dry_run:
            print(f"  ⏳ Rate Limit 대기 ({COOLDOWN_SECONDS}초)...")
            time.sleep(COOLDOWN_SECONDS)
    
    # 전체 완료 시 체크포인트 삭제
    if error_count == 0:
        clear_checkpoint(day)
    
    # 최종 결과 출력
    print(f"\n{'='*60}")
    print(f"📊 [{day.upper()}] 실행 완료")
    print(f"   ✅ 성공: {success_count}개")
    print(f"   ❌ 실패: {error_count}개")
    print(f"   📁 저장 위치: Google Drive > [세계 분석] > 04_카테고리_분석")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
