"""
바운딩 박스 격자 시트 생성 — 전수 육안 훑기용

data/raw/images 안의 모든 사진에 라벨의 바운딩 박스를 빨간색으로 그린 뒤,
16장(4x4)씩 묶어 한 장의 큰 이미지로 만든다.
각 사진 아래에는 [시트번호-칸번호] 사진이름 이 적힌다.

팀원들이 이 시트를 넘겨보며 결함을 찾고, 이상한 칸의 번호를 기록하면 된다.
예) "07-13 박스가 망고 밖에 있음"

실행 방법 (프로젝트 최상위 폴더에서):
    python "scripts/(2.2)bbox_grid_review.py"

만들어지는 파일:
    outputs/(2.2)bbox_grid_review/train_sheet_001.jpg ...   격자 시트
    outputs/(2.2)bbox_grid_review/grid_index.csv            칸번호 - 사진이름 대조표
"""

from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

# ------------------------------------------------------------------ 설정

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_ROOT = PROJECT_ROOT / "data" / "raw" / "images"
LABEL_CSV = PROJECT_ROOT / "outputs" / "(2.2)labels_csv 파일" / "labels_parsed.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "(2.2)bbox_grid_review"

SPLITS = ["train", "val", "test"]
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG")

# 격자 모양
GRID_COLS = 4
GRID_ROWS = 4
PER_SHEET = GRID_COLS * GRID_ROWS   # 16장

# 칸 하나의 크기 (픽셀)
CELL_IMG = 420        # 사진이 들어갈 정사각형 영역
CAPTION_H = 46        # 사진 아래 이름이 들어갈 띠의 높이
PAD = 10              # 칸 사이 여백

# 박스 모양
BOX_COLOR = (220, 30, 30)
BOX_WIDTH = 3
SHOW_CLASS_LABEL = True   # 박스 옆에 클래스 이름 표시. 지저분하면 False 로

# 색
BG_COLOR = (255, 255, 255)
CELL_BG = (245, 245, 245)
TEXT_COLOR = (30, 30, 30)
JPEG_QUALITY = 88


# ------------------------------------------------------------------ 준비

def load_font(size: int):
    """한글/영문 폰트를 찾아서 불러온다. 없으면 기본 폰트."""
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_CAPTION = load_font(20)
FONT_LABEL = load_font(16)


def load_boxes_by_image(csv_path: Path) -> dict:
    """파싱 CSV를 읽어서 {(split, 사진이름): [박스, ...]} 형태로 만든다."""
    df = pd.read_csv(csv_path)
    grouped = {}
    for (split, name), sub in df.groupby(["split", "image_name"]):
        grouped[(split, name)] = sub[
            ["class_name", "x_center", "y_center", "width", "height"]
        ].to_dict("records")
    return grouped


def list_images(split: str) -> list:
    """해당 split 폴더의 사진 파일 전부를 이름순으로."""
    folder = IMAGE_ROOT / split
    if not folder.exists():
        print(f"[경고] 폴더가 없습니다: {folder}")
        return []
    files = [p for p in folder.iterdir() if p.suffix in IMAGE_EXTS]
    return sorted(files, key=lambda p: p.stem.lower())


# ------------------------------------------------------------------ 칸 하나 만들기

