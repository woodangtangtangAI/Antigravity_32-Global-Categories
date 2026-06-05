# Antigravity_32-Global-Categories

구글 안티그래비티로 32개 분야 글로벌 데이터 축적 (구글 드라이브)

## 개요

매주 월~금, GitHub Actions가 자동으로 32개 글로벌 분석 카테고리의 정량 데이터를 수집하고 Gemini 1.5 Pro를 활용하여 정성 분석 리포트를 생성합니다. 결과물은 Google Drive `[세계 분석]` 폴더에 자동 저장됩니다.

## 카테고리 구조

| 요일 | 그룹 | 카테고리 수 |
|------|------|----------|
| 월요일 | A. 금융·시장 | 6개 |
| 화요일 | B. 산업·인프라 | 7개 |
| 수요일 | B. 성장·혁신 + C. 기술 | 8개 |
| 목요일 | D. 지정학 + E. 규제 | 8개 |
| 금요일 | F. 사회 + G. 에너지 | 5개 |

## 필요 환경변수 (GitHub Secrets)

| 변수명 | 설명 |
|--------|------|
| `FRED_API_KEY` | FRED API 키 |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | Google Drive 서비스 어카운트 JSON |
| `GEMINI_API_KEY` | Google AI Studio API 키 |
| `SERPER_API_KEY` | Serper.dev 웹 검색 API 키 |
| `GDRIVE_PARENT_FOLDER_ID` | [세계 분석] 폴더 ID |

## 수동 실행

```bash
# 월요일 카테고리 실행
python src/main.py monday

# 드라이런 (API 호출 없이 흐름 확인)
python src/main.py monday --dry-run
```

## 기술 스택

- **정량 수집**: FRED API + Yahoo Finance (yfinance)
- **뉴스 검색**: Serper.dev API
- **정성 분석**: Google Gemini 1.5 Pro API
- **저장소**: Google Drive API
- **자동화**: GitHub Actions (cron)
