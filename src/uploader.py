# -*- coding: utf-8 -*-
"""Google Drive 업로드 모듈"""
import os
import io
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


def get_drive_service():
    key_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not key_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY 환경변수가 설정되지 않았습니다.")
    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    """폴더를 찾거나 없으면 생성합니다."""
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    items = results.get('files', [])
    if items:
        return items[0]['id']
    # 없으면 생성
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"  [DRIVE] 폴더 생성: {folder_name}")
    return folder.get('id')


def ensure_category_folder(service, parent_folder_id: str, group_name: str, cat_id: str, cat_name: str) -> str:
    root_id = find_or_create_folder(service, '04_카테고리_분석', parent_folder_id)
    group_id = find_or_create_folder(service, group_name, root_id)
    cat_folder_name = f"{cat_id}_{cat_name}"
    cat_id_folder = find_or_create_folder(service, cat_folder_name, group_id)
    return cat_id_folder


def _get_file_id(service, folder_id: str, file_name: str):
    """폴더 내 파일 ID를 찾습니다. 없으면 None."""
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id)').execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None


def append_text_to_file(service, folder_id: str, file_name: str, new_content: str, date_str: str):
    """누적 마크다운 파일에 최신 리포트를 맨 위에 추가합니다. 없으면 새로 만듭니다."""
    file_id = _get_file_id(service, folder_id, file_name)

    header = f"## 🗓️ {date_str}\n\n"
    separator = "\n\n---\n\n"

    if file_id:
        # 기존 파일 다운로드
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, service.files().get_media(fileId=file_id))
        done = False
        while not done:
            _, done = downloader.next_chunk()
        existing = fh.getvalue().decode('utf-8')

        # 제목 줄 분리 후 새 내용을 맨 위에 삽입
        lines = existing.split('\n')
        title = lines[0] if lines else f"# {file_name}"
        rest = '\n'.join(lines[1:]).lstrip('\n')
        final = title + '\n\n' + header + new_content + separator + rest
    else:
        # 파일이 없으면 새로 생성
        title = f"# 누적 리포트 — {file_name.replace('.md', '')}"
        final = title + '\n\n' + header + new_content
        print(f"  [DRIVE] 마크다운 파일 신규 생성: {file_name}")

    media = MediaIoBaseUpload(io.BytesIO(final.encode('utf-8')), mimetype='text/markdown', resumable=True)
    if file_id:
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [DRIVE] 리포트 누적 업데이트: {file_name}")
    else:
        meta = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=meta, media_body=media, fields='id').execute()


def upload_or_update_csv(service, folder_id: str, file_name: str, new_df: pd.DataFrame):
    """CSV를 누적 업데이트합니다. 없으면 새로 만듭니다."""
    if new_df.empty:
        print(f"  [SKIP] {file_name}: 수집된 데이터 없음")
        return

    file_id = _get_file_id(service, folder_id, file_name)
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

        filtered = []
        for _, row in new_df.iterrows():
            is_dup = ((existing_df['Date'] == row['Date']) &
                      (existing_df['Indicator'] == row['Indicator'])).any()
            if not is_dup:
                filtered.append(row)

        if not filtered:
            print(f"  [SKIP] {file_name}: 이번 주 데이터 이미 존재")
            return

        final_df = pd.concat([existing_df, pd.DataFrame(filtered)], ignore_index=True)
        final_df = final_df.sort_values(by=['Date', 'Indicator'])
        csv_bytes = final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype='text/csv', resumable=True)
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [DRIVE] CSV 누적 업데이트: {file_name} (+{len(filtered)}행)")
    else:
        # 없으면 새로 생성
        csv_bytes = new_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype='text/csv', resumable=True)
        meta = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=meta, media_body=media, fields='id').execute()
        print(f"  [DRIVE] CSV 신규 생성: {file_name} ({len(new_df)}행)")


def get_previous_report(service, folder_id: str, cat_id: str, cat_name: str) -> str:
    """누적 리포트에서 가장 최신 리포트를 가져옵니다."""
    try:
        file_name = f"{cat_id}_누적_리포트.md"
        file_id = _get_file_id(service, folder_id, file_name)
        if file_id:
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, service.files().get_media(fileId=file_id))
            done = False
            while not done:
                _, done = downloader.next_chunk()
            content = fh.getvalue().decode('utf-8')
            parts = content.split('---')
            return parts[0].strip() if len(parts) > 1 else content.strip()
    except Exception as e:
        print(f"  [WARNING] 이전 리포트 조회 실패: {e}")
    return ""
