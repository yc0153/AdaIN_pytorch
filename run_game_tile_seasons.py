import argparse
import subprocess
import sys
from pathlib import Path


SEASONS = ("spring", "summer", "fall", "winter")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main():
    # 계절별 style 폴더와 output 폴더를 지정할 수 있도록 실행 인자를 받는다.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--content_dir",
        type=Path,
        default=Path("input/content/game_tile"),
        help="게임 타일 content 이미지 폴더",
    )
    parser.add_argument(
        "--style_root",
        type=Path,
        default=Path("input/style"),
        help="계절별 style 폴더의 상위 경로",
    )
    parser.add_argument(
        "--output_root",
        type=Path,
        default=Path("output"),
        help="계절별 결과를 저장할 상위 경로",
    )
    parser.add_argument(
        "--style_size",
        type=int,
        default=512,
        help="style 이미지 리사이즈 크기, 0이면 원본 유지",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=1.0,
        help="스타일 강도",
    )
    parser.add_argument(
        "--save_ext",
        type=str,
        default=".png",
        help="결과 이미지 확장자",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    content_dir = (project_root / args.content_dir).resolve()
    style_root = (project_root / args.style_root).resolve()
    output_root = (project_root / args.output_root).resolve()
    test_script = project_root / "test.py"

    if not content_dir.exists():
        raise FileNotFoundError(f"content 폴더를 찾을 수 없습니다: {content_dir}")

    # spring/summer/fall/winter 순서로 각 계절 폴더를 순회한다.
    for season in SEASONS:
        season_style_root = style_root / season
        season_output_root = output_root / season

        if not season_style_root.exists():
            print(f"[skip] style 폴더가 없어 건너뜁니다: {season_style_root}")
            continue

        # 계절 폴더 안의 하위 디렉터리까지 찾아 style 이미지가 있는 폴더만 처리한다.
        style_dirs = [p for p in sorted(season_style_root.rglob("*")) if p.is_dir()]
        image_files = [p for p in sorted(season_style_root.rglob("*")) if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]

        if image_files and not style_dirs:
            style_dirs = [season_style_root]

        for style_dir in style_dirs:
            has_images = any(
                p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
                for p in style_dir.iterdir()
            )
            if not has_images:
                continue

            # output도 style 폴더 구조를 그대로 따라가게 만든다.
            relative_dir = style_dir.relative_to(season_style_root)
            output_dir = season_output_root / relative_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # content_size=0 으로 고정해 출력 크기를 항상 원본 content와 같게 유지한다.
            cmd = [
                sys.executable,
                str(test_script),
                "--content_dir",
                str(content_dir),
                "--style_dir",
                str(style_dir),
                "--content_size",
                "0",
                "--style_size",
                str(args.style_size),
                "--alpha",
                str(args.alpha),
                "--save_ext",
                args.save_ext,
                "--output",
                str(output_dir),
            ]

            print(f"[run] {season}/{relative_dir}: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, cwd=project_root)


if __name__ == "__main__":
    main()
