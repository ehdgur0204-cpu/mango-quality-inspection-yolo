"""
이미지-라벨 대응관계 점검 스크립트 — 2.1

data/raw/images/<split>/*.jpg 이미지와 data/raw/labels/<split>/*.txt 라벨이
파일 이름 기준으로 1:1 로 잘 짝지어져 있는지 확인한다.

라벨 쪽 정보는 다시 txt 를 읽지 않고, 2.2 단계에서 이미 만들어 둔 CSV
(outputs/(2.2)labels_csv 파일/*.csv) 를 재사용한다.
    labels_parsed.csv  박스가 있는 라벨 파일
    labels_empty.csv   내용이 비어 있는 라벨 파일 (Background 이미지 등)
    labels_errors.csv  형식이 이상한 줄이 있는 라벨 파일
                       (오류 줄만 있고 정상 박스가 하나도 없어도 '라벨은 존재함'으로 처리)

실행 방법 (프로젝트 최상위 폴더에서):
    python "scripts/(2.1)image-labels.py"

만들어지는 파일 (outputs/(2.1)image_labels/):
    image_without_label.csv   라벨 파일이 없는 이미지 목록
    label_without_image.csv   대응하는 이미지가 없는 라벨 목록
    split_mismatch.csv        같은 이름의 파일이 이미지/라벨에서 서로 다른
                               split 폴더에 들어있는 경우 (폴더를 잘못 넣은 의심)
"""

from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------ 설정

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = PROJECT_ROOT / "data" / "raw" / "images"
LABELS_CSV_DIR = PROJECT_ROOT / "outputs" / "(2.2)labels_csv 파일"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "(2.1)image_labels"

SPLITS = ["train", "val", "test"]
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG")


# ------------------------------------------------------------------ 이미지 목록

def list_images() -> pd.DataFrame:
    """data/raw/images/<split> 폴더를 실제로 훑어서 이미지 목록을 만든다."""
    rows = []
    for split in SPLITS:
        split_dir = IMAGE_ROOT / split
        if not split_dir.exists():
            print(f"[경고] 폴더가 없습니다: {split_dir}")
            continue

        for img_path in sorted(split_dir.iterdir()):
            if img_path.is_file() and img_path.suffix in IMAGE_EXTS:
                rows.append({
                    "split": split,
                    "image_name": img_path.stem,
                    "image_file": img_path.name,
                })

    return pd.DataFrame(rows, columns=["split", "image_name", "image_file"])


# ------------------------------------------------------------------ 라벨 목록 (CSV 재사용)

def load_label_index() -> pd.DataFrame:
    """(2.2) 단계 CSV 세 개를 합쳐 '실제로 존재하는 라벨 파일' 목록을 돌려준다."""
    frames = []

    for name in ("labels_parsed.csv", "labels_empty.csv"):
        path = LABELS_CSV_DIR / name
        if not path.exists():
            print(f"[경고] 파일이 없습니다: {path}")
            continue
        df = pd.read_csv(path, usecols=["split", "image_name", "label_file"])
        frames.append(df)

    # 형식 오류만 있는 라벨 파일도 '파일 자체는 존재함'으로 인정한다
    errors_path = LABELS_CSV_DIR / "labels_errors.csv"
    if errors_path.exists():
        try:
            df_err = pd.read_csv(errors_path, usecols=["split", "label_file"])
        except pd.errors.EmptyDataError:
            df_err = pd.DataFrame(columns=["split", "label_file"])  # 오류가 하나도 없었던 경우
        df_err = df_err.drop_duplicates()
        df_err["image_name"] = df_err["label_file"].apply(lambda f: Path(f).stem)
        frames.append(df_err[["split", "image_name", "label_file"]])
    else:
        print(f"[경고] 파일이 없습니다: {errors_path}")

    if not frames:
        return pd.DataFrame(columns=["split", "image_name", "label_file"])

    df_labels = pd.concat(frames, ignore_index=True)
    return df_labels.drop_duplicates(subset=["split", "image_name"])


# ------------------------------------------------------------------ 대응관계 점검

