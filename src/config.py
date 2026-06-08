# -*- coding: utf-8 -*-
"""34개 글로벌 분석 카테고리 정의 및 주간 스케줄

각 카테고리는 다음 구조를 따름:
- name: 영문 식별자
- name_kr: 한국어 표시명
- group: 소속 그룹 (A~G)
- prompt_file: 프롬프트 템플릿 파일명
- quantitative: 정량 데이터 소스 (FRED / YFINANCE)
    - FRED: {지표명: [시리즈ID, 분류, 단위, 주기]}
    - YFINANCE: {지표명: [티커심볼, 분류_kr, 단위, 주기]}
- search_keywords: 뉴스 검색용 키워드 리스트
"""

# ─────────────────────────────────────────────
# 34개 글로벌 분석 카테고리 정의
# ─────────────────────────────────────────────

CATEGORIES = {

    # ═══════════════════════════════════════════
    # A. 금융·시장  (group: A_금융_시장)
    # ═══════════════════════════════════════════

    "A-1": {
        "name": "글로벌_통화정책",
        "name_kr": "글로벌 통화정책·중앙은행",
        "group": "A_금융_시장",
        "prompt_file": "finance_prompt.txt",
        "quantitative": {
            "FRED": {
                "미국_기준금리": ["FEDFUNDS", "금리", "%", "Monthly"],
                "유럽_기준금리": ["ECBDFR", "금리", "%", "Monthly"],
                "일본_콜금리": ["IRSTCI01JPM156N", "금리", "%", "Monthly"],
                "미국_실질금리_10Y": ["DFII10", "금리", "%", "Monthly"],
            },
            "YFINANCE": {},
        },
        "search_keywords": [
            "central bank policy rate decision 2026",
            "FOMC minutes",
            "ECB rate decision",
            "BOJ monetary policy",
        ],
    },

    "A-2": {
        "name": "글로벌_신용_부채",
        "name_kr": "글로벌 신용·부채 사이클",
        "group": "A_금융_시장",
        "prompt_file": "finance_prompt.txt",
        "quantitative": {
            "FRED": {
                "하이일드_OAS": ["BAMLH0A0HYM2", "신용", "bp", "Daily"],
                "IG_스프레드": ["BAMLC0A4CBBB", "신용", "bp", "Daily"],
                "장단기스프레드_10Y2Y": ["T10Y2Y", "금리", "%", "Daily"],
            },
            "YFINANCE": {},
        },
        "search_keywords": [
            "credit spread high yield 2026",
            "corporate default rate",
            "US fiscal deficit debt",
            "China local government debt",
        ],
    },

    "A-3": {
        "name": "외환_자본흐름",
        "name_kr": "외환·국제자본흐름",
        "group": "A_금융_시장",
        "prompt_file": "finance_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "달러인덱스": ["DX-Y.NYB", "환율", "Pt", "Weekly"],
                "USD_CNY": ["CNY=X", "환율", "CNY", "Weekly"],
                "USD_JPY": ["JPY=X", "환율", "JPY", "Weekly"],
                "USD_KRW": ["KRW=X", "환율", "KRW", "Weekly"],
                "USD_EUR": ["EUR=X", "환율", "EUR", "Weekly"],
            },
        },
        "search_keywords": [
            "dollar index DXY 2026",
            "de-dollarization yuan",
            "capital flows emerging markets",
            "carry trade unwind",
        ],
    },

    "A-4": {
        "name": "글로벌_주식시장",
        "name_kr": "글로벌 주식시장·밸류에이션",
        "group": "A_금융_시장",
        "prompt_file": "finance_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "S&P500": ["^GSPC", "증시", "Pt", "Weekly"],
                "나스닥": ["^IXIC", "증시", "Pt", "Weekly"],
                "코스피": ["^KS11", "증시", "Pt", "Weekly"],
                "유로스톡스50": ["^STOXX50E", "증시", "Pt", "Weekly"],
                "닛케이225": ["^N225", "증시", "Pt", "Weekly"],
                "상하이종합": ["000001.SS", "증시", "Pt", "Weekly"],
            },
        },
        "search_keywords": [
            "global equity market valuation PE 2026",
            "fund flows ETF",
            "stock market outlook",
            "market sentiment VIX",
        ],
    },

    "A-5": {
        "name": "원자재_커모디티",
        "name_kr": "원자재·커모디티 시장",
        "group": "A_금융_시장",
        "prompt_file": "finance_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "금_선물": ["GC=F", "원자재", "USD", "Weekly"],
                "은_선물": ["SI=F", "원자재", "USD", "Weekly"],
                "구리_선물": ["HG=F", "원자재", "USD", "Weekly"],
                "WTI": ["CL=F", "에너지", "USD", "Weekly"],
                "브렌트유": ["BZ=F", "에너지", "USD", "Weekly"],
                "천연가스": ["NG=F", "에너지", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "commodity market outlook 2026",
            "OPEC production cut",
            "copper demand supply",
            "gold price forecast",
        ],
    },

    "A-6": {
        "name": "암호화폐_디지털자산",
        "name_kr": "암호화폐·디지털자산",
        "group": "A_금융_시장",
        "prompt_file": "finance_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "비트코인": ["BTC-USD", "암호화폐", "USD", "Weekly"],
                "이더리움": ["ETH-USD", "암호화폐", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "bitcoin ETF flows 2026",
            "crypto regulation SEC",
            "CBDC digital currency",
            "stablecoin market cap",
        ],
    },

    # ═══════════════════════════════════════════
    # B. 산업·섹터  (group: B_산업_섹터)
    # ═══════════════════════════════════════════

    "B-1": {
        "name": "반도체_전자부품",
        "name_kr": "반도체·전자부품",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "필라델피아반도체": ["^SOX", "반도체", "Pt", "Weekly"],
                "TSMC": ["TSM", "반도체", "USD", "Weekly"],
                "NVIDIA": ["NVDA", "반도체", "USD", "Weekly"],
                "ASML": ["ASML", "반도체", "USD", "Weekly"],
                "SK하이닉스": ["000660.KS", "반도체", "KRW", "Weekly"],
            },
        },
        "search_keywords": [
            "semiconductor market sales 2026",
            "TSMC foundry utilization",
            "HBM memory demand",
            "chip export control China",
        ],
    },

    "B-2": {
        "name": "AI_클라우드_SW",
        "name_kr": "AI·클라우드·소프트웨어",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "MSFT": ["MSFT", "빅테크", "USD", "Weekly"],
                "GOOG": ["GOOG", "빅테크", "USD", "Weekly"],
                "AMZN": ["AMZN", "빅테크", "USD", "Weekly"],
                "AI_ETF": ["BOTZ", "AI", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "AI infrastructure capex 2026",
            "cloud revenue growth AWS Azure GCP",
            "foundation model benchmark",
            "GPU supply shortage",
        ],
    },

    "B-3": {
        "name": "에너지_전력_산업",
        "name_kr": "에너지·전력 산업",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "유틸리티ETF": ["XLU", "전력", "USD", "Weekly"],
                "넥스트에라에너지": ["NEE", "전력", "USD", "Weekly"],
                "우라늄ETF": ["URA", "원자력", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "data center power demand 2026",
            "nuclear energy revival",
            "renewable energy capacity",
            "electricity grid bottleneck",
        ],
    },

    "B-4": {
        "name": "금융_은행_보험",
        "name_kr": "금융·은행·보험",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {
                "미국_은행예금": ["DPSACBW027SBOG", "은행", "십억USD", "Weekly"],
                "미국_대출잔고": ["TOTLL", "은행", "십억USD", "Weekly"],
            },
            "YFINANCE": {
                "금융ETF": ["XLF", "금융", "USD", "Weekly"],
                "JP모건": ["JPM", "은행", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "bank earnings 2026",
            "commercial real estate loan delinquency",
            "fintech funding",
            "bank deposit outflow",
        ],
    },

    "B-5": {
        "name": "방산_우주_항공",
        "name_kr": "방산·우주·항공",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "방산ETF": ["ITA", "방산", "USD", "Weekly"],
                "록히드마틴": ["LMT", "방산", "USD", "Weekly"],
                "보잉": ["BA", "항공", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "defense spending NATO 2026",
            "arms export contract",
            "satellite launch SpaceX",
            "Korea defense export",
        ],
    },

    "B-6": {
        "name": "자동차_모빌리티",
        "name_kr": "자동차·모빌리티",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "테슬라": ["TSLA", "EV", "USD", "Weekly"],
                "도요타": ["TM", "자동차", "USD", "Weekly"],
                "현대차": ["005380.KS", "자동차", "KRW", "Weekly"],
                "자동차ETF": ["CARZ", "자동차", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "EV sales penetration rate 2026",
            "battery price kWh",
            "autonomous driving regulation",
            "China EV export tariff",
        ],
    },

    "B-7": {
        "name": "바이오_제약_헬스케어",
        "name_kr": "바이오·제약·헬스케어",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "바이오ETF": ["IBB", "바이오", "USD", "Weekly"],
                "헬스케어ETF": ["XLV", "헬스케어", "USD", "Weekly"],
                "일라이릴리": ["LLY", "제약", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "FDA drug approval 2026",
            "GLP-1 obesity drug sales",
            "biotech IPO funding",
            "AI drug discovery pipeline",
        ],
    },

    "B-8": {
        "name": "부동산_인프라",
        "name_kr": "부동산·인프라",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {
                "케이스실러_주택지수": ["CSUSHPISA", "부동산", "Index", "Monthly"],
                "미국_주택착공": ["HOUST", "부동산", "천건", "Monthly"],
            },
            "YFINANCE": {
                "부동산ETF": ["VNQ", "부동산", "USD", "Weekly"],
                "데이터센터REIT": ["EQIX", "인프라", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "US housing market 2026",
            "commercial real estate vacancy",
            "China property crisis",
            "data center REIT demand",
        ],
    },

    "B-9": {
        "name": "소비재_리테일",
        "name_kr": "소비재·리테일·럭셔리",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {
                "미국_소매판매": ["RSXFS", "소비", "십억USD", "Monthly"],
                "소비자신뢰지수": ["UMCSENT", "심리", "Index", "Monthly"],
            },
            "YFINANCE": {
                "소비재ETF": ["XLY", "소비재", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "US retail sales consumer spending 2026",
            "luxury goods LVMH sales",
            "e-commerce penetration",
            "consumer confidence",
        ],
    },

    "B-10": {
        "name": "물류_공급망_해운",
        "name_kr": "물류·공급망·해운",
        "group": "B_산업_섹터",
        "prompt_file": "sector_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "해운ETF": ["BDRY", "해운", "USD", "Weekly"],
                "페덱스": ["FDX", "물류", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "container shipping rate SCFI 2026",
            "supply chain pressure index",
            "Red Sea Houthi disruption",
            "reshoring nearshoring",
        ],
    },

    # ═══════════════════════════════════════════
    # C. 기술·혁신  (group: C_기술_혁신)
    # ═══════════════════════════════════════════

    "C-1": {
        "name": "양자컴퓨팅",
        "name_kr": "양자컴퓨팅",
        "group": "C_기술_혁신",
        "prompt_file": "tech_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "IonQ": ["IONQ", "양자", "USD", "Weekly"],
                "Rigetti": ["RGTI", "양자", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "quantum computing qubit 2026",
            "post-quantum cryptography PQC",
            "IBM quantum roadmap",
            "quantum advantage",
        ],
    },

    "C-2": {
        "name": "로보틱스_자동화",
        "name_kr": "로보틱스·자동화·Physical AI",
        "group": "C_기술_혁신",
        "prompt_file": "tech_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "로봇ETF": ["BOTZ", "로봇", "USD", "Weekly"],
                "테라다인": ["TER", "자동화", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "humanoid robot commercial deployment 2026",
            "industrial robot shipments IFR",
            "Tesla Optimus",
            "warehouse automation",
        ],
    },

    "C-3": {
        "name": "바이오테크_유전자",
        "name_kr": "바이오테크·합성생물학·유전자치료",
        "group": "C_기술_혁신",
        "prompt_file": "tech_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "유전체학ETF": ["ARKG", "바이오테크", "USD", "Weekly"],
                "CRISPR치료제": ["CRSP", "바이오테크", "USD", "Weekly"],
                "빔테라퓨틱스": ["BEAM", "바이오테크", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "CRISPR gene therapy clinical trial 2026",
            "synthetic biology",
            "mRNA platform",
            "brain computer interface",
        ],
    },

    "C-4": {
        "name": "우주_위성_기술",
        "name_kr": "우주·위성 기술",
        "group": "C_기술_혁신",
        "prompt_file": "tech_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "우주ETF": ["UFO", "우주", "USD", "Weekly"],
                "ARK우주ETF": ["ARKX", "우주", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "satellite launch count 2026",
            "Starlink subscribers",
            "space economy investment",
            "LEO satellite internet",
        ],
    },

    # ═══════════════════════════════════════════
    # D. 지정학·안보  (group: D_지정학_안보)
    # ═══════════════════════════════════════════

    "D-1": {
        "name": "미중_전략_경쟁",
        "name_kr": "미·중 전략 경쟁",
        "group": "D_지정학_안보",
        "prompt_file": "geopolitics_prompt.txt",
        "quantitative": {
            "FRED": {
                "미국_대중_무역적자": ["BOPGSTB", "무역", "십억USD", "Monthly"],
            },
            "YFINANCE": {
                "중국ETF": ["FXI", "중국", "USD", "Weekly"],
                "대만ETF": ["EWT", "대만", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "US China trade war tariff 2026",
            "Taiwan strait military",
            "chip export control",
            "AUKUS Quad alliance",
        ],
    },

    "D-2": {
        "name": "유럽_러시아_나토",
        "name_kr": "유럽·러시아·나토",
        "group": "D_지정학_안보",
        "prompt_file": "geopolitics_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "유럽증시_STOXX50": ["^STOXX50E", "유럽", "Pt", "Weekly"],
                "BAE시스템즈_ADR": ["BAESY", "방산", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "Ukraine war frontline 2026",
            "NATO defense spending GDP",
            "EU defense budget",
            "Russia sanctions effect",
        ],
    },

    "D-3": {
        "name": "중동_지정학",
        "name_kr": "중동·에너지 지정학",
        "group": "D_지정학_안보",
        "prompt_file": "geopolitics_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "브렌트유": ["BZ=F", "에너지", "USD", "Weekly"],
                "금_선물": ["GC=F", "안전자산", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "Middle East conflict Iran Israel 2026",
            "Houthi Red Sea shipping",
            "Saudi Vision 2030",
            "OPEC production policy",
        ],
    },

    "D-4": {
        "name": "글로벌_사우스",
        "name_kr": "인도·태평양·글로벌 사우스",
        "group": "D_지정학_안보",
        "prompt_file": "geopolitics_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "인도ETF": ["INDA", "인도", "USD", "Weekly"],
                "베트남ETF": ["VNM", "베트남", "USD", "Weekly"],
                "멕시코ETF": ["EWW", "멕시코", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "India GDP growth 2026",
            "ASEAN manufacturing shift",
            "nearshoring Mexico Vietnam",
            "Africa critical minerals",
        ],
    },

    # ═══════════════════════════════════════════
    # E. 정책·규제  (group: E_정책_규제)
    # ═══════════════════════════════════════════

    "E-1": {
        "name": "AI_규제_거버넌스",
        "name_kr": "AI 규제·거버넌스",
        "group": "E_정책_규제",
        "prompt_file": "policy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {},
        },
        "search_keywords": [
            "EU AI Act implementation 2026",
            "US AI executive order",
            "AI safety regulation",
            "deepfake regulation",
        ],
    },

    "E-2": {
        "name": "무역_산업_정책",
        "name_kr": "무역·산업 정책",
        "group": "E_정책_규제",
        "prompt_file": "policy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {},
        },
        "search_keywords": [
            "US IRA CHIPS Act subsidy 2026",
            "EU CBAM carbon border",
            "industrial policy subsidy war",
            "trade tariff negotiation",
        ],
    },

    "E-3": {
        "name": "금융_규제_감독",
        "name_kr": "금융 규제·감독",
        "group": "E_정책_규제",
        "prompt_file": "policy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {},
        },
        "search_keywords": [
            "Basel III bank capital regulation 2026",
            "crypto regulation MiCA",
            "SEC enforcement action",
            "CBDC pilot program",
        ],
    },

    "E-4": {
        "name": "데이터_사이버보안",
        "name_kr": "데이터·프라이버시·사이버보안",
        "group": "E_정책_규제",
        "prompt_file": "policy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "사이버보안ETF": ["HACK", "사이버보안", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "data privacy regulation GDPR 2026",
            "cyberattack state-sponsored",
            "data localization law",
            "cross-border data transfer",
        ],
    },

    # ═══════════════════════════════════════════
    # F. 사회·구조  (group: F_사회_구조)
    # ═══════════════════════════════════════════

    "F-1": {
        "name": "인구_노동_이민",
        "name_kr": "인구·노동·이민",
        "group": "F_사회_구조",
        "prompt_file": "social_prompt.txt",
        "quantitative": {
            "FRED": {
                "미국_경활참가율": ["CIVPART", "노동", "%", "Monthly"],
                "미국_실업률": ["UNRATE", "고용", "%", "Monthly"],
                "한국_출산율": ["SPDYNTFRTINKOR", "인구", "명", "Yearly"],
            },
            "YFINANCE": {},
        },
        "search_keywords": [
            "population decline fertility rate 2026",
            "immigration policy reform",
            "labor shortage aging society",
            "gig economy remote work",
        ],
    },

    "F-2": {
        "name": "불평등_정치양극화",
        "name_kr": "불평등·정치 양극화",
        "group": "F_사회_구조",
        "prompt_file": "social_prompt.txt",
        "quantitative": {
            "FRED": {
                "지니계수_미국": ["SIPOVGINIUSA", "불평등", "Index", "Yearly"],
                "가구중위소득_미국": ["MEHOINUSA646N", "소득", "USD", "Yearly"],
            },
            "YFINANCE": {},
        },
        "search_keywords": [
            "income inequality wealth gap 2026",
            "populism election results",
            "political polarization",
            "social unrest protest",
        ],
    },

    "F-3": {
        "name": "교육_인적자본",
        "name_kr": "교육·인적자본·AI 시대 노동",
        "group": "F_사회_구조",
        "prompt_file": "social_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {},
        },
        "search_keywords": [
            "AI job displacement automation 2026",
            "STEM education workforce",
            "university enrollment decline",
            "reskilling upskilling",
        ],
    },

    # ═══════════════════════════════════════════
    # G. 에너지·자원·기후  (group: G_에너지_자원)
    # ═══════════════════════════════════════════

    "G-1": {
        "name": "에너지전환_탈탄소",
        "name_kr": "에너지전환·탈탄소",
        "group": "G_에너지_자원",
        "prompt_file": "energy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "탄소배출권ETF": ["KRBN", "탄소", "USD", "Weekly"],
                "클린에너지ETF": ["ICLN", "에너지전환", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "net zero carbon transition 2026",
            "renewable energy capacity addition",
            "nuclear power plant new build",
            "hydrogen economy cost",
        ],
    },

    "G-2": {
        "name": "핵심광물_자원안보",
        "name_kr": "핵심광물·자원안보",
        "group": "G_에너지_자원",
        "prompt_file": "energy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "구리_선물": ["HG=F", "광물", "USD", "Weekly"],
                "리튬ETF": ["LIT", "광물", "USD", "Weekly"],
                "희토류ETF": ["REMX", "광물", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "critical minerals supply chain 2026",
            "lithium cobalt nickel price",
            "rare earth China export control",
            "mining investment Africa",
        ],
    },

    "G-3": {
        "name": "기후리스크_자연재해",
        "name_kr": "기후리스크·자연재해",
        "group": "G_에너지_자원",
        "prompt_file": "energy_prompt.txt",
        "quantitative": {
            "FRED": {},
            "YFINANCE": {
                "농산물ETF": ["DBA", "농산물", "USD", "Weekly"],
            },
        },
        "search_keywords": [
            "climate disaster cost insurance 2026",
            "El Nino La Nina impact",
            "crop yield food security",
            "water scarcity stress",
        ],
    },
}

