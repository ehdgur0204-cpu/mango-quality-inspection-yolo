# app 폴더 안내

이 폴더는 향후 구현할 Streamlit 품질관리 대시보드의 구조를 설명한다.
**현재 시점에는 실제 Streamlit 파일(`Home.py`, `pages/*.py`)이 아직 생성되어
있지 않다.** 아래 구조는 앞으로 구현할 예정 계획이다.

## 예정 구조

```text
app/
├── Home.py
└── pages/
    ├── 01_single_inspection.py
    ├── 02_lot_inspection.py
    ├── 03_model_reliability.py
    └── 04_inspection_report.py
```

## 각 페이지의 예정 기능

- **`Home.py`**: 대시보드 진입 화면. 프로젝트 개요와 각 페이지로의 이동 안내를
  제공할 예정이다.
- **`pages/01_single_inspection.py`**: 단일 망고 이미지를 업로드해 YOLO 탐지
  결과와 PASS/HOLD/REJECT 판정을 즉시 확인하는 페이지가 될 예정이다.
- **`pages/02_lot_inspection.py`**: 여러 이미지(LOT 단위)를 일괄 업로드하여
  LOT 전체의 품질 KPI(병해율, HOLD 비율 등)를 집계해 보여주는 페이지가 될
  예정이다.
- **`pages/03_model_reliability.py`**: 밝기, 흐림, 배경 변화 등 촬영 조건
  변화에 따른 모델 신뢰성 검증 결과를 시각화하는 페이지가 될 예정이다.
- **`pages/04_inspection_report.py`**: 검사 결과를 CSV 또는 PDF 형태의
  품질검사 보고서로 내보내는 페이지가 될 예정이다.
