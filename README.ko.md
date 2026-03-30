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

## 실행 파일 설명

이 문서는 현재 프로젝트에서 `결과 이미지가 만들어지기까지` 어떤 파일이 어떤 역할을 하는지 중심으로 정리한 설명서입니다.

### 전체 흐름

1. `models/`에서 사전학습 가중치(`vgg_normalised.pth`, `decoder.pth`)를 읽는다.
2. `test.py`가 content 이미지와 style 이미지를 받아 AdaIN 스타일 전이를 수행한다.
3. 여러 이미지를 한꺼번에 처리할 때는 `run_game_tile_seasons_batched.py` 또는 `run_game_tile_interpolation_batched.py`가 이 과정을 자동 반복한다.
4. 결과는 `output/` 또는 `output_int/`에 저장된다.
5. 필요하면 `build_spritesheets.py`가 결과 타일을 원본 RPGpack 배치에 맞는 스프라이트시트로 합친다.

### 핵심 추론 파일

#### `test.py`

- 실제 AdaIN 스타일 전이를 수행하는 메인 추론 파일
- content 이미지와 style 이미지를 읽는다
- 이미지를 전처리한 뒤 VGG 인코더와 디코더를 로드한다
- content feature와 style feature를 계산한다
- AdaIN 연산으로 style 통계를 content feature에 적용한다
- 디코더로 결과 이미지를 복원하고 저장한다

즉, `결과 한 장을 실제로 만들어내는 중심 파일`이 `test.py`이다.

#### `net.py`

- VGG 인코더와 디코더 구조를 정의하는 파일
- 학습용 `Net` 클래스도 포함되어 있다
- `test.py`와 `train.py`가 여기서 모델 구조를 가져다 쓴다

즉, `모델 모양 자체`는 `net.py`에 들어 있다.

#### `function.py`

- AdaIN 핵심 함수들이 들어 있는 파일
- `adaptive_instance_normalization()`이 가장 중요한 함수이다
- interpolation 구현에서 사용하는 `calc_mean_std()`도 여기에 있다

즉, `스타일을 어떻게 섞을지 계산하는 수학적 핵심`이 `function.py`에 있다.

### 가중치 파일

#### `models/decoder.pth`

- 디코더 가중치 파일
- feature를 다시 RGB 이미지로 복원할 때 사용

#### `models/vgg_normalised.pth`

- VGG 인코더 가중치 파일
- content와 style 이미지를 feature 공간으로 바꿀 때 사용

즉, `모델이 실제로 동작하려면 models 폴더의 두 파일이 먼저 준비되어 있어야 한다`.

### 대량 실행용 파일

#### `run_game_tile_seasons_batched.py`

- `input/content/game_tile`의 타일 이미지를 읽는다
- `input/style/spring`, `summer`, `fall`, `winter`를 계절별로 순회한다
- 모델을 한 번만 메모리에 올리고 content feature를 캐시한다
- 개별 style 이미지 기준 결과를 빠르게 대량 생성한다
- 결과는 `output/<season>/<2D|real>` 등에 저장된다

즉, `계절별 개별 스타일 결과를 대량으로 생성할 때 쓰는 메인 실행 파일`이다.

#### `run_game_tile_interpolation_batched.py`

- 같은 style 폴더 안의 여러 style 이미지를 하나의 그룹으로 본다
- 예를 들어 `fa1~fa5`를 따로 쓰지 않고 하나의 interpolation 결과로 만든다
- style feature 자체가 아니라 style 통계(mean/std)를 평균내는 방식으로 interpolation 한다
- 결과는 `output_int/<season>/<2D|real>`에 저장된다

즉, `여러 스타일을 섞은 결과를 만들 때 쓰는 파일`이다.

#### `run_game_tile_seasons.py`

- `test.py`를 반복 호출하는 기본형 실행 스크립트
- 구조는 단순하지만 속도는 batched 버전보다 느리다

즉, `개념적으로 가장 단순한 계절별 반복 실행 스크립트`이다.

### 결과 정리 파일

#### `build_spritesheets.py`

- stylized/interpolated 타일들을 다시 한 장의 스프라이트시트로 합친다
- 원본 `RPGpack_sheet.png`의 실제 타일 위치를 읽어 같은 배치로 붙인다
- 단순 격자 배치가 아니라 원본과 같은 레이아웃의 `_layout.png` 파일을 만든다
- `output/<season>/Spritesheet`, `output_int/<season>/Spritesheet` 아래 결과를 생성한다

즉, `게임에서 바로 보기 좋은 시트 형태로 결과를 정리하는 파일`이다.

### 학습 관련 파일

#### `train.py`

- AdaIN 디코더를 학습하거나 파인튜닝할 때 사용하는 파일
- content/style 데이터셋을 읽고 손실을 계산한다
- 체크포인트를 저장한다

즉, `지금 결과 생성 과정에는 직접 쓰이지 않았지만 학습용으로 필요한 파일`이다.

#### `sampler.py`

- 학습 중 DataLoader가 무한 샘플링되도록 돕는 보조 파일

즉, `train.py`가 배치를 계속 받아오도록 도와주는 파일`이다.

### 입력/출력 폴더

#### `input/`

- `input/content/game_tile/`: 게임 타일 content 이미지
- `input/style/spring/`, `summer/`, `fall/`, `winter/`: 계절별 style 이미지

#### `output/`

- 개별 style 이미지 기준 AdaIN 결과가 저장되는 폴더

#### `output_int/`

- style interpolation 결과가 저장되는 폴더

### 정리

가장 핵심은 아래처럼 보면 된다.

- `test.py`: 실제 스타일 전이 실행
- `net.py`: 모델 구조 정의
- `function.py`: AdaIN 연산 정의
- `run_game_tile_seasons_batched.py`: 개별 스타일 대량 생성
- `run_game_tile_interpolation_batched.py`: interpolation 결과 대량 생성
- `build_spritesheets.py`: 결과를 스프라이트시트로 합침

한 줄로 정리하면, `test.py가 엔진이고, run_game_tile_* 파일들이 대량 실행을 맡으며, build_spritesheets.py가 최종 결과를 게임용 시트로 정리한다`고 이해하면 된다.

## 참고 문헌
- [1] X. Huang and S. Belongie. "Arbitrary Style Transfer in Real-time with Adaptive Instance Normalization.", ICCV, 2017.
- [2] [Torch 원본 구현](https://github.com/xunhuang1995/AdaIN-style)
