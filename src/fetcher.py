# -*- coding: utf-8 -*-
"""정량 데이터 수집 및 프롬프트 요약 모듈 (FRED + yfinance)

초기 실행 시 3년치 히스토리를 로드하고, 이후 매주 최신 데이터를 누적합니다.
Gemini 프롬프트 입력 시에는 수천 행의 원시 데이터 대신 지표별 최신값·전회비 증감률·최근 추이를
정밀 계산한 컴팩트 요약본을 전달하여 토큰 폭주와 날짜 오독을 방지합니다.
"""
import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from datetime import datetime, timedelta

HISTORY_YEARS = 3          # FRED: 최근 3년치
YF_HISTORY_PERIOD = "2y"   # yfinance: 최근 2년치 주봉


def get_fred_client():
    api_key = os.environ.get('FRED_API_KEY')
    if not api_key:
        print("[WARNING] FRED_API_KEY not set. Skipping FRED data.")
        return None
    return Fred(api_key=api_key)


def get_fred_safe(fred_client, series_id, name, category, unit, freq):
    """FRED에서 최근 3년치 데이터를 수집합니다."""
    if fred_client is None:
        return pd.DataFrame()
    try:
        start_date = (datetime.now() - timedelta(days=365 * HISTORY_YEARS)).strftime('%Y-%m-%d')
        data = fred_client.get_series(series_id, observation_start=start_date)
        if data is not None and not data.empty:
            df = pd.DataFrame({'Date': data.index, 'Value': data.values})
            df = df.dropna(subset=['Value'])
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce').round(4)
            df = df.dropna(subset=['Value'])
            df['Indicator'] = name
            df['Category'] = category
            df['Unit'] = unit
            df['Frequency'] = freq
            df['Source'] = 'FRED'
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            return df
    except Exception as e:
        print(f"  [FRED ERROR] {series_id}: {e}")
    return pd.DataFrame()


def get_yf_safe(ticker, name, category, unit, freq):
    """Yahoo Finance에서 최근 2년치 주봉 데이터를 수집합니다."""
    try:
        data = yf.download(
            ticker,
            period=YF_HISTORY_PERIOD,
            interval="1wk",
            auto_adjust=True,
            progress=False,
        )
        if data is not None and not data.empty:
            close_data = data['Close']
            if isinstance(close_data, pd.DataFrame):
                close_data = close_data.iloc[:, 0]
            close_series = pd.to_numeric(close_data, errors='coerce').round(4)
            df = pd.DataFrame({
                'Date': pd.to_datetime(data.index).strftime('%Y-%m-%d'),
                'Value': close_series.values,
                'Indicator': name,
                'Category': category,
                'Unit': unit,
                'Frequency': freq,
                'Source': 'Y-Finance',
            })
            df = df.dropna(subset=['Value'])
            return df
    except Exception as e:
        print(f"  [YF ERROR] {ticker}: {e}")
    return pd.DataFrame()


def fetch_quantitative(category_config: dict) -> pd.DataFrame:
    """카테고리 1개의 정량 지표를 FRED + yfinance에서 수집합니다."""
    results = []
    fred_client = get_fred_client()

    for ind_name, info in category_config["quantitative"].get("FRED", {}).items():
        results.append(get_fred_safe(fred_client, info[0], ind_name, info[1], info[2], info[3]))

    for ind_name, info in category_config["quantitative"].get("YFINANCE", {}).items():
        results.append(get_yf_safe(info[0], ind_name, info[1], info[2], info[3]))

    valid = [d for d in results if not d.empty]
    if valid:
        return pd.concat(valid, ignore_index=True)
    return pd.DataFrame()


def summarize_quantitative(df: pd.DataFrame) -> str:
    """수집된 시계열 DataFrame에서 지표별 최신값, 직전치 대비 변화율, 최근 4회 추이를 요약합니다."""
    if df is None or df.empty:
        return ""

    lines = []
    for ind_name, grp in df.groupby('Indicator', sort=False):
        g = grp.sort_values('Date').reset_index(drop=True)
        if g.empty:
            continue
        unit = g['Unit'].iloc[-1]
        freq = g['Frequency'].iloc[-1]
        src = g['Source'].iloc[-1]
        latest_dt = g['Date'].iloc[-1]
        latest_val = float(g['Value'].iloc[-1])

        if len(g) >= 2:
            prev_dt = g['Date'].iloc[-2]
            prev_val = float(g['Value'].iloc[-2])
            diff = latest_val - prev_val
            if prev_val != 0:
                pct = (diff / abs(prev_val)) * 100.0
                arrow = "↑" if pct > 0.05 else ("↓" if pct < -0.05 else "→")
                chg_str = f"직전({prev_dt}: {prev_val:,.4g}) 대비 {diff:+,.4g} ({pct:+.2f}% {arrow})"
            else:
                chg_str = f"직전({prev_dt}: {prev_val:,.4g}) 대비 {diff:+,.4g}"
        else:
            chg_str = "직전 비교 데이터 없음"

        recent_tail = g.tail(4)
        tail_str = " → ".join(
            f"{row['Date']}: {float(row['Value']):,.4g}" for _, row in recent_tail.iterrows()
        )
        lines.append(
            f"- **{ind_name}** [{unit}, {freq}, {src}]: 최신 {latest_val:,.4g} ({latest_dt}) | {chg_str} | 최근 추이: [{tail_str}]"
        )

    return "\n".join(lines)
