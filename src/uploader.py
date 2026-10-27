# -*- coding: utf-8 -*-
"""Google Drive 업로드 및 리포트 무결성 점검 모듈 - OAuth2 + Service Account 자동 전환"""
import os
import io
import re
import json
from datetime import datetime
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


def get_drive_service():
    """OAuth refresh token이 있으면 OAuth 사용, 없으면 Service Account 사용."""
    refresh_token = os.environ.get('GOOGLE_REFRESH_TOKEN')

    if refresh_token:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=os.environ.get('GOOGLE_CLIENT_ID'),
            client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
            token_uri='https://oauth2.googleapis.com/token',
        )
        creds.refresh(Request())
        print("  [AUTH] OAuth2 인증 사용")
        return build('drive', 'v3', credentials=creds)
    else:
        from google.oauth2 import service_account
        key_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
        if not key_json:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY 또는 GOOGLE_REFRESH_TOKEN 환경변수가 필요합니다.")
        info = json.loads(key_json)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=['https://www.googleapis.com/auth/drive']
        )
        print("  [AUTH] Service Account 인증 사용")
        return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    query = (
        f"name='{folder_name}' and '{parent_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    results = service.files().list(q=query, fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id],
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"  [DRIVE] 폴더 생성: {folder_name}")
    return folder.get('id')


def ensure_category_folder(service, parent_folder_id: str, group_name: str, cat_id: str, cat_name: str) -> str:
    root_id = find_or_create_folder(service, '04_카테고리_분석', parent_folder_id)
    group_id = find_or_create_folder(service, group_name, root_id)
    cat_folder_name = f"{cat_id}_{cat_name}"
    return find_or_create_folder(service, cat_folder_name, group_id)


def _get_file_id(service, folder_id: str, file_name: str):
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id)').execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None


def _download_text_file(service, file_id: str) -> str:
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, service.files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return fh.getvalue().decode('utf-8', errors='replace')


def _split_weekly_entries(content: str) -> list:
    """누적 리포트에서 주간 구분선('---' + '## 🗓️') 기준으로 개별 주간 블록을 분리합니다."""
    idx = content.find('## 🗓️')
    if idx == -1:
        return []
    body = content[idx:]
    return re.split(r'\n---\s*\n+(?=## 🗓️)', body)


def _is_valid_entry(entry_text: str) -> bool:
    """에러 경고문이 아닌 정상 주간 리포트인지 판별합니다."""
    if not entry_text or len(entry_text.strip()) < 250:
        return False
    if "[!WARNING]" in entry_text or "Gemini API 호출 중 에러" in entry_text:
        return False
    return True


def has_recent_valid_entry(service, folder_id: str, cat_id: str, max_age_days: int = 4) -> tuple:
    """최근 max_age_days 이내에 정상 생성된 주간 리포트가 있는지 확인합니다.

    Returns:
        (is_recent_and_valid: bool, latest_valid_date_str: str)
    """
    try:
        file_id = _get_file_id(service, folder_id, f"{cat_id}_누적_리포트.md")
        if not file_id:
            return (False, "")
        content = _download_text_file(service, file_id)
        entries = _split_weekly_entries(content)
        if not entries:
            return (False, "")

        # 가장 상단 엔트리부터 검사하여 최신 유효 리포트 날짜 확인
        top_entry = entries[0]
        m = re.search(r'##\s*🗓️\s*(\d{4}-\d{2}-\d{2})', top_entry)
        if not m or not _is_valid_entry(top_entry):
            return (False, m.group(1) if m else "FAIL_STUB")

        entry_date_str = m.group(1)
        entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
        age_days = (datetime.now().date() - entry_date).days
        return (age_days <= max_age_days, entry_date_str)
    except Exception as e:
        print(f"  [WARNING] 최근 리포트 점검 실패 ({cat_id}): {e}")
        return (False, "")


def append_text_to_file(service, folder_id: str, file_name: str, new_content: str, date_str: str):
    """누적 마크다운 파일 맨 위에 최신 리포트를 추가합니다. 없으면 새로 생성합니다."""
    if "[!WARNING]" in new_content or len(new_content.strip()) < 200:
        raise ValueError(f"비정상 리포트 본문 업로드 차단 ({file_name})")

    file_id = _get_file_id(service, folder_id, file_name)
    header = f"## 🗓️ {date_str}\n\n"
    separator = "\n\n---\n\n"

    if file_id:
        existing = _download_text_file(service, file_id)
        lines = existing.split('\n')
        title = lines[0] if lines else "# 누적 리포트"
        rest = '\n'.join(lines[1:]).lstrip('\n')
        final = title + '\n\n' + header + new_content + separator + rest
        media = MediaIoBaseUpload(io.BytesIO(final.encode('utf-8')), mimetype='text/markdown', resumable=True)
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [DRIVE] 리포트 누적 업데이트: {file_name}")
    else:
        title = "# 누적 리포트\n\n"
        final = title + header + new_content
        media = MediaIoBaseUpload(io.BytesIO(final.encode('utf-8')), mimetype='text/markdown', resumable=True)
        meta = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=meta, media_body=media, fields='id').execute()
        print(f"  [DRIVE] 마크다운 신규 생성: {file_name}")


def upload_or_update_csv(service, folder_id: str, file_name: str, new_df: pd.DataFrame):
    """CSV 누적 업데이트(기존 행 최신값 갱신 + 신규 날짜 병합)."""
    if new_df is None or new_df.empty:
        print(f"  [SKIP] {file_name}: 데이터 없음")
        return

    file_id = _get_file_id(service, folder_id, file_name)
    new_df = new_df.copy()
    new_df['Date'] = new_df['Date'].astype(str)

    if file_id:
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, service.files().get_media(fileId=file_id))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        try:
            existing_df = pd.read_csv(fh)
            existing_df['Date'] = existing_df['Date'].astype(str)
        except Exception:
            existing_df = pd.DataFrame(columns=new_df.columns)

        prev_len = len(existing_df)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['Date', 'Indicator'], keep='last')
        combined = combined.sort_values(by=['Date', 'Indicator']).reset_index(drop=True)

        added_rows = len(combined) - prev_len
        if added_rows == 0 and combined.equals(existing_df.sort_values(by=['Date', 'Indicator']).reset_index(drop=True)):
            print(f"  [SKIP] {file_name}: 이미 최신 데이터")
            return

        csv_bytes = combined.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype='text/csv', resumable=True)
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [DRIVE] CSV 누적 업데이트: {file_name} (+{max(0, added_rows)}행, 총 {len(combined)}행)")
    else:
        csv_bytes = new_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype='text/csv', resumable=True)
        meta = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=meta, media_body=media, fields='id').execute()
        print(f"  [DRIVE] CSV 신규 생성: {file_name} ({len(new_df)}행)")


def get_previous_report(service, folder_id: str, cat_id: str, cat_name: str) -> str:
    """누적 리포트에서 에러 스텁([!WARNING])을 건너뛰고 가장 최근의 '정상' 리포트 블록을 반환합니다."""
    try:
        file_id = _get_file_id(service, folder_id, f"{cat_id}_누적_리포트.md")
        if file_id:
            content = _download_text_file(service, file_id)
            for entry in _split_weekly_entries(content):
                if _is_valid_entry(entry):
                    return entry.strip()
    except Exception as e:
        print(f"  [WARNING] 이전 리포트 조회 실패: {e}")
    return ""
