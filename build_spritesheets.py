import argparse
import math
import re
from pathlib import Path

from PIL import Image


BASE_SHEET = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/rpg_base/Spritesheet/RPGpack_sheet.png")
BASE_TILES = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/rpg_base/PNG")
FALL_2D_TILES = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output/fall/2D")
FALL_2D_SHEETS = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output/fall/Spritesheet")
FALL_INT_2D_TILES = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/fall/2D")
FALL_INT_REAL_TILES = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/fall/real")
FALL_INT_SHEETS = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/fall/Spritesheet")
OUTPUT_INT_ROOT = Path("/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int")


def tile_index(path: Path):
    match = re.search(r"rpgTile(\d+)", path.stem)
    return int(match.group(1)) if match else path.stem


def sprite_suffix(path: Path):
    match = re.search(r"_stylized_([^.]+)$", path.stem)
    return match.group(1) if match else ""


def non_empty_positions(template_path: Path, tile_size=64):
    template = Image.open(template_path).convert("RGBA")
    positions = []
    for y in range(0, template.size[1], tile_size):
        for x in range(0, template.size[0], tile_size):
            cell = template.crop((x, y, x + tile_size, y + tile_size))
            if cell.getbbox() is not None:
                positions.append((x, y))
    return template.size, positions


def build_sheet(source_files, output_path, columns, rows=None):
    if not source_files:
        raise ValueError(f"합칠 이미지가 없습니다: {output_path}")

    ordered_files = sorted(source_files, key=tile_index)
    first = Image.open(ordered_files[0]).convert("RGBA")
    tile_width, tile_height = first.size
    rows = rows or math.ceil(len(ordered_files) / columns)

    # 원본 스프라이트시트와 같은 규칙으로 왼쪽에서 오른쪽, 위에서 아래 순서로 배치한다.
    sheet = Image.new("RGBA", (columns * tile_width, rows * tile_height), (0, 0, 0, 0))

    for idx, path in enumerate(ordered_files):
        tile = Image.open(path).convert("RGBA")
        x = (idx % columns) * tile_width
        y = (idx // columns) * tile_height
        sheet.paste(tile, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return output_path, sheet.size


def build_sheet_from_template_layout(source_files, output_path, template_path):
    if not source_files:
        raise ValueError(f"합칠 이미지가 없습니다: {output_path}")

    ordered_files = sorted(source_files, key=tile_index)
    template_size, positions = non_empty_positions(template_path)
    if len(ordered_files) != len(positions):
        raise ValueError(
            f"타일 개수와 템플릿 위치 수가 다릅니다: {len(ordered_files)} vs {len(positions)}"
        )

    sheet = Image.new("RGBA", template_size, (0, 0, 0, 0))
    for path, (x, y) in zip(ordered_files, positions):
        tile = Image.open(path).convert("RGBA")
        sheet.paste(tile, (x, y))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return output_path, sheet.size


def build_base_reference_sheet():
    base_files = sorted(BASE_TILES.glob("*.png"), key=tile_index)
    base_sheet = Image.open(BASE_SHEET)
    columns = base_sheet.size[0] // 64
    rows = base_sheet.size[1] // 64
    return build_sheet(base_files, BASE_SHEET.with_name("RPGpack_sheet_rebuilt.png"), columns, rows)


def build_fall_2d_sheets():
    fall_files = list(FALL_2D_TILES.glob("*.png"))
    grouped = {}
    for path in fall_files:
        grouped.setdefault(sprite_suffix(path), []).append(path)

    results = []
    base_sheet = Image.open(BASE_SHEET)
    columns = base_sheet.size[0] // 64
    rows = base_sheet.size[1] // 64
    for suffix, files in sorted(grouped.items()):
        output_path = FALL_2D_SHEETS / f"RPGpack_sheet_{suffix}.png"
        results.append(build_sheet(files, output_path, columns, rows))
    return results


def build_base_layout_sheet():
    base_files = sorted(BASE_TILES.glob("*.png"), key=tile_index)
    return build_sheet_from_template_layout(
        base_files,
        BASE_SHEET.with_name("RPGpack_sheet_layout.png"),
        BASE_SHEET,
    )


def build_fall_2d_layout_sheets():
    fall_files = list(FALL_2D_TILES.glob("*.png"))
    grouped = {}
    for path in fall_files:
        grouped.setdefault(sprite_suffix(path), []).append(path)

    results = []
    for suffix, files in sorted(grouped.items()):
        output_path = FALL_2D_SHEETS / f"RPGpack_sheet_{suffix}_layout.png"
        results.append(build_sheet_from_template_layout(files, output_path, BASE_SHEET))
    return results


def build_fall_interpolation_layout_sheets():
    results = []
    interpolation_sets = [
        ("2D", FALL_INT_2D_TILES, FALL_INT_SHEETS / "RPGpack_sheet_interp_2D_layout.png"),
        ("real", FALL_INT_REAL_TILES, FALL_INT_SHEETS / "RPGpack_sheet_interp_real_layout.png"),
    ]

    for _, tiles_dir, output_path in interpolation_sets:
        files = sorted(tiles_dir.glob("*.png"), key=tile_index)
        if not files:
            continue
        results.append(build_sheet_from_template_layout(files, output_path, BASE_SHEET))
    return results


def build_all_interpolation_layout_sheets():
    results = []
    for season in ("spring", "summer", "fall", "winter"):
        season_root = OUTPUT_INT_ROOT / season
        spritesheet_dir = season_root / "Spritesheet"
        for variant in ("2D", "real"):
            tiles_dir = season_root / variant
            files = sorted(tiles_dir.glob("*.png"), key=tile_index)
            if not files:
                continue
            output_path = spritesheet_dir / f"RPGpack_sheet_interp_{variant}_layout.png"
            results.append(build_sheet_from_template_layout(files, output_path, BASE_SHEET))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--rebuild-base",
        action="store_true",
        help="원본 PNG 폴더로부터 기준 스프라이트시트를 다시 생성",
    )
    args = parser.parse_args()

    if args.rebuild_base:
        output_path, size = build_base_reference_sheet()
        print(f"[done] base -> {output_path} {size}")
        output_path, size = build_base_layout_sheet()
        print(f"[done] base(layout) -> {output_path} {size}")

    for output_path, size in build_fall_2d_sheets():
        print(f"[done] fall/2D -> {output_path} {size}")
    for output_path, size in build_fall_2d_layout_sheets():
        print(f"[done] fall/2D(layout) -> {output_path} {size}")
    for output_path, size in build_all_interpolation_layout_sheets():
        print(f"[done] fall/interp(layout) -> {output_path} {size}")


if __name__ == "__main__":
    main()
