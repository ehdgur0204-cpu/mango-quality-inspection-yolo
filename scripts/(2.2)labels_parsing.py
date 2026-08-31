"""
라벨(txt) 파싱 스크립트 — 2.2 / 2.3 / 2.4 공통 입력 생성

YOLO 라벨 파일(labels/<split>/*.txt)을 전부 읽어서
"박스 1개 = 1행" 형태의 표(CSV)로 만든다.

실행 방법 (프로젝트 최상위 폴더에서):
    python "scripts/labels_parsing(2.2).py"

만들어지는 파일 (outputs/ 폴더):
    labels_parsed.csv   박스 1개 = 1행. 클래스 분포·BBox 분석의 공통 입력
    labels_empty.csv    내용이 비어 있는 라벨 파일 목록 (2.5 담당에게 전달)
    labels_errors.csv   형식/범위가 이상한 줄 목록 (2.1 담당에게 전달)
"""

from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------ 설정

# 이 파일(scripts/xxx.py) 기준으로 프로젝트 최상위 폴더를 찾는다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LABEL_ROOT = PROJECT_ROOT / "data" / "raw" / "labels"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "(2.2)labels_csv"

SPLITS = ["train", "val", "test"]
CLASS_NAMES = {0: "Alternaria", 1: "Anthracnose", 2: "Healthy", 3: "Scab"}


# ------------------------------------------------------------------ 파싱

def parse_all_labels():
    """라벨 폴더 전체를 읽어서 (박스 목록, 빈 파일 목록, 오류 목록) 을 돌려준다."""
    boxes = []    # 정상적으로 읽은 박스
    empties = []  # 내용이 비어 있는 라벨 파일
    errors = []   # 형식이나 값이 이상한 줄

    for split in SPLITS:
        split_dir = LABEL_ROOT / split
        if not split_dir.exists():
            print(f"[경고] 폴더가 없습니다: {split_dir}")
            continue

        for txt_path in sorted(split_dir.glob("*.txt")):
            text = txt_path.read_text(encoding="utf-8")
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

            # 내용이 비어 있는 라벨 파일 (Background 이미지 등)
            if not lines:
                empties.append({
                    "split": split,
                    "label_file": txt_path.name,
                    "image_name": txt_path.stem,
                })
                continue

            for line_no, line in enumerate(lines, start=1):
                parts = line.split()

                # 숫자가 5개가 아니면 형식 오류
                if len(parts) != 5:
                    errors.append({
                        "split": split,
                        "label_file": txt_path.name,
                        "line_no": line_no,
                        "content": line,
                        "reason": f"값이 5개가 아님 ({len(parts)}개)",
                    })
                    continue

                # 숫자로 바꿀 수 없으면 형식 오류
                try:
                    class_id = int(float(parts[0]))
                    x_center, y_center, width, height = (float(v) for v in parts[1:])
                except ValueError:
                    errors.append({
                        "split": split,
                        "label_file": txt_path.name,
                        "line_no": line_no,
                        "content": line,
                        "reason": "숫자로 변환할 수 없는 값이 있음",
                    })
                    continue

                # 값의 범위 검사 — 이상해도 표에는 넣고, 오류 목록에도 남긴다
                reasons = []
                if class_id not in CLASS_NAMES:
                    reasons.append(f"클래스 번호가 0~3 밖 ({class_id})")
                if not all(0.0 <= v <= 1.0 for v in (x_center, y_center, width, height)):
                    reasons.append("좌표가 0~1 범위 밖")
                if width <= 0 or height <= 0:
                    reasons.append("폭 또는 높이가 0 이하")
                if reasons:
                    errors.append({
                        "split": split,
                        "label_file": txt_path.name,
                        "line_no": line_no,
                        "content": line,
                        "reason": ", ".join(reasons),
                    })

                boxes.append({
                    "split": split,
                    "image_name": txt_path.stem,
                    "label_file": txt_path.name,
                    "line_no": line_no,
                    "class_id": class_id,
                    "class_name": CLASS_NAMES.get(class_id, f"UNKNOWN({class_id})"),
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height,
                })

    return (pd.DataFrame(boxes),
            pd.DataFrame(empties),
            pd.DataFrame(errors))


# ------------------------------------------------------------------ 요약 출력

def print_summary(df_boxes, df_empty, df_error):
    print("\n" + "=" * 60)
    print("파싱 결과 요약")
    print("=" * 60)

    if df_boxes.empty:
        print("읽어들인 박스가 없습니다. 폴더 경로를 확인하세요.")
        return

    print(f"\n총 박스 수   : {len(df_boxes):,}개")
    print(f"총 이미지 수 : {df_boxes['image_name'].nunique():,}장 (박스가 있는 이미지)")
    print(f"빈 라벨 파일 : {len(df_empty)}개")
    print(f"오류 줄      : {len(df_error)}건")

    print("\n[ split 별 ]")
    split_table = pd.DataFrame({
        "이미지수": df_boxes.groupby("split")["image_name"].nunique(),
        "박스수": df_boxes.groupby("split").size(),
    }).reindex(SPLITS)
    print(split_table.to_string())

    print("\n[ 클래스 별 ]")
    class_table = pd.DataFrame({
        "박스수": df_boxes.groupby("class_name").size(),
        "이미지수": df_boxes.groupby("class_name")["image_name"].nunique(),
    })
    class_table["박스비율"] = (class_table["박스수"] / len(df_boxes) * 100).round(1)
    print(class_table.sort_values("박스수", ascending=False).to_string())

    if not df_error.empty:
        print("\n[ 오류 줄 예시 (최대 5건) ]")
        print(df_error.head(5).to_string(index=False))


# ------------------------------------------------------------------ 실행

def main():
    print(f"라벨 폴더 : {LABEL_ROOT}")

    df_boxes, df_empty, df_error = parse_all_labels()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 엑셀에서 한글이 깨지지 않도록 utf-8-sig 로 저장
    df_boxes.to_csv(OUTPUT_DIR / "labels_parsed.csv", index=False, encoding="utf-8-sig")
    df_empty.to_csv(OUTPUT_DIR / "labels_empty.csv", index=False, encoding="utf-8-sig")
    df_error.to_csv(OUTPUT_DIR / "labels_errors.csv", index=False, encoding="utf-8-sig")

    print_summary(df_boxes, df_empty, df_error)

    print("\n저장 완료:")
    for name in ("labels_parsed.csv", "labels_empty.csv", "labels_errors.csv"):
        print(f"  {OUTPUT_DIR / name}")


if __name__ == "__main__":
    main()
