# data 폴더 안내

이 폴더는 망고 품질검사 프로젝트에서 사용하는 데이터의 위치와 구조를 설명한다.
**실제 이미지·라벨 파일은 GitHub 저장소에 포함되지 않는다.** `data/raw/`와
`data/processed/`는 `.gitignore`에 등록되어 있으며, 이 `data/README.md` 파일만
Git에서 추적되어 저장소에 올라간다.

## raw vs processed

- **`data/raw/`**: Google Drive에서 내려받은 원본 데이터 그대로를 보관한다.
  **원본 데이터는 어떤 이유로도 직접 수정하지 않는다.** 라벨 오류 수정, 중복 제거,
  전처리 등 모든 가공 작업은 반드시 `processed`에 결과물로 남긴다.
- **`data/processed/`**: 다음 작업이 완료된 데이터를 저장하는 폴더다.
  - 이미지와 라벨 파일 대응(짝) 여부 검사
  - YOLO 좌표(bounding box)가 정상 범위인지 검사
  - 잘못된 라벨 수정
  - 중복 이미지 처리
  - Train / Validation / Test 분할 검증
  - 필요한 전처리(리사이즈, 정규화 등) 결과 반영
  - 처리 내역을 기록한 `processing_manifest.json` 생성

## Google Drive 다운로드

아래 두 ZIP 파일을 Google Drive에서 내려받는다.

```text
MangoFruitBD_raw_v2.zip
MangoFruitBD_processed_v1.0.zip
```

Google Drive 링크: 추후 입력

### 압축 해제 위치

내려받은 ZIP 파일은 각각 다음 위치에 압축을 해제한다.

- `MangoFruitBD_raw_v2.zip` → `data/raw/` 아래에 압축 해제
- `MangoFruitBD_processed_v1.0.zip` → `data/processed/` 아래에 압축 해제

압축 해제 전, `python scripts/setup_data_dirs.py`를 먼저 실행해 폴더 구조를
만들어 두는 것을 권장한다.

## 예상 데이터 폴더 구조

```text
data/
├── README.md
├── raw/
│   ├── images/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── labels/
│   │   ├── train/
│   │   ├── val/
│   │   └── test/
│   ├── data.yaml
│   ├── CITATION.cff
│   ├── LICENSE.txt
│   └── DATASET_README.md
│
└── processed/
    ├── images/
    │   ├── train/
    │   ├── val/
    │   └── test/
    ├── labels/
    │   ├── train/
    │   ├── val/
    │   └── test/
    └── processing_manifest.json
```

## 이미지와 라벨 대응 규칙

이미지 파일과 라벨 파일은 **같은 파일명**을 사용하고 확장자만 다르다.

```text
images/train/Alternaria (1).jpg
labels/train/Alternaria (1).txt
```

즉, `images/<split>/<파일명>.jpg`가 있다면 `labels/<split>/<파일명>.txt`가
반드시 짝을 이루어야 한다.

## Git에서 제외되는 항목

- `data/raw/` 내부의 모든 실제 데이터 파일
- `data/processed/` 내부의 모든 실제 데이터 파일

위 폴더의 실제 내용은 용량 문제와 라이선스 문제로 GitHub에 올리지 않는다.
팀원은 각자 Google Drive에서 데이터를 내려받아 로컬에 준비해야 한다.

## 데이터 라이선스와 출처

- 데이터셋: MangoFruitBD (Version 2)
- 출처: https://data.mendeley.com/datasets/bhrz29mkmr/2
- 라이선스: CC BY-NC 3.0 (비상업적 이용, 출처 표기 필요)
