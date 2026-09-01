"""
이미지 중복검사 스크립트 — 2.4

data/raw/images/<split>/ 안의 이미지 파일을 전부 읽어서
"내용이 완전히 똑같은 파일"을 찾아낸다.

원리:
    파일 내용을 통째로 계산해서 짧은 지문(해시) 문자열을 만든다.
    내용이 1바이트라도 다르면 지문이 완전히 달라지고,
    내용이 같으면 파일 이름이 달라도 항상 같은 지문이 나온다.
    → 지문이 같은 파일끼리 묶으면 그게 중복 묶음이다.

실행 방법 (프로젝트 최상위 폴더에서):
    python "scripts/(2.4)duplicate_check.py"

만들어지는 파일 (outputs/(2.4)duplicate_check/ 폴더):
    duplicate_groups.csv   중복 묶음 목록. 파일 1개 = 1행 (읽기 쉬운 기본 결과)
    duplicate_pairs.csv    중복 쌍 목록. 쌍 1개 = 1행
    read_errors.csv        열지 못한 파일 목록

주의:
    이 스크립트는 파일을 지우지 않는다. 목록만 만든다.
    CSV를 사람이 확인한 뒤 삭제 여부를 결정할 것.

남길 파일(keep) 선정 규칙:
    묶음 안에서 경로 사전순으로 첫 번째 파일을 남김(keep),
    나머지를 중복(duplicate)으로 표시한다. 항상 같은 결과가 나오도록 한 규칙이다.
    split이 섞인 묶음은 어느 쪽을 지울지 사람이 판단해야 하므로 별도로 표시한다.
"""

import csv
import hashlib
from itertools import combinations
from pathlib import Path

import pandas as pd

# ------------------------------------------------------------------ 설정

# 이 파일(scripts/xxx.py) 기준으로 프로젝트 최상위 폴더를 찾는다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = PROJECT_ROOT / "data" / "raw" / "images"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "(2.4)duplicate_check"

SPLITS = ["train", "val", "test"]
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

# 지문을 만들 때 한 번에 읽는 크기 (큰 파일도 메모리에 통째로 올리지 않기 위함)
CHUNK_SIZE = 1024 * 1024  # 1MB


# ------------------------------------------------------------------ 파일 수집

