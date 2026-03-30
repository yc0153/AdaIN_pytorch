import argparse
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.utils import save_image

import net
from function import calc_mean_std


SEASONS = ("spring", "summer", "fall", "winter")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def style_transfer_from_blended_stats(decoder, content_f, style_mean, style_std, alpha=1.0):
    # 여러 스타일의 통계(mean/std)를 평균 내서 AdaIN을 적용한다.
    content_mean, content_std = calc_mean_std(content_f)
    normalized = (content_f - content_mean.expand(content_f.size())) / content_std.expand(content_f.size())
    feat = normalized * style_std.expand(content_f.size()) + style_mean.expand(content_f.size())
    feat = feat * alpha + content_f * (1 - alpha)
    return decoder(feat)


def collect_style_dirs(season_style_root: Path):
    # 이미지가 실제로 들어 있는 하위 폴더만 대상으로 삼는다.
    style_dirs = []
    for path in sorted(season_style_root.rglob("*")):
        if not path.is_dir():
            continue
        if any(child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES for child in path.iterdir()):
            style_dirs.append(path)
    return style_dirs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--content_dir", type=Path, default=Path("input/content/game_tile"))
    parser.add_argument("--style_root", type=Path, default=Path("input/style"))
    parser.add_argument("--output_root", type=Path, default=Path("output_int"))
    parser.add_argument("--vgg", type=Path, default=Path("models/vgg_normalised.pth"))
    parser.add_argument("--decoder", type=Path, default=Path("models/decoder.pth"))
    parser.add_argument("--style_size", type=int, default=512)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--save_ext", type=str, default=".png")
    parser.add_argument("--batch_size", type=int, default=1024)
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

    # content 타일을 한 번만 읽고 재사용한다.
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

    # content feature를 미리 계산해 style 그룹마다 재사용한다.
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

    # 계절별 폴더 안의 style 그룹(예: 2D, real)을 하나의 interpolation 그룹으로 본다.
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
            if not style_paths:
                continue

            # 같은 폴더의 style 이미지를 하나씩 인코딩한 뒤 mean/std를 동일 가중치로 평균낸다.
            with torch.no_grad():
                style_means = []
                style_stds = []
                for path in style_paths:
                    style_tensor = style_tf(Image.open(str(path)).convert("RGB")).unsqueeze(0).to(device)
                    style_feature = vgg(style_tensor)
                    style_mean, style_std = calc_mean_std(style_feature)
                    style_means.append(style_mean.cpu())
                    style_stds.append(style_std.cpu())
                blended_style_mean = torch.stack(style_means, dim=0).mean(dim=0)
                blended_style_std = torch.stack(style_stds, dim=0).mean(dim=0)

            for start in range(0, len(content_paths), args.batch_size):
                batch_paths = content_paths[start:start + args.batch_size]
                pending_indices = [
                    idx for idx, path in enumerate(batch_paths, start=start)
                    if not (output_dir / f"{path.stem}_stylized_interp{args.save_ext}").exists()
                ]
                if not pending_indices:
                    continue

                pending_paths = [content_paths[idx] for idx in pending_indices]
                content_feature_batch = content_features[pending_indices].to(device)
                style_mean_batch = blended_style_mean.expand(content_feature_batch.size(0), -1, -1, -1).to(device)
                style_std_batch = blended_style_std.expand(content_feature_batch.size(0), -1, -1, -1).to(device)

                with torch.no_grad():
                    output_batch = style_transfer_from_blended_stats(
                        decoder,
                        content_feature_batch,
                        style_mean_batch,
                        style_std_batch,
                        args.alpha,
                    ).cpu()

                for idx, content_path in enumerate(pending_paths):
                    output_name = output_dir / f"{content_path.stem}_stylized_interp{args.save_ext}"
                    save_image(output_batch[idx], str(output_name))

            print(f"[done] {season}/{relative_dir} <- {len(style_paths)} styles interpolated")


if __name__ == "__main__":
    main()
