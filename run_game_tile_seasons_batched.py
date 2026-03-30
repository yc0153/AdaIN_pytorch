import argparse
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.utils import save_image

import net
from function import adaptive_instance_normalization


SEASONS = ("spring", "summer", "fall", "winter")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def style_transfer_from_features(decoder, content_f, style_f, alpha=1.0):
    # 이미 추출된 content/style feature에서 AdaIN을 적용한 뒤 디코더로 복원한다.
    feat = adaptive_instance_normalization(content_f, style_f)
    feat = feat * alpha + content_f * (1 - alpha)
    return decoder(feat)


def collect_style_dirs(season_style_root: Path):
    # 이미지 파일이 실제로 들어 있는 style 하위 폴더만 수집한다.
    style_dirs = []
    for path in sorted(season_style_root.rglob("*")):
        if not path.is_dir():
            continue
        if any(
            child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES
            for child in path.iterdir()
        ):
            style_dirs.append(path)
    if not style_dirs and any(
        child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES
        for child in season_style_root.iterdir()
    ):
        style_dirs.append(season_style_root)
    return style_dirs


def main():
    # 기본 경로와 실행 옵션을 인자로 받아 재사용 가능하게 만든다.
    parser = argparse.ArgumentParser()
    parser.add_argument("--content_dir", type=Path, default=Path("input/content/game_tile"))
    parser.add_argument("--style_root", type=Path, default=Path("input/style"))
    parser.add_argument("--output_root", type=Path, default=Path("output"))
    parser.add_argument("--vgg", type=Path, default=Path("models/vgg_normalised.pth"))
    parser.add_argument("--decoder", type=Path, default=Path("models/decoder.pth"))
    parser.add_argument("--style_size", type=int, default=512)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--save_ext", type=str, default=".png")
    parser.add_argument("--batch_size", type=int, default=64)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    content_dir = (project_root / args.content_dir).resolve()
    style_root = (project_root / args.style_root).resolve()
    output_root = (project_root / args.output_root).resolve()

    content_paths = sorted(
        p for p in content_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
    )
    if not content_paths:
        raise FileNotFoundError(f"content 이미지가 없습니다: {content_dir}")

    # content 타일은 모두 같은 크기이므로 한 번만 메모리에 올려 재사용한다.
    content_tensor = torch.stack([
        transforms.ToTensor()(Image.open(str(path)).convert("RGB"))
        for path in content_paths
    ])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    decoder = net.decoder
    vgg = net.vgg
    decoder.eval()
    vgg.eval()

    decoder.load_state_dict(torch.load(project_root / args.decoder, map_location=device))
    vgg.load_state_dict(torch.load(project_root / args.vgg, map_location=device))
    vgg = nn.Sequential(*list(vgg.children())[:31])

    decoder.to(device)
    vgg.to(device)

    # content feature를 한 번만 계산해 스타일마다 다시 인코딩하지 않도록 캐시한다.
    with torch.no_grad():
        content_features = []
        for start in range(0, len(content_paths), args.batch_size):
            content_batch = content_tensor[start:start + args.batch_size].to(device)
            content_features.append(vgg(content_batch).cpu())
        content_features = torch.cat(content_features, dim=0)

    style_tf = transforms.Compose([
        transforms.Resize(args.style_size) if args.style_size != 0 else transforms.Lambda(lambda x: x),
        transforms.ToTensor(),
    ])

    # 계절별 -> style 하위폴더별 -> style 이미지별 순서로 결과를 생성한다.
    for season in SEASONS:
        season_style_root = style_root / season
        if not season_style_root.exists():
            print(f"[skip] missing season style root: {season_style_root}")
            continue

        for style_dir in collect_style_dirs(season_style_root):
            relative_dir = style_dir.relative_to(season_style_root)
            output_dir = output_root / season / relative_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            style_paths = sorted(
                p for p in style_dir.iterdir()
                if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
            )

            for style_path in style_paths:
                # style 이미지는 한 장씩 인코딩하고, 같은 style feature를 배치 전체에 재사용한다.
                style_tensor = style_tf(Image.open(str(style_path)).convert("RGB")).unsqueeze(0).to(device)
                with torch.no_grad():
                    style_feature = vgg(style_tensor).cpu()

                for start in range(0, len(content_paths), args.batch_size):
                    batch_paths = content_paths[start:start + args.batch_size]
                    # 이미 만들어진 결과는 건너뛰어서 중간에 멈춰도 이어서 실행할 수 있게 한다.
                    pending_indices = [
                        idx for idx, path in enumerate(batch_paths, start=start)
                        if not (output_dir / f"{path.stem}_stylized_{style_path.stem}{args.save_ext}").exists()
                    ]
                    pending = [content_paths[idx] for idx in pending_indices]
                    if not pending:
                        continue

                    content_feature_batch = content_features[pending_indices].to(device)
                    style_feature_batch = style_feature.expand(content_feature_batch.size(0), -1, -1, -1).to(device)

                    with torch.no_grad():
                        output_batch = style_transfer_from_features(
                            decoder,
                            content_feature_batch,
                            style_feature_batch,
                            args.alpha,
                        ).cpu()

                    for idx, content_path in enumerate(pending):
                        output_name = output_dir / f"{content_path.stem}_stylized_{style_path.stem}{args.save_ext}"
                        save_image(output_batch[idx], str(output_name))

                # 어떤 style 이미지까지 처리가 끝났는지 로그로 남긴다.
                print(f"[done] {season}/{relative_dir} <- {style_path.name}")


if __name__ == "__main__":
    main()
