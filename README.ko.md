# pytorch-AdaIN

이 저장소는 Huang 등(ICCV 2017)의 논문
"Arbitrary Style Transfer in Real-time with Adaptive Instance Normalization"의
비공식 PyTorch 구현입니다.

저자 분들의 Torch 원본 구현([AdaIN-style](https://github.com/xunhuang1995/AdaIN-style))을 많이 참고했고,
큰 도움을 받았습니다.

![Results](results.png)

## 요구 사항
아래 명령으로 의존성을 설치하세요.

```bash
pip install -r requirements.txt
```

- Python 3.5+
- PyTorch 0.4+
- TorchVision
- Pillow

(학습 시 선택)
- tqdm
- TensorboardX

## 사용 방법

### 모델 다운로드
[release](https://github.com/naoto0804/pytorch-AdaIN/releases/tag/v0.0.0)에서
`decoder.pth`, `vgg_normalised.pth`를 다운로드한 뒤 `models/` 아래에 넣으세요.

### 테스트
콘텐츠 이미지와 스타일 이미지를 각각 `--content`, `--style`로 지정합니다.

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> python test.py --content input/content/cornell.jpg --style input/style/woman_with_hat_matisse.jpg
```

`--content_dir`, `--style_dir`를 사용하면 폴더 단위로 모든 조합을 생성할 수 있습니다.

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> python test.py --content_dir input/content --style_dir input/style
```

아래는 `--style`과 `--style_interpolation_weights`를 이용해
4개 스타일을 혼합하는 예시입니다.

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> python test.py --content input/content/avril.jpg --style input/style/picasso_self_portrait.jpg,input/style/impronte_d_artista.jpg,input/style/trial.jpg,input/style/antimonocromatismo.jpg --style_interpolation_weights 1,1,1,1 --content_size 512 --style_size 512 --crop
```

기타 주요 옵션:
- `--content_size`: 콘텐츠 이미지 최소 크기(0이면 원본 유지)
- `--style_size`: 스타일 이미지 최소 크기(0이면 원본 유지)
- `--alpha`: 스타일 강도 조절(기본값 1.0, 범위 0.0~1.0)
- `--preserve_color`: 콘텐츠 이미지 색상 보존

### 게임 타일 계절별 배치 실행

이 저장소에는 게임 타일용 계절별 배치 실행 스크립트가 추가되어 있습니다.

- content 폴더: `input/content/game_tile`
- style 폴더: `input/style/spring`, `input/style/summer`, `input/style/fall`, `input/style/winter`
- 결과 폴더: `output/spring`, `output/summer`, `output/fall`, `output/winter`

기본 실행 스크립트:

```bash
python run_game_tile_seasons.py
```

더 빠른 배치 실행 스크립트:

```bash
python run_game_tile_seasons_batched.py --batch_size 1024
```

이 배치 스크립트는 다음을 보장하도록 구성되어 있습니다.

- output 이미지는 항상 원본 content와 같은 크기로 저장
- 계절 폴더 안의 `2D`, `real` 같은 하위 폴더 구조를 그대로 유지
- 이미 생성된 결과 파일은 건너뛰므로 중간에 멈춰도 이어서 실행 가능

예를 들어 아래와 같은 결과가 생성됩니다.

- `output/spring/2D/rpgTile000_stylized_sa1.png`
- `output/summer/real/rpgTile010_stylized_sr3.png`
- `output/fall/2D/rpgTile100_stylized_fa4.png`
- `output/winter/real/rpgTile220_stylized_wr5.png`

### 학습
콘텐츠/스타일 이미지 디렉터리를 지정해 학습합니다.

```bash
CUDA_VISIBLE_DEVICES=<gpu_id> python train.py --content_dir <content_dir> --style_dir <style_dir>
```

세부 파라미터는 `--help`를 참고하세요.

이 코드로 학습된 모델(`iter_1000000.pth`)은
[release](https://github.com/naoto0804/pytorch-AdaIN/releases/tag/v0.0.0)에서 제공합니다.

## 참고 문헌
- [1] X. Huang and S. Belongie. "Arbitrary Style Transfer in Real-time with Adaptive Instance Normalization.", ICCV, 2017.
- [2] [Torch 원본 구현](https://github.com/xunhuang1995/AdaIN-style)
