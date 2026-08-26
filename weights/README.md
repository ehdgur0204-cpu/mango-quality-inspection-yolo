# weights 폴더 안내

이 폴더는 학습된 YOLO 모델의 가중치 파일(`best.pt`, `last.pt` 등)을 저장하는
곳이다.

## Git 관리 원칙

- 가중치 파일(`.pt` 등)은 용량이 크기 때문에 **GitHub 저장소에 직접 올리지
  않는다.**
- `weights/*`는 `.gitignore`에 등록되어 있으며, 이 `README.md` 파일만
  예외적으로 Git에 포함된다.
- 학습된 가중치는 추후 **Google Drive 또는 GitHub Release**를 통해 팀원과
  공유할 예정이다.

## 가중치 기록 계획

각 가중치 파일을 공유할 때는 아래 정보를 함께 문서에 기록할 예정이다.

- 모델 버전 (예: yolov8n, yolov8s 등)
- 학습 날짜
- 사용한 데이터 버전 (예: MangoFruitBD processed v1.0)
- 주요 성능 지표 (mAP, Precision, Recall 등)

현재 시점에는 아직 학습된 가중치나 기록이 없으며, 모델 학습이 진행되는 대로
이 문서를 업데이트할 예정이다.
