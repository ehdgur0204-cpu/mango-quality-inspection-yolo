# 데이터 가이드 (Data Guide)

## 1. 데이터셋 개요

- 이름: MangoFruitBD
- 버전: Version 2
- 이미지 수: 1,310장
- 객체 라벨 수: 2,127개
- 클래스: Alternaria, Anthracnose, Healthy, Scab
- 라벨 형식: YOLO Bounding Box
- 출처: https://data.mendeley.com/datasets/bhrz29mkmr/2
- 라이선스: CC BY-NC 3.0

## 2. 클래스 설명

| 클래스명      | 설명                              |
|--------------|-----------------------------------|
| Alternaria   | 알터나리아병(검은 반점형 병해)이 있는 망고 |
| Anthracnose  | 탄저병 병해가 있는 망고            |
| Healthy      | 병해가 없는 정상 망고               |
| Scab         | 더뎅이병(Scab) 병해가 있는 망고     |

## 3. 이미지와 YOLO 라벨 구조

- 이미지는 `images/<split>/` 폴더에, 라벨은 `labels/<split>/` 폴더에 저장된다.
- 이미지 파일과 라벨 파일은 **같은 파일명**을 사용하고 확장자만 다르다.

```text
images/train/Alternaria (1).jpg
labels/train/Alternaria (1).txt
```

- 라벨 파일의 각 줄은 YOLO 형식(`class_id x_center y_center width height`,
  모두 0~1 사이로 정규화된 값)을 따른다.

## 4. Train / Validation / Test 구성

- 데이터는 `train`, `val`, `test` 세 개의 split으로 구성된다.
- 각 split별 정확한 이미지 수, 클래스별 분포는 데이터 검증 단계(EDA)에서
  확인하고 문서화할 예정이다.

## 5. 데이터 품질검사 계획

- 이미지-라벨 파일명 대응 여부 검사
- YOLO 좌표(x_center, y_center, width, height)가 0~1 범위인지 검사
- 클래스 번호가 0~3 범위인지 검사
- 라벨이 없는 이미지, 이미지가 없는 라벨 존재 여부 검사

## 6. 클래스 불균형 확인 계획

- 클래스별 객체 수(라벨 수)와 이미지 수를 집계하여 불균형 여부를 확인한다.
- 불균형이 확인될 경우 데이터 증강, 클래스 가중치 조정 등의 대응 방안을
  검토한다.

## 7. Alternaria 배경 편향 가능성

- Alternaria 클래스의 경우 촬영 배경이나 조명 조건이 다른 클래스와 다르게
  편향되어 있을 가능성이 있다. 이는 모델이 병해 자체가 아니라 배경 특징으로
  분류를 학습하는 원인이 될 수 있으므로, EDA 및 모델 신뢰성 검증 단계에서
  반드시 확인이 필요하다.

## 8. 중복 이미지 검사 계획

- 동일하거나 매우 유사한 이미지가 여러 split에 중복 포함되어 있는지 검사한다.
- 특히 train/val/test 간 데이터 누수(data leakage)가 발생하지 않도록 중복
  이미지가 서로 다른 split에 나뉘어 들어가지 않았는지 확인한다.

## 9. 데이터 라이선스와 사용상 주의사항

- 라이선스: CC BY-NC 3.0 (비상업적 이용만 허용, 출처 표기 필요)
- 본 프로젝트는 학습·연구 목적으로 데이터셋을 사용하며, 상업적 이용 시에는
  별도의 라이선스 확인이 필요하다.

## 10. 데이터 버전 관리 방법

- 원본 데이터는 `data/raw/`에, 가공된 데이터는 `data/processed/`에 분리
  보관한다.
- 실제 데이터 파일은 Git으로 관리하지 않고 Google Drive를 통해 ZIP 파일
  단위(`MangoFruitBD_raw_v2.zip`, `MangoFruitBD_processed_v1.0.zip`)로
  버전을 구분해 공유한다.
- `processed` 데이터의 가공 이력은 `data/processed/processing_manifest.json`
  파일에 기록한다.