def check_correspondence(df_images: pd.DataFrame, df_labels: pd.DataFrame):
    """같은 split 안에서 이미지·라벨을 맞춰보고, 어긋난 목록들을 돌려준다."""

    merged = pd.merge(
        df_images, df_labels,
        on=["split", "image_name"], how="outer", indicator=True,
    )

    image_without_label = (
        merged[merged["_merge"] == "left_only"]
        [["split", "image_name", "image_file"]]
        .sort_values(["split", "image_name"])
        .reset_index(drop=True)
    )
    label_without_image = (
        merged[merged["_merge"] == "right_only"]
        [["split", "image_name", "label_file"]]
        .sort_values(["split", "image_name"])
        .reset_index(drop=True)
    )

    # 파일명은 같은데 이미지/라벨의 split 폴더가 서로 다른 경우
    # (위 두 목록에서 뽑아낸 '한쪽만 있는' 파일들 중, 다른 split에 짝이 있는지 확인)
    img_splits_by_name = df_images.groupby("image_name")["split"].apply(lambda s: sorted(set(s)))
    lbl_splits_by_name = df_labels.groupby("image_name")["split"].apply(lambda s: sorted(set(s)))

    mismatch_rows = []
    for _, row in image_without_label.iterrows():
        other_splits = lbl_splits_by_name.get(row["image_name"], [])
        if other_splits:
            mismatch_rows.append({
                "image_name": row["image_name"],
                "image_split": row["split"],
                "label_split": ",".join(other_splits),
            })
    for _, row in label_without_image.iterrows():
        other_splits = img_splits_by_name.get(row["image_name"], [])
        if other_splits:
            mismatch_rows.append({
                "image_name": row["image_name"],
                "image_split": ",".join(other_splits),
                "label_split": row["split"],
            })

    split_mismatch = (
        pd.DataFrame(mismatch_rows, columns=["image_name", "image_split", "label_split"])
        .drop_duplicates()
        .sort_values("image_name")
        .reset_index(drop=True)
    )

    return image_without_label, label_without_image, split_mismatch


# ------------------------------------------------------------------ 요약 출력

def print_summary(df_images, df_labels, image_without_label, label_without_image, split_mismatch):
    print("\n" + "=" * 60)
    print("이미지-라벨 대응관계 점검 결과")
    print("=" * 60)

    print("\n[ split 별 개수 ]")
    count_table = pd.DataFrame({
        "이미지수": df_images.groupby("split").size(),
        "라벨수": df_labels.groupby("split").size(),
    }).reindex(SPLITS).fillna(0).astype(int)
    print(count_table.to_string())

    print(f"\n라벨 없는 이미지 : {len(image_without_label)}건")
    print(f"이미지 없는 라벨 : {len(label_without_image)}건")
    print(f"split 불일치     : {len(split_mismatch)}건 (파일명은 같은데 폴더가 다름)")

    if image_without_label.empty and label_without_image.empty and split_mismatch.empty:
        print("\n문제 없음 - 모든 이미지와 라벨이 정확히 1:1로 대응합니다.")
        return

    if not image_without_label.empty:
        print("\n[ 라벨 없는 이미지 예시 (최대 5건) ]")
        print(image_without_label.head(5).to_string(index=False))

    if not label_without_image.empty:
        print("\n[ 이미지 없는 라벨 예시 (최대 5건) ]")
        print(label_without_image.head(5).to_string(index=False))

    if not split_mismatch.empty:
        print("\n[ split 불일치 예시 (최대 5건) ]")
        print(split_mismatch.head(5).to_string(index=False))


# ------------------------------------------------------------------ 실행

def main():
    print(f"이미지 폴더 : {IMAGE_ROOT}")
    print(f"라벨 CSV    : {LABELS_CSV_DIR}")

    df_images = list_images()
    df_labels = load_label_index()

    image_without_label, label_without_image, split_mismatch = check_correspondence(
        df_images, df_labels
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 엑셀에서 한글이 깨지지 않도록 utf-8-sig 로 저장
    image_without_label.to_csv(OUTPUT_DIR / "image_without_label.csv", index=False, encoding="utf-8-sig")
    label_without_image.to_csv(OUTPUT_DIR / "label_without_image.csv", index=False, encoding="utf-8-sig")
    split_mismatch.to_csv(OUTPUT_DIR / "split_mismatch.csv", index=False, encoding="utf-8-sig")

    print_summary(df_images, df_labels, image_without_label, label_without_image, split_mismatch)

    print("\n저장 완료:")
    for name in ("image_without_label.csv", "label_without_image.csv", "split_mismatch.csv"):
        print(f"  {OUTPUT_DIR / name}")


if __name__ == "__main__":
    main()