def collect_image_files():
    """split 폴더를 돌면서 이미지 파일 경로 목록을 만든다."""
    files = []

    for split in SPLITS:
        split_dir = IMAGE_ROOT / split
        if not split_dir.exists():
            print(f"[경고] 폴더가 없습니다: {split_dir}")
            continue

        found = [p for p in sorted(split_dir.rglob("*"))
                 if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
        print(f"  {split:5s} : {len(found):,}장")
        files.extend((split, p) for p in found)

    return files


# ------------------------------------------------------------------ 지문(해시) 계산

def file_hash(path):
    """파일 내용을 조각내어 읽으면서 SHA-256 지문 문자열을 만든다."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def build_hash_table(files):
    """{지문: [(split, 경로), ...]} 형태의 표와, 읽기 실패 목록을 만든다."""
    table = {}
    errors = []
    total = len(files)

    for i, (split, path) in enumerate(files, start=1):
        try:
            digest = file_hash(path)
        except OSError as e:
            errors.append({
                "split": split,
                "file_path": str(path.relative_to(PROJECT_ROOT)),
                "reason": f"파일을 읽을 수 없음: {e}",
            })
            continue

        table.setdefault(digest, []).append((split, path))

        if i % 200 == 0 or i == total:
            print(f"  진행 {i:,}/{total:,}장")

    return table, errors


# ------------------------------------------------------------------ 결과 표 만들기

def build_group_rows(table):
    """파일이 2개 이상 들어있는 묶음만 골라 '파일 1개 = 1행' 표로 만든다."""
    # 지문이 같은 파일이 2개 이상인 것만 = 중복 묶음
    dup_items = [(digest, sorted(items, key=lambda x: str(x[1])))
                 for digest, items in table.items() if len(items) > 1]
    # 묶음 크기가 큰 것부터, 같으면 경로순으로 정렬 → 항상 같은 번호가 붙는다
    dup_items.sort(key=lambda x: (-len(x[1]), str(x[1][0][1])))

    rows = []
    for group_id, (digest, items) in enumerate(dup_items, start=1):
        splits_in_group = {split for split, _ in items}
        cross_split = len(splits_in_group) > 1

        for order, (split, path) in enumerate(items):
            rows.append({
                "group_id": group_id,
                "group_size": len(items),
                "role": "keep" if order == 0 else "duplicate",
                "split": split,
                "image_name": path.name,
                "file_path": str(path.relative_to(PROJECT_ROOT)),
                "file_size": path.stat().st_size,
                "cross_split": cross_split,   # split을 넘나드는 중복 = 분할 누수 위험
                "hash": digest,
            })

    return pd.DataFrame(rows)


def build_pair_rows(df_groups):
    """묶음 표를 바탕으로 '쌍 1개 = 1행' 표를 만든다."""
    rows = []

    if df_groups.empty:
        return pd.DataFrame(rows)

    for group_id, group in df_groups.groupby("group_id", sort=True):
        records = group.to_dict("records")
        for a, b in combinations(records, 2):
            rows.append({
                "group_id": group_id,
                "split_a": a["split"],
                "image_a": a["image_name"],
                "path_a": a["file_path"],
                "split_b": b["split"],
                "image_b": b["image_name"],
                "path_b": b["file_path"],
                "cross_split": a["split"] != b["split"],
            })

    return pd.DataFrame(rows)


# ------------------------------------------------------------------ 요약 출력

def print_summary(total_files, df_groups, df_pairs, errors):
    print("\n" + "=" * 60)
    print("중복검사 결과 요약")
    print("=" * 60)

    if total_files == 0:
        print("\n검사한 이미지가 없습니다. 폴더 경로를 확인하세요.")
        return

    if df_groups.empty:
        print(f"\n전체 이미지        : {total_files:,}장")
        print("중복 묶음          : 0개")
        print("\n내용이 완전히 같은 파일은 없습니다.")
        if errors:
            print(f"\n[주의] 읽지 못한 파일 {len(errors)}건 — read_errors.csv 확인")
        return

    n_dup_files = int((df_groups["role"] == "duplicate").sum())   # 지워도 되는 여분
    n_involved = len(df_groups)                                   # 중복에 연루된 전체
    n_groups = int(df_groups["group_id"].nunique())
    n_unique = total_files - n_dup_files

    print(f"\n전체 이미지        : {total_files:,}장")
    print(f"서로 다른 이미지   : {n_unique:,}장")
    print(f"중복 묶음          : {n_groups:,}개")
    print(f"중복에 연루된 파일 : {n_involved:,}장 (묶음에 속한 전부)")
    print(f"지워도 되는 여분   : {n_dup_files:,}장 "
          f"({n_dup_files / total_files * 100:.1f}%)")
    print(f"중복 쌍            : {len(df_pairs):,}쌍")

    print("\n[ split 별 여분 파일 수 ]")
    dup_only = df_groups[df_groups["role"] == "duplicate"]
    split_table = dup_only.groupby("split").size().reindex(SPLITS, fill_value=0)
    for split, cnt in split_table.items():
        print(f"  {split:5s} : {cnt:,}장")

    # split을 넘나드는 중복 = train/val/test 분할 누수 위험이라 따로 강조
    cross_groups = df_groups[df_groups["cross_split"]]["group_id"].nunique()
    print(f"\n[ split을 넘나드는 중복 묶음 ] {cross_groups:,}개")
    if cross_groups:
        print("  → 같은 이미지가 train/val/test에 나눠 들어가 있습니다.")
        print("     분할 누수(data leakage)이므로 재분할 검토가 필요합니다.")

    print("\n[ 중복 묶음 미리보기 (상위 3개 묶음) ]")
    preview_ids = df_groups["group_id"].drop_duplicates().head(3)
    preview = df_groups[df_groups["group_id"].isin(preview_ids)]
    cols = ["group_id", "role", "split", "image_name", "file_size", "cross_split"]
    print(preview[cols].to_string(index=False))

    if errors:
        print(f"\n[주의] 읽지 못한 파일 {len(errors)}건 — read_errors.csv 확인")


# ------------------------------------------------------------------ 실행

def main():
    print(f"이미지 폴더 : {IMAGE_ROOT}\n")

    print("[1/3] 파일 목록 수집")
    files = collect_image_files()
    total_files = len(files)
    print(f"  합계  : {total_files:,}장")

    if total_files == 0:
        print("\n검사할 이미지가 없습니다. 종료합니다.")
        return

    print("\n[2/3] 지문(해시) 계산")
    table, errors = build_hash_table(files)

    print("\n[3/3] 중복 묶음 정리 및 저장")
    df_groups = build_group_rows(table)
    df_pairs = build_pair_rows(df_groups)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 엑셀에서 한글이 깨지지 않도록 utf-8-sig 로 저장
    df_groups.to_csv(OUTPUT_DIR / "duplicate_groups.csv",
                     index=False, encoding="utf-8-sig")
    df_pairs.to_csv(OUTPUT_DIR / "duplicate_pairs.csv",
                    index=False, encoding="utf-8-sig")

    with open(OUTPUT_DIR / "read_errors.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["split", "file_path", "reason"])
        writer.writeheader()
        writer.writerows(errors)

    print_summary(total_files, df_groups, df_pairs, errors)

    print("\n저장 완료:")
    for name in ("duplicate_groups.csv", "duplicate_pairs.csv", "read_errors.csv"):
        print(f"  {OUTPUT_DIR / name}")


if __name__ == "__main__":
    main()
