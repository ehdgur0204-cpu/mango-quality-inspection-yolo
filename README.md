# 망고 품질검사 프로젝트 (mango-quality-inspection)

**YOLO 기반 망고 원물 입고검사 의사결정 지원 시스템 – 객체별 병해 상태 탐지, 모델 신뢰성 검증 및 LOT 품질 리포팅**

## 1. 프로젝트 배경

망고 원물 입고검사는 현재 대부분 작업자의 육안 판단에 의존하고 있다.
육안 검사는 작업자 간 판단 기준이 다를 수 있고, 검사 속도와 일관성 측면에서
한계가 있다. 본 프로젝트는 객체 탐지(Object Detection) 모델을 활용해
망고 개체별 병해 상태를 자동으로 탐지하고, 이를 품질 판정과 LOT 단위
리포팅으로 연결하는 의사결정 지원 시스템을 구축하고자 한다.

## 2. 문제 정의

- 망고 원물 입고 시, 개체별로 병해(Alternaria, Anthracnose, Scab) 여부와
  정상(Healthy) 여부를 빠르고 일관되게 판별해야 한다.
- 단순 분류가 아니라, 이미지 내 여러 망고 객체 각각의 위치와 상태를
  개별적으로 탐지해야 한다.
- 모델의 판단을 그대로 신뢰하기보다, 밝기·흐림·배경 변화 등 환경 요인에 따라
  모델이 얼마나 신뢰할 수 있는지 함께 검증해야 한다.

## 3. 프로젝트 목표

- YOLO 기반 객체 탐지 모델로 망고 개체별 병해 상태를 탐지한다.
- 탐지 결과를 PASS / HOLD / REJECT 품질 판정으로 변환하는 의사결정 로직을
  구현한다.
- 환경 변화(밝기, 흐림, 배경 등)에 따른 모델 신뢰성을 검증한다.
- 단일 이미지 검사와 LOT 단위 일괄검사를 모두 지원한다.
- Streamlit 기반 품질관리 대시보드를 제공한다.
- CSV 또는 PDF 형식의 품질검사 보고서를 생성한다.

## 4. 주요 기능

- 망고 객체별 `Alternaria`, `Anthracnose`, `Healthy`, `Scab` 탐지
- 탐지 결과를 `PASS`, `HOLD`, `REJECT` 품질 판정으로 변환
- 밝기, 흐림, 배경 변화 등에 따른 모델 신뢰성 검증
- 단일 이미지 및 LOT 단위 일괄검사
- Streamlit 품질관리 대시보드
- CSV 또는 PDF 품질검사 보고서 생성

## 5. 전체 처리 흐름

```text
망고 이미지 입력
→ YOLO 객체별 건강·병해 상태 탐지
→ Confidence 기반 PASS/HOLD/REJECT 판정
→ LOT 단위 품질 KPI 집계
→ 모델 신뢰성 검증
→ Streamlit 대시보드
→ 검사보고서 생성
```

## 6. 데이터셋 개요

| 항목 | 내용 |
|---|---|
| 이름 | MangoFruitBD |
| 버전 | Version 2 |
| 이미지 수 | 1,310장 |
| 객체 라벨 수 | 2,127개 |
| 클래스 | Alternaria, Anthracnose, Healthy, Scab |
| 라벨 형식 | YOLO Bounding Box |
| 출처 | https://data.mendeley.com/datasets/bhrz29mkmr/2 |
| 라이선스 | CC BY-NC 3.0 |

자세한 내용은 [docs/data_guide.md](docs/data_guide.md)와
[data/README.md](data/README.md)를 참고한다.

## 7. 클래스 설명

| 클래스명 | 설명 |
|---|---|
| Alternaria | 알터나리아병(검은 반점형 병해)이 있는 망고 |
| Anthracnose | 탄저병 병해가 있는 망고 |
| Healthy | 병해가 없는 정상 망고 |
| Scab | 더뎅이병(Scab) 병해가 있는 망고 |

## 8. 프로젝트 폴더 구조

```text
mango-quality-inspection/
├── README.md
├── .gitignore
├── .gitattributes
├── requirements.txt
│
├── configs/
│   ├── data.example.yaml
│   └── train.example.yaml
│
├── data/
│   └── README.md
│
├── notebooks/
│   └── README.md
│
├── src/
│   ├── __init__.py
│   ├── data/
│   ├── modeling/
│   ├── validation/
│   ├── decision/
│   ├── reporting/
│   └── utils/
│
├── scripts/
│   └── setup_data_dirs.py
│
├── app/
│   └── README.md
│
├── outputs/
│   └── README.md
│
├── weights/
│   └── README.md
│
├── docs/
│   ├── project_plan.md
│   ├── data_guide.md
│   └── inspection_policy.md
│
└── tests/
    └── README.md
```

## 9. 설치 방법

```bash
git clone <repository-url>
cd mango-quality-inspection

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 10. 데이터 준비 방법

1. Google Drive에서 다음 두 ZIP 파일을 내려받는다.
   - `MangoFruitBD_raw_v2.zip`
   - `MangoFruitBD_processed_v1.0.zip`
2. 로컬 데이터 폴더를 생성한다.
   ```bash
   python scripts/setup_data_dirs.py
   ```
3. 내려받은 ZIP 파일을 각각 `data/raw/`, `data/processed/`에 압축 해제한다.
4. `configs/data.example.yaml`을 복사해 `configs/data.local.yaml`을 만들고,
   `path` 값을 본인 PC의 절대경로로 수정한다.

자세한 내용은 [data/README.md](data/README.md)를 참고한다.

## 11. 향후 개발 계획

- 데이터 검증 및 EDA 노트북 작성 (`notebooks/`)
- YOLO 베이스라인 모델 학습 및 평가
- PASS/HOLD/REJECT 판정 로직 구현 (`src/decision/`)
- 모델 신뢰성 검증 로직 구현 (`src/validation/`)
- CSV/PDF 보고서 생성 기능 구현 (`src/reporting/`)
- Streamlit 대시보드 구현 (`app/`)
- 테스트 코드 작성 (`tests/`)

## 12. 데이터 출처와 라이선스

- 출처: https://data.mendeley.com/datasets/bhrz29mkmr/2
- 라이선스: CC BY-NC 3.0 (비상업적 이용, 출처 표기 필요)

## 13. 현재 프로젝트 상태

**현재 상태: 프로젝트 초기 구조 및 데이터 준비 단계**

아직 모델 학습, 품질 판정 로직, 대시보드, 보고서 생성 기능은 구현되지
않았다. 위 "향후 개발 계획"에 따라 순차적으로 구현할 예정이다.
