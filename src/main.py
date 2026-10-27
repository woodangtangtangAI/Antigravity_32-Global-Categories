# -*- coding: utf-8 -*-
"""34개 글로벌 분석 카테고리 — 주간 자동화 및 자동 복구(Self-Heal) 실행 진입점

Usage:
    python src/main.py monday            # 월요일 카테고리 실행 (최근 4일 내 정상본 있으면 자동 스킵)
    python src/main.py wednesday         # 수요일 카테고리 실행
    python src/main.py heal              # 전 카테고리(34개) 전수 점검 후 6일 초과 누락/실패 건만 자동 복구
    python src/main.py B-2,D-1 --force   # 특정 카테고리 강제 재실행
    python src/main.py monday --dry-run  # API 호출 없이 흐름만 확인
"""
import os
import sys
import json
import time
import socket
from datetime import datetime

# 소켓 타임아웃 90초 설정 (네트워크 무한 대기 방지)
socket.setdefaulttimeout(90)

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 루트를 Python Path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CATEGORIES, SCHEDULE, COOLDOWN_SECONDS, MAX_RETRIES, TOP_NEWS_LIMIT
from src.fetcher import fetch_quantitative, summarize_quantitative
from src.searcher import search_news
from src.analyzer import generate_analysis, load_prompt
from src.uploader import (
    get_drive_service,
    ensure_category_folder,
    upload_or_update_csv,
    append_text_to_file,
    get_previous_report,
    has_recent_valid_entry,
)

GDRIVE_PARENT_FOLDER_ID = os.environ.get('GDRIVE_PARENT_FOLDER_ID') or '1d7NsdNtejQ5zxaZRQPGBZGdWiDCQes0J'
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'prompts')


def load_checkpoint(mode_key: str) -> set:
    checkpoint_file = f"checkpoint_{mode_key}.json"
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def save_checkpoint(mode_key: str, completed: set):
    checkpoint_file = f"checkpoint_{mode_key}.json"
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(list(completed), f)


def clear_checkpoint(mode_key: str):
    checkpoint_file = f"checkpoint_{mode_key}.json"
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)


def resolve_target_categories(arg: str) -> tuple:
    """실행 인자(요일명, 'heal', 'all', 또는 쉼표 구분 카테고리 ID)를 해석합니다.

    Returns:
        (mode_label, category_id_list, skip_max_age_days)
    """
    lowered = arg.lower().strip()
    if lowered in SCHEDULE:
        return (lowered, SCHEDULE[lowered], 4)
    if lowered in ('heal', 'all'):
        return ('heal', list(CATEGORIES.keys()), 6)

    # 쉼표 구분 카테고리 ID 지원 (예: B-2,D-1,E-2)
    raw_ids = [x.strip().upper() for x in arg.split(',') if x.strip()]
    invalid = [x for x in raw_ids if x not in CATEGORIES]
    if invalid:
        raise ValueError(f"알 수 없는 실행 인자 또는 카테고리 ID: {invalid}")
    return ('custom', raw_ids, 4)


def run_category(
    cat_id: str,
    cat_config: dict,
    service,
    dry_run: bool = False,
    force: bool = False,
    skip_max_age_days: int = 4,
) -> bool:
    """단일 카테고리를 실행합니다.

    Returns:
        True: 실제 AI 분석 및 업로드를 수행함 (Cooldown 필요)
        False: 이미 최신 유효 리포트가 존재하여 스킵함 (Cooldown 불필요)
    """
    cat_name = cat_config['name']
    cat_name_kr = cat_config['name_kr']
    group = cat_config['group']

    folder_id = None
    if not dry_run:
        folder_id = ensure_category_folder(service, GDRIVE_PARENT_FOLDER_ID, group, cat_id, cat_name)
        if not force:
            is_fresh, latest_dt = has_recent_valid_entry(
                service, folder_id, cat_id, max_age_days=skip_max_age_days
            )
            if is_fresh:
                print(f"⏭️ [SKIP] {cat_id} ({cat_name_kr}): 최근 유효 리포트({latest_dt}) 확인됨")
                return False

    print(f"\n{'='*60}")
    print(f"[START] {cat_id}: {cat_name_kr}")
    print(f"{'='*60}")

    # 1단계: 정량 데이터 수집 및 핵심 요약
    print("  📊 1단계: 정량 데이터 수집...")
    if dry_run:
        print("  [DRY-RUN] 정량 수집 건너뜀")
        quant_df = None
        quant_summary = "(드라이런 모드)"
    else:
        quant_df = fetch_quantitative(cat_config)
        quant_summary = summarize_quantitative(quant_df)
        print(f"  → {len(quant_df)}행 수집 / 지표 요약 생성 완료" if not quant_df.empty else "  → 정량 지표 없음 (정성 집중)")

    # 2단계: 실시간 뉴스 검색 (Serper -> Google News RSS 자동 폴백)
    print("  📰 2단계: 실시간 웹 뉴스 검색...")
    if dry_run:
        print("  [DRY-RUN] 뉴스 검색 건너뜀")
        news = []
    else:
        keywords = cat_config.get('search_keywords', [])
        news = search_news(keywords, num_results=TOP_NEWS_LIMIT)
        print(f"  → {len(news)}건 최신 뉴스 확보")

    # 3단계: Gemini 멀티모델 폴백 정성 분석
    print("  🤖 3단계: Gemini 멀티모델 분석 생성...")
    if dry_run:
        print("  [DRY-RUN] AI 분석 건너뜀")
        report_md = f"# [{cat_id}] {cat_name_kr} — 드라이런 리포트\n\n테스트 모드입니다."
    else:
        prompt = load_prompt(PROMPTS_DIR, cat_config['prompt_file'])
        prev_report = get_previous_report(service, folder_id, cat_id, cat_name)
        report_md = generate_analysis(
            category_id=cat_id,
            category_name=cat_name_kr,
            quant_summary=quant_summary,
            news_results=news,
            prompt_template=prompt,
            prev_report=prev_report,
        )

    # 4단계: Google Drive 업로드
    print("  ☁️ 4단계: Google Drive 업로드...")
    if dry_run:
        print("  [DRY-RUN] 업로드 건너뜀")
    else:
        if quant_df is not None and not quant_df.empty:
            csv_name = f"{cat_id}_DB.csv"
            try:
                upload_or_update_csv(service, folder_id, csv_name, quant_df)
            except Exception as e:
                print(f"  [DRIVE WARNING] CSV 업로드 지연 (리포트는 계속 진행): {e}")

        today = datetime.now().strftime("%Y-%m-%d")
        report_name = f"{cat_id}_누적_리포트.md"
        append_text_to_file(service, folder_id, report_name, report_md, today)

    print(f"[DONE] {cat_id}: {cat_name_kr} ✓")
    return True


