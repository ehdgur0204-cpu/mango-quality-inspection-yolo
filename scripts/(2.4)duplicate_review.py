"""
중복 이미지 비교용 시트 생성 — 2.4

duplicate_groups.csv 를 읽어,
같은 중복 묶음의 이미지 2개를 한 장에 붙여서 사람 눈으로 쉽게 비교할 수 있게 만든다.

출력 형식:
    outputs/duplicate_review/
        pair_001.jpg
        pair_002.jpg
        ...

각 결과 이미지는 좌우 2개 이미지를 나란히 붙이고,
아래쪽에 각 이미지 이름을 캡션으로 표시한다.

주의:
    라벨 정보는 전혀 사용하지 않고, 사람 눈으로 중복 여부만 확인하는 용도다.
"""

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ------------------------------------------------------------------ 설정

PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROUP_CSV = PROJECT_ROOT / "outputs" / "(2.4)duplicate_check" / "duplicate_groups.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "duplicate_review"

PANEL_W = 900
PANEL_H = 900
CAPTION_H = 58
GAP = 24
OUTER_MARGIN = 28

FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_font(size: int):
    """한글/영문 폰트를 찾고, 없으면 기본 폰트를 사용한다."""
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_TITLE = load_font(24)
FONT_CAPTION = load_font(18)


# ------------------------------------------------------------------ 경로 처리

def resolve_image_path(file_path_value: str) -> Path:
    """CSV에 적힌 경로 문자열을 프로젝트 기준 절대 경로로 변환한다."""
    rel_path = Path(str(file_path_value).replace("\\", "/"))
    return (PROJECT_ROOT / rel_path).resolve()


# ------------------------------------------------------------------ 이미지 준비

def fit_to_box(image: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """비율을 유지하면서 지정된 영역에 맞춰 이미지를 조절한다."""
    image = ImageOps.exif_transpose(image).convert("RGB")
    orig_w, orig_h = image.size
    scale = min(target_w / orig_w, target_h / orig_h)
    new_w = max(1, int(orig_w * scale))
    new_h = max(1, int(orig_h * scale))
    resized = image.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (target_w, target_h), (245, 245, 245))
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    canvas.paste(resized, (x, y))
    return canvas


# ------------------------------------------------------------------ 한 장짜리 비교 이미지 생성

def build_pair_image(left_row: pd.Series, right_row: pd.Series, pair_idx: int) -> Image.Image:
    """두 이미지를 좌우로 붙이고 이름 캡션을 아래에 넣는 최종 비교 이미지를 만든다."""
    width = PANEL_W * 2 + GAP
    height = PANEL_H + CAPTION_H + OUTER_MARGIN * 2

    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # 상단 헤더
    title = f"Duplicate Pair {pair_idx:03d}"
    title_box = draw.textbbox((0, 0), title, font=FONT_TITLE)
    draw.text((OUTER_MARGIN, OUTER_MARGIN), title, fill=(40, 40, 40), font=FONT_TITLE)

    # 좌/우 패널 시작 위치
    left_x = OUTER_MARGIN
    right_x = OUTER_MARGIN + PANEL_W + GAP
    top_y = OUTER_MARGIN + 28

    # 이미지를 각 패널에 넣기
    left_path = resolve_image_path(left_row["file_path"])
    right_path = resolve_image_path(right_row["file_path"])

    left_img = fit_to_box(Image.open(left_path), PANEL_W, PANEL_H)
    right_img = fit_to_box(Image.open(right_path), PANEL_W, PANEL_H)

    canvas.paste(left_img, (left_x, top_y))
    canvas.paste(right_img, (right_x, top_y))

    # 경계선
    draw.rectangle(
        [left_x - 2, top_y - 2, left_x + PANEL_W + 1, top_y + PANEL_H + 1],
        outline=(180, 180, 180), width=2,
    )
    draw.rectangle(
        [right_x - 2, top_y - 2, right_x + PANEL_W + 1, top_y + PANEL_H + 1],
        outline=(180, 180, 180), width=2,
    )

    # 캡션 바
    caption_y = top_y + PANEL_H + 8
    panel_left_label = f"KEEP: {left_row['image_name']}"
    panel_right_label = f"DUP: {right_row['image_name']}"

    left_label_box = draw.textbbox((0, 0), panel_left_label, font=FONT_CAPTION)
    right_label_box = draw.textbbox((0, 0), panel_right_label, font=FONT_CAPTION)

    left_label_h = left_label_box[3] - left_label_box[1]
    right_label_h = right_label_box[3] - right_label_box[1]

    # 왼쪽 캡션 배경
    draw.rectangle(
        [left_x, caption_y, left_x + PANEL_W, caption_y + CAPTION_H],
        fill=(242, 242, 242), outline=(210, 210, 210), width=1,
    )
    draw.rectangle(
        [right_x, caption_y, right_x + PANEL_W, caption_y + CAPTION_H],
        fill=(242, 242, 242), outline=(210, 210, 210), width=1,
    )

    # 텍스트 위치 (중앙 정렬)
    draw.text(
        (left_x + 12, caption_y + (CAPTION_H - left_label_h) // 2 - 2),
        panel_left_label,
        fill=(35, 35, 35),
        font=FONT_CAPTION,
    )
    draw.text(
        (right_x + 12, caption_y + (CAPTION_H - right_label_h) // 2 - 2),
        panel_right_label,
        fill=(35, 35, 35),
        font=FONT_CAPTION,
    )

    # 하단 추가 메모: group_id / split 정보
    group_label = f"group_id={int(left_row['group_id'])}, split={left_row['split']} / {right_row['split']}"
    draw.text((OUTER_MARGIN, height - 26), group_label, fill=(90, 90, 90), font=FONT_CAPTION)

    return canvas


# ------------------------------------------------------------------ 메인

def main():
    if not GROUP_CSV.exists():
        raise FileNotFoundError(f"중복 CSV를 찾을 수 없습니다: {GROUP_CSV}")

    df = pd.read_csv(GROUP_CSV)

    if df.empty:
        print("중복 데이터가 없습니다. 출력할 이미지가 없습니다.")
        return

    # group_size가 2인 그룹만 비교용 이미지로 생성
    valid_groups = df[df["group_size"] == 2].copy()

    if valid_groups.empty:
        print("group_size == 2 인 중복 그룹이 없습니다.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processed = 0
    for group_id, group in valid_groups.groupby("group_id", sort=True):
        keep_row = group[group["role"] == "keep"].iloc[0]
        dup_row = group[group["role"] == "duplicate"].iloc[0]

        pair_img = build_pair_image(keep_row, dup_row, processed + 1)
        out_path = OUTPUT_DIR / f"pair_{int(group_id):03d}.jpg"
        pair_img.save(out_path, quality=92)
        processed += 1

    print(f"중복 비교 이미지 저장 완료: {processed}장")
    print(f"저장 경로: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
