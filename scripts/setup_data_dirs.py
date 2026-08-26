"""로컬 데이터 폴더를 자동으로 생성하는 스크립트.

Git 저장소를 clone한 뒤, 실제 데이터(raw/processed)를 담을 폴더 구조를
로컬 PC에 생성한다. data/raw, data/processed의 실제 내용은 Git에서
제외되므로, 팀원마다 이 스크립트를 실행해 동일한 폴더 구조를
로컬에 준비해야 한다.

실행 방법:
    python scripts/setup_data_dirs.py
"""

from pathlib import Path

# 이 스크립트 파일(scripts/setup_data_dirs.py) 기준으로 저장소 루트를 계산한다.
# 어느 위치에서 실행하더라도 항상 저장소 루트 기준으로 폴더가 생성된다.
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"

SPLITS = ("train", "val", "test")
DATASETS = ("raw", "processed")
KINDS = ("images", "labels")


def build_target_dirs() -> list[Path]:
    """생성할 데이터 폴더 경로 목록을 반환한다."""
    targets = []
    for dataset in DATASETS:
        for kind in KINDS:
            for split in SPLITS:
                targets.append(DATA_ROOT / dataset / kind / split)
    return targets


def main() -> None:
    target_dirs = build_target_dirs()

    print(f"저장소 루트: {REPO_ROOT}")
    print("다음 데이터 폴더를 생성합니다:\n")

    for target_dir in target_dirs:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"  - {target_dir.relative_to(REPO_ROOT)}")

    print("\n로컬 데이터 폴더 생성이 완료되었습니다.")


if __name__ == "__main__":
    main()