def main():
    cli_args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not cli_args:
        print("Usage: python src/main.py <day_of_week | heal | CAT_IDS> [--force] [--dry-run]")
        sys.exit(1)

    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv or os.environ.get('FORCE_RUN', '').lower() == 'true'

    try:
        mode_key, target_categories, skip_max_age_days = resolve_target_categories(cli_args[0])
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(f"\n🚀 [{mode_key.upper()}] 실행 시작 — 점검 대상 {len(target_categories)}개 카테고리 (force={force})")
    print(f"   대상: {', '.join(target_categories)}")
    if dry_run:
        print("   ⚠️ 드라이런 모드 (API 호출 없음)")
    print()

    service = None
    if not dry_run:
        try:
            service = get_drive_service()
            print("✓ Google Drive 연결 성공\n")
        except Exception as e:
            print(f"✗ Google Drive 연결 실패: {e}")
            sys.exit(1)

    completed = load_checkpoint(mode_key) if not force else set()
    if completed:
        print(f"📌 체크포인트 발견: {len(completed)}개 이미 완료 — 나머지만 점검")

    executed_count = 0
    skipped_count = 0
    error_count = 0
    failed_ids = []

    for idx, cat_id in enumerate(target_categories):
        if cat_id in completed:
            print(f"⏭️ [SKIP] {cat_id}: 체크포인트 완료됨")
            skipped_count += 1
            continue

        did_execute = False
        cat_succeeded = False

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                did_execute = run_category(
                    cat_id,
                    CATEGORIES[cat_id],
                    service,
                    dry_run=dry_run,
                    force=force,
                    skip_max_age_days=skip_max_age_days,
                )
                completed.add(cat_id)
                save_checkpoint(mode_key, completed)
                cat_succeeded = True
                break
            except Exception as e:
                print(f"  [RETRY {attempt}/{MAX_RETRIES}] {cat_id}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(15)
                else:
                    print(f"  ❌ [FAILED] {cat_id}: {MAX_RETRIES}회 시도 후 최종 실패")

        if cat_succeeded:
            if did_execute:
                executed_count += 1
                if idx < len(target_categories) - 1 and not dry_run:
                    print(f"  ⏳ 할당량 보호 대기 ({COOLDOWN_SECONDS}초)...")
                    time.sleep(COOLDOWN_SECONDS)
            else:
                skipped_count += 1
        else:
            error_count += 1
            failed_ids.append(cat_id)

    if error_count == 0:
        clear_checkpoint(mode_key)

    print(f"\n{'='*60}")
    print(f"📊 [{mode_key.upper()}] 실행 요약")
    print(f"   ✅ 신규 생성/복구: {executed_count}개")
    print(f"   ⏭️ 최신 상태(스킵): {skipped_count}개")
    print(f"   ❌ 실패: {error_count}개" + (f" ({', '.join(failed_ids)})" if failed_ids else ""))
    print(f"   📁 저장 위치: Google Drive > [세계 분석] > 04_카테고리_분석")
    print(f"{'='*60}")

    if error_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
