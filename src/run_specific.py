# -*- coding: utf-8 -*-
"""실패했던 특정 카테고리만 수동 재실행하는 스크립트"""
import os
import sys
import time

# 프로젝트 루트를 Python Path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CATEGORIES
from src.main import run_category
from src.uploader import get_drive_service

# 누락된 1개 카테고리 지정
missing_categories = ['E-1']

def main():
    service = get_drive_service()
    print(f"Starting execution of {len(missing_categories)} missing categories...")
    
    for idx, cat_id in enumerate(missing_categories):
        print(f"\n[{idx+1}/{len(missing_categories)}] Running {cat_id}...")
        try:
            run_category(cat_id, CATEGORIES[cat_id], service, dry_run=False)
        except Exception as e:
            print(f"Error running {cat_id}: {e}")
            
        if cat_id != missing_categories[-1]:
            print("Waiting 35 seconds cooldown...")
            time.sleep(35)
            
    print("Completed all missing categories!")

if __name__ == '__main__':
    main()
