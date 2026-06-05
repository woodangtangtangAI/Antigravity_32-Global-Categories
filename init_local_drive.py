import os
import pandas as pd

base_path = r"G:\내 드라이브\[세계 분석]\04_카테고리_분석"
os.makedirs(base_path, exist_ok=True)

categories = {
    "A-1": ("글로벌_통화정책", "A_금융_시장"),
    "A-2": ("글로벌_신용_부채", "A_금융_시장"),
    "A-3": ("외환_자본흐름", "A_금융_시장"),
    "A-4": ("글로벌_주식시장", "A_금융_시장"),
    "A-5": ("원자재_커모디티", "A_금융_시장"),
    "A-6": ("암호화폐_디지털자산", "A_금융_시장"),
    "B-1": ("반도체_전자부품", "B_산업_섹터"),
    "B-2": ("AI_클라우드_SW", "B_산업_섹터"),
    "B-3": ("에너지_전력_산업", "B_산업_섹터"),
    "B-4": ("금융_은행_보험", "B_산업_섹터"),
    "B-5": ("방산_우주_항공", "B_산업_섹터"),
    "B-6": ("자동차_모빌리티", "B_산업_섹터"),
    "B-7": ("바이오_제약_헬스케어", "B_산업_섹터"),
    "B-8": ("부동산_인프라", "B_산업_섹터"),
    "B-9": ("소비재_리테일", "B_산업_섹터"),
    "B-10": ("물류_공급망_해운", "B_산업_섹터"),
    "C-1": ("양자컴퓨팅", "C_기술_혁신"),
    "C-2": ("로보틱스_자동화", "C_기술_혁신"),
    "C-3": ("바이오테크_유전자", "C_기술_혁신"),
    "C-4": ("우주_위성_기술", "C_기술_혁신"),
    "D-1": ("미중_전략_경쟁", "D_지정학_안보"),
    "D-2": ("유럽_러시아_나토", "D_지정학_안보"),
    "D-3": ("중동_지정학", "D_지정학_안보"),
    "D-4": ("글로벌_사우스", "D_지정학_안보"),
    "E-1": ("AI_규제_거버넌스", "E_정책_규제"),
    "E-2": ("무역_산업_정책", "E_정책_규제"),
    "E-3": ("금융_규제_감독", "E_정책_규제"),
    "E-4": ("데이터_사이버보안", "E_정책_규제"),
    "F-1": ("인구_노동_이민", "F_사회_구조"),
    "F-2": ("불평등_정치양극화", "F_사회_구조"),
    "F-3": ("교육_인적자본", "F_사회_구조"),
    "G-1": ("에너지전환_탈탄소", "G_에너지_자원"),
    "G-2": ("핵심광물_자원안보", "G_에너지_자원"),
    "G-3": ("기후리스크_자연재해", "G_에너지_자원"),
}

for cat_id, (cat_name, group) in categories.items():
    group_path = os.path.join(base_path, group)
    cat_folder_name = f"{cat_id}_{cat_name}"
    cat_path = os.path.join(group_path, cat_folder_name)
    os.makedirs(cat_path, exist_ok=True)
    
    csv_path = os.path.join(cat_path, f"{cat_id}_DB.csv")
    if not os.path.exists(csv_path):
        df = pd.DataFrame(columns=['Date', 'Indicator', 'Value', 'Unit', 'Frequency'])
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    md_path = os.path.join(cat_path, f"{cat_id}_누적_리포트.md")
    if not os.path.exists(md_path):
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# [{cat_id}] {cat_name} 누적 리포트\n\n이 파일에 매주 리포트가 누적됩니다.\n")

print("Local structure created successfully.")