def make_cell(img_path: Path, boxes: list, caption: str) -> Image.Image:
    """사진 한 장에 박스를 그리고, 아래에 이름을 붙인 칸 이미지를 만든다."""
    cell = Image.new("RGB", (CELL_IMG, CELL_IMG + CAPTION_H), CELL_BG)

    try:
        photo = Image.open(img_path)
        photo.draft("RGB", (CELL_IMG * 2, CELL_IMG * 2))  # JPEG 디코딩 속도 향상
        photo = photo.convert("RGB")
    except OSError:
        photo = None

    if photo is None:
        draw = ImageDraw.Draw(cell)
        draw.text((10, 10), "이미지를 열 수 없음", fill=(200, 0, 0), font=FONT_CAPTION)
    else:
        orig_w, orig_h = photo.size

        # 비율을 유지한 채 칸 안에 맞춰 줄인다
        scale = min(CELL_IMG / orig_w, CELL_IMG / orig_h)
        new_w, new_h = max(1, int(orig_w * scale)), max(1, int(orig_h * scale))
        photo = photo.resize((new_w, new_h), Image.LANCZOS)

        # 칸 가운데에 배치
        off_x = (CELL_IMG - new_w) // 2
        off_y = (CELL_IMG - new_h) // 2
        cell.paste(photo, (off_x, off_y))

        # 박스 그리기 — 라벨 좌표는 0~1 비율이므로 줄인 크기에 맞춰 환산
        draw = ImageDraw.Draw(cell)
        for box in boxes:
            bw = box["width"] * new_w
            bh = box["height"] * new_h
            cx = box["x_center"] * new_w + off_x
            cy = box["y_center"] * new_h + off_y
            x1, y1 = cx - bw / 2, cy - bh / 2
            x2, y2 = cx + bw / 2, cy + bh / 2
            draw.rectangle([x1, y1, x2, y2], outline=BOX_COLOR, width=BOX_WIDTH)

            if SHOW_CLASS_LABEL:
                text = str(box["class_name"])
                tx, ty = x1 + 2, max(0, y1 - 18)
                # 글자가 사진에 묻히지 않도록 뒤에 작은 띠를 깐다
                left, top, right, bottom = draw.textbbox((tx, ty), text, font=FONT_LABEL)
                draw.rectangle([left - 2, top - 1, right + 2, bottom + 1], fill=BOX_COLOR)
                draw.text((tx, ty), text, fill=(255, 255, 255), font=FONT_LABEL)

    # 아래쪽 이름 띠
    draw = ImageDraw.Draw(cell)
    draw.rectangle([0, CELL_IMG, CELL_IMG, CELL_IMG + CAPTION_H], fill=BG_COLOR)
    draw.text((8, CELL_IMG + 12), caption, fill=TEXT_COLOR, font=FONT_CAPTION)
    draw.rectangle([0, 0, CELL_IMG - 1, CELL_IMG + CAPTION_H - 1],
                   outline=(210, 210, 210), width=1)
    return cell


# ------------------------------------------------------------------ 시트 만들기

def build_sheets(split: str, boxes_by_image: dict, index_rows: list) -> int:
    """한 split 의 사진 전부를 16장씩 묶어 시트로 저장한다. 만든 시트 수를 돌려준다."""
    images = list_images(split)
    if not images:
        return 0

    sheet_w = GRID_COLS * CELL_IMG + (GRID_COLS + 1) * PAD
    sheet_h = GRID_ROWS * (CELL_IMG + CAPTION_H) + (GRID_ROWS + 1) * PAD

    sheet_count = 0
    for start in range(0, len(images), PER_SHEET):
        chunk = images[start:start + PER_SHEET]
        sheet_count += 1
        sheet_no = sheet_count
        sheet = Image.new("RGB", (sheet_w, sheet_h), BG_COLOR)

        for i, img_path in enumerate(chunk):
            cell_no = i + 1
            name = img_path.stem
            boxes = boxes_by_image.get((split, name), [])
            tag = f"{sheet_no:03d}-{cell_no:02d}"
            suffix = "  (라벨 없음)" if not boxes else ""
            caption = f"[{tag}] {name}{suffix}"

            cell = make_cell(img_path, boxes, caption)
            col, row = i % GRID_COLS, i // GRID_COLS
            x = PAD + col * (CELL_IMG + PAD)
            y = PAD + row * (CELL_IMG + CAPTION_H + PAD)
            sheet.paste(cell, (x, y))

            index_rows.append({
                "split": split,
                "sheet_file": f"{split}_sheet_{sheet_no:03d}.jpg",
                "tag": tag,
                "image_name": name,
                "box_count": len(boxes),
                "class_names": ", ".join(sorted({b["class_name"] for b in boxes})),
            })

        out_path = OUTPUT_DIR / f"{split}_sheet_{sheet_no:03d}.jpg"
        sheet.save(out_path, quality=JPEG_QUALITY)
        print(f"  저장 {out_path.name}  ({len(chunk)}장)")

    return sheet_count


# ------------------------------------------------------------------ 실행

def main():
    if not LABEL_CSV.exists():
        raise FileNotFoundError(
            f"파싱 CSV를 찾을 수 없습니다: {LABEL_CSV}\n"
            f'먼저 "scripts/labels_parsing(2.2).py" 를 실행하세요.'
        )

    print(f"사진 폴더 : {IMAGE_ROOT}")
    print(f"라벨 CSV  : {LABEL_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    boxes_by_image = load_boxes_by_image(LABEL_CSV)

    index_rows = []
    total_sheets = 0
    for split in SPLITS:
        print(f"\n[{split}]")
        total_sheets += build_sheets(split, boxes_by_image, index_rows)

    df_index = pd.DataFrame(index_rows)
    df_index.to_csv(OUTPUT_DIR / "grid_index.csv", index=False, encoding="utf-8-sig")

    print("\n" + "=" * 60)
    print(f"시트 {total_sheets}장, 사진 {len(df_index)}장")
    print(f"라벨 없는 사진: {int((df_index['box_count'] == 0).sum())}장")
    print(f"저장 위치: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
