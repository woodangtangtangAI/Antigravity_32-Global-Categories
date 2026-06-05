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


def find_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    """Google Drive에서 폴더를 찾거나 없으면 새로 생성합니다.
    
    Returns:
        폴더 ID
    """
    # 기존 폴더 검색
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    
    # 새 폴더 생성
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"  [DRIVE] 폴더 생성: {folder_name}")
    return folder.get('id')


def ensure_category_folder(service, parent_folder_id: str, group_name: str, cat_id: str, cat_name: str) -> str:
    """카테고리 폴더 경로를 보장합니다.
    
    예: 04_카테고리_분석/A_금융_시장/A-1_글로벌_통화정책/
    """
    # 1. 04_카테고리_분석 폴더
    root_id = find_or_create_folder(service, '04_카테고리_분석', parent_folder_id)
    
    # 2. 그룹 폴더 (예: A_금융_시장)
    group_id = find_or_create_folder(service, group_name, root_id)
    
    # 3. 카테고리 폴더 (예: A-1_글로벌_통화정책)
    cat_folder_name = f"{cat_id}_{cat_name}"
    cat_id_folder = find_or_create_folder(service, cat_folder_name, group_id)
    
    return cat_id_folder


def upload_text_file(service, folder_id: str, file_name: str, content: str, mime_type: str = 'text/markdown'):
    """텍스트 파일을 Google Drive에 업로드합니다 (항상 새 파일 생성)."""
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaIoBaseUpload(
        io.BytesIO(content.encode('utf-8')),
        mimetype=mime_type,
        resumable=True
    )
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()
    
    print(f"  [DRIVE] 파일 업로드: {file_name}")
    return file.get('id')


def upload_or_update_csv(service, folder_id: str, file_name: str, new_df: pd.DataFrame):
    """CSV 파일을 업로드하거나, 기존 파일이 있으면 행을 추가합니다.
    
    기존 macro_from202605.py의 process_file() 패턴을 재활용합니다.
    """
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
        existing_df = pd.read_csv(fh)
        
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
        print(f"  [DRIVE] CSV 업데이트: {file_name} (+{len(filtered_rows)}행)")
    
    else:
        # 새 파일 생성
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        csv_bytes = new_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        media = MediaIoBaseUpload(io.BytesIO(csv_bytes), mimetype='text/csv', resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"  [DRIVE] CSV 신규 생성: {file_name} ({len(new_df)}행)")


def get_previous_report(service, folder_id: str, cat_id: str, cat_name: str) -> str:
    """지난주 리포트를 Google Drive에서 다운로드합니다."""
    try:
        query = f"name contains '[{cat_id}_{cat_name}] 주간 리포트' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query, 
            fields='files(id, name)',
            orderBy='name desc',  # 날짜순 역순
            pageSize=1
        ).execute()
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
            return fh.read().decode('utf-8')
    except Exception as e:
        print(f"  [WARNING] 이전 리포트 조회 실패: {e}")
    
    return ""