# ─────────────────────────────────────────────
# 주간 분석 스케줄 (요일별 카테고리 배정)
# ─────────────────────────────────────────────
# 월~금 5일에 34개 카테고리를 분산 배치
# Monday(6) + Tuesday(7) + Wednesday(8) + Thursday(8) + Friday(5) = 34

SCHEDULE = {
    "monday":    ["A-1", "A-2", "A-3", "A-4", "A-5", "A-6"],                        # 6개 — 금융·시장 전체
    "tuesday":   ["B-1", "B-3", "B-4", "B-8", "B-9", "B-10", "G-2"],                # 7개 — 산업·섹터(전반) + 자원안보
    "wednesday": ["B-2", "B-5", "B-6", "B-7", "C-1", "C-2", "C-3", "C-4"],          # 8개 — 산업·섹터(후반) + 기술·혁신
    "thursday":  ["D-1", "D-2", "D-3", "D-4", "E-1", "E-2", "E-3", "E-4"],          # 8개 — 지정학·안보 + 정책·규제
    "friday":    ["F-1", "F-2", "F-3", "G-1", "G-3"],                                # 5개 — 사회·구조 + 에너지·기후
}

# ─────────────────────────────────────────────
# API 및 실행 설정
# ─────────────────────────────────────────────

COOLDOWN_SECONDS = 35   # Gemini 무료 API 분당 2회 제한 우회용
MAX_RETRIES = 3         # 네트워크 에러 시 재시도 횟수
TOP_NEWS_LIMIT = 5      # 카테고리당 뉴스 검색 결과 개수
