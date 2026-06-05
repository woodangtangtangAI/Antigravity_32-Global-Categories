# -*- coding: utf-8 -*-
"""Google Drive 업로드 모듈

기존 [세계 분석] macro_from202605.py의 인증/업로드 로직을 재활용합니다.
환경변수 GOOGLE_SERVICE_ACCOUNT_KEY에서 서비스 어카운트 JSON을 읽습니다.
"""
import os
import io
import json
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload


def get_drive_service():
    """Google Drive API 서비스 객체를 생성합니다."""
    key_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not key_json:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY 환경변수가 설정되지 않았습니다.")
    
    info = json.loads(key_json)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)


def find_folder(service, folder_name: str, parent_id: str) -> str:
    """Google Drive에서 폴더를 찾습니다 (생성하지 않음)."""
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    raise Exception(f"폴더를 찾을 수 없습니다: {folder_name} (미리 동기화되어 있어야 합니다.)")


def ensure_category_folder(service, parent_folder_id: str, group_name: str, cat_id: str, cat_name: str) -> str:
    """카테고리 폴더 경로를 찾습니다."""
    # 1. 04_카테고리_분석 폴더
    root_id = find_folder(service, '04_카테고리_분석', parent_folder_id)
    
    # 2. 그룹 폴더 (예: A_금융_시장)
    group_id = find_folder(service, group_name, root_id)
    
    # 3. 카테고리 폴더 (예: A-1_글로벌_통화정책)
    cat_folder_name = f"{cat_id}_{cat_name}"
    cat_id_folder = find_folder(service, cat_folder_name, group_id)
    
    return cat_id_folder


def append_text_to_file(service, folder_id: str, file_name: str, new_content: str, date_str: str):
    """기존 마크다운 파일 상단에 새 리포트를 누적 업데이트합니다."""
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        file_id = items[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        existing_content = fh.getvalue().decode('utf-8')
        
        # 새 리포트를 맨 위 (제목 아래)에 추가
        lines = existing_content.split('\n')
        title_line = lines[0] if lines else f"# {file_name.replace('.md', '')}"
        rest_content = '\n'.join(lines[1:])
        
        header_separator = f"\n\n## 🗓️ 업데이트 날짜: {date_str}\n\n"
        final_content = title_line + header_separator + new_content + "\n\n---\n" + rest_content
        
        media = MediaIoBaseUpload(
            io.BytesIO(final_content.encode('utf-8')),
            mimetype='text/markdown',
            resumable=True
        )
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [DRIVE] 리포트 누적 업데이트 완료: {file_name}")
    else:
        print(f"  [ERROR] 누적할 마크다운 파일이 없습니다: {file_name} (미리 생성되어 있어야 합니다.)")


def upload_or_update_csv(service, folder_id: str, file_name: str, new_df: pd.DataFrame):
    """CSV 파일에 새로운 행을 추가 업데이트합니다 (생성하지 않음)."""
    if new_df.empty:
        print(f"  [SKIP] {file_name}: 수집된 데이터 없음")
        return
    
    # 기존 파일 검색
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id)').execute()
    items = results.get('files', [])
    
    if items:
        # 기존 파일 다운로드
        file_id = items[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        fh.seek(0)
        try:
            existing_df = pd.read_csv(fh)
        except:
            existing_df = pd.DataFrame(columns=['Date', 'Indicator', 'Value', 'Unit', 'Frequency'])
            
        # 중복 체크 (같은 날짜 + 같은 지표명이면 건너뜀)
        existing_df['Date'] = existing_df['Date'].astype(str)
        new_df['Date'] = new_df['Date'].astype(str)
        
        filtered_rows = []
        for _, row in new_df.iterrows():
            is_dup = ((existing_df['Date'] == row['Date']) & 
                      (existing_df['Indicator'] == row['Indicator'])).any()
            if not is_dup:
                filtered_rows.append(row)
        
        if not filtered_rows:
            print(f"  [SKIP] {file_name}: 이번 주 데이터 이미 존재")
            return
        
        new_rows_df = pd.DataFrame(filtered_rows)
        final_df = pd.concat([existing_df, new_rows_df], ignore_index=True)
        final_df = final_df.sort_values(by=['Date', 'Indicator'])
        
        # 기존 파일 업데이트
        csv_bytes = final_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype='text/csv', resumable=True)
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [DRIVE] CSV 누적 업데이트 완료: {file_name} (+{len(filtered_rows)}행)")
    else:
        print(f"  [ERROR] 누적할 CSV 파일이 없습니다: {file_name} (미리 생성되어 있어야 합니다.)")


def get_previous_report(service, folder_id: str, cat_id: str, cat_name: str) -> str:
    """누적 리포트에서 지난주(가장 상단) 리포트 내용을 추출합니다."""
    try:
        file_name = f"{cat_id}_누적_리포트.md"
        query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields='files(id)').execute()
        items = results.get('files', [])
        
        if items:
            file_id = items[0]['id']
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            content = fh.read().decode('utf-8')
            
            # --- 로 분리된 섹션 중 첫 번째(최신) 리포트만 반환
            parts = content.split('---')
            if len(parts) > 1:
                return parts[0].strip()
            return content.strip()
    except Exception as e:
        print(f"  [WARNING] 이전 리포트 조회 실패: {e}")
    
    return ""
