# -*- coding: utf-8 -*-
"""
[1회 실행] 구글 드라이브 OAuth 인증 설정 스크립트
실행하면 브라우저가 열리며 구글 로그인 후 refresh_token이 출력됩니다.
출력된 값을 GitHub Secret에 GOOGLE_REFRESH_TOKEN으로 등록하세요.
"""
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

# ───────────────────────────────────────────────
# 아래 client_id, client_secret은 구글에서 발급받은 OAuth 앱 자격증명입니다.
# GCP Console > API 및 서비스 > 사용자 인증 정보 > OAuth 2.0 클라이언트 ID
# 아래는 공개용 데스크탑 앱 자격증명 (이 값을 그대로 사용하셔도 됩니다)
# ───────────────────────────────────────────────
CLIENT_CONFIG = {
    "installed": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    print("=" * 60)
    print("구글 드라이브 OAuth 토큰 발급")
    print("=" * 60)
    
    # OAuth 앱 자격증명 파일 확인
    cred_file = "oauth_client_secret.json"
    if os.path.exists(cred_file):
        flow = InstalledAppFlow.from_client_secrets_file(cred_file, SCOPES)
    else:
        print("\n[오류] oauth_client_secret.json 파일이 필요합니다.")
        print("\n방법:")
        print("1. https://console.cloud.google.com 접속")
        print("2. API 및 서비스 > 사용자 인증 정보")
        print("3. OAuth 2.0 클라이언트 ID > 데스크톱 앱 > 다운로드")
        print("4. 파일명을 oauth_client_secret.json으로 저장 후 재실행")
        return
    
    print("\n브라우저가 열립니다. 마스터님의 구글 계정으로 로그인하세요.")
    creds = flow.run_local_server(port=0)
    
    print("\n" + "=" * 60)
    print("✅ 인증 성공! 아래 값을 GitHub Secret에 등록하세요:")
    print("=" * 60)
    print(f"\n[Secret 이름]: GOOGLE_REFRESH_TOKEN")
    print(f"[Secret 값]:\n{creds.refresh_token}")
    print("\n[Secret 이름]: GOOGLE_CLIENT_ID")
    print(f"[Secret 값]:\n{creds.client_id}")
    print("\n[Secret 이름]: GOOGLE_CLIENT_SECRET")
    print(f"[Secret 값]:\n{creds.client_secret}")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
