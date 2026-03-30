# AdaIN 작업 정리

## 목적

- `game_tile` content 이미지에 계절별 style 이미지를 적용해 AdaIN 결과를 생성
- 결과를 `output/spring`, `output/summer`, `output/fall`, `output/winter` 아래에 저장
- output 크기가 항상 원본 content 크기와 같도록 유지

## 이번에 한 작업

### 1. 코드 읽기 및 주석 보강

- [`train.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/train.py)
  - 학습 전처리, 데이터셋 로딩, 학습 루프, 체크포인트 저장 부분에 한국어 설명 주석 추가
- [`test.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/test.py)
  - 추론 전처리, AdaIN 적용, 결과 저장 흐름에 한국어 설명 주석 추가

### 2. 추론 코드 보완

- [`test.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/test.py)
  - content/style 이미지를 항상 `RGB`로 읽도록 수정
  - `RGBA` PNG 때문에 생기던 4채널 오류를 방지
  - 이미 생성된 output 파일이 있으면 해당 조합은 건너뛰도록 수정

### 3. 계절별 실행 스크립트 추가

- [`run_game_tile_seasons.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/run_game_tile_seasons.py)
  - `test.py`를 이용해 계절별 style 폴더를 순회하는 기본 실행 스크립트
  - `output/<계절>/<하위폴더>` 구조로 저장
  - `content_size=0`으로 고정해 output 크기를 content와 같게 유지

### 4. 고속 배치 실행 스크립트 추가

- [`run_game_tile_seasons_batched.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/run_game_tile_seasons_batched.py)
  - 모델을 한 번만 로드하고 여러 이미지에 대해 배치 추론
  - content 이미지를 메모리에 캐시
  - content feature를 미리 계산해 style마다 재사용
  - 이미 생성된 결과는 건너뛰도록 처리
  - 전체 계절 데이터 생성에 실제 사용한 스크립트

### 5. 스타일 interpolation 실행 스크립트 추가

- [`run_game_tile_interpolation_batched.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/run_game_tile_interpolation_batched.py)
  - 같은 폴더의 style 이미지들(`2D`, `real`)을 하나의 그룹으로 보고 interpolation 수행
  - style feature 자체가 아니라 style의 통계(mean/std)를 평균내는 방식으로 구현
  - 결과를 `output_int/<계절>/<하위폴더>`에 저장
  - 각 계절별로 `2D` 229장, `real` 229장씩 생성

### 6. 스프라이트시트 생성 스크립트 추가

- [`build_spritesheets.py`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/build_spritesheets.py)
  - 원본 `RPGpack_sheet.png`의 실제 타일 배치를 분석해 동일한 위치에 타일을 다시 배치
  - 개별 스타일 결과와 interpolation 결과를 스프라이트시트로 생성
  - `output_int/<계절>/Spritesheet` 아래에 계절별 `2D`, `real` 스프라이트시트 생성

## 실행 중 만난 문제와 해결

### 문제 1. style 폴더 안에 하위 폴더가 있음

- 원인: `spring/2D`, `spring/real`처럼 style 이미지가 하위 폴더에 들어 있었음
- 해결: 하위 폴더까지 순회하도록 실행 스크립트 수정

### 문제 2. PNG 일부가 RGBA 4채널 이미지였음

- 원인: AdaIN 모델은 3채널 RGB 입력을 기대함
- 해결: `Image.open(...).convert('RGB')`로 강제 변환

### 문제 3. 전체 조합 수가 많아 실행 시간이 김

- 원인: 계절 4개 × style 여러 장 × content 다수 조합
- 해결:
  - 배치 실행 스크립트 추가
  - content 텐서 캐시
  - content feature 캐시
  - 이미 생성된 결과 건너뛰기

### 문제 4. 스타일 이미지들의 크기가 서로 달라 interpolation이 바로 되지 않음

- 원인: `fa1~fa5` 같은 style 이미지들이 서로 다른 해상도를 가져 feature map 크기가 달랐음
- 해결:
  - style 이미지를 한 번에 stack하지 않고 개별 인코딩
  - feature map 자체 대신 style 통계(mean/std)를 평균내는 방식으로 interpolation 구현

### 문제 5. 원본 스프라이트시트와 단순 격자 배치가 다름

- 원인: `RPGpack_sheet.png`는 20열 순차 배치가 아니라 빈 칸을 포함한 고정 레이아웃을 사용함
- 해결:
  - 원본 시트의 비어 있지 않은 셀 좌표를 추출
  - stylized/interpolated 타일을 같은 좌표에 그대로 배치하는 `_layout` 스프라이트시트 생성

## 최종 결과

- [`output/spring`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output/spring): 2290개
- [`output/summer`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output/summer): 2290개
- [`output/fall`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output/fall): 2290개
- [`output/winter`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output/winter): 2290개
- [`output_int/spring`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/spring): 458개
- [`output_int/summer`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/summer): 458개
- [`output_int/fall`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/fall): 458개
- [`output_int/winter`](/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN/output_int/winter): 458개
- `output_int/<계절>/Spritesheet` 아래에 계절별 `RPGpack_sheet_interp_2D_layout.png`, `RPGpack_sheet_interp_real_layout.png` 생성

## 다시 실행할 때

가장 빠른 실행 방법:

```bash
cd "/mnt/c/Users/praisy/Desktop/26-1/캡스톤/AdaIN/pytorch-AdaIN"
./.venv/bin/python run_game_tile_seasons_batched.py --batch_size 1024
```

이 스크립트는 이미 만들어진 결과 파일은 건너뛰므로, 중간에 멈춰도 이어서 실행할 수 있다.

interpolation 결과 생성:

```bash
./.venv/bin/python run_game_tile_interpolation_batched.py
```

스프라이트시트 생성:

```bash
./.venv/bin/python build_spritesheets.py
```
