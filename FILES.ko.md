# pytorch-AdaIN 파일 안내

이 문서는 `pytorch-AdaIN` 폴더 안 주요 파일/폴더가 무엇을 의미하는지 정리한 안내서입니다.

## 루트 파일/폴더
- `.git/`: Git 버전 관리 메타데이터
- `.gitignore`: Git 추적 제외 규칙
- `LICENSE`: 오픈소스 라이선스 문서
- `README.md`: 원본 영어 사용 설명서
- `README.ko.md`: 한국어 사용 설명서
- `FILES.ko.md`: 현재 파일(구성 안내)
- `WORKLOG.ko.md`: 이번 작업 내용과 실행 결과를 정리한 문서
- `input/`: 입력 데이터 폴더
- `models/`: 사전학습 가중치 폴더
- `output/`: 개별 style 이미지 기준 AdaIN 결과 폴더
- `output_int/`: style interpolation 기준 AdaIN 결과 폴더

## 코드 파일
- `test.py`: 이미지 스타일 변환(추론) 메인 스크립트
- `test_video.py`: 비디오 스타일 변환 스크립트
- `train.py`: 모델 학습 스크립트
- `net.py`: 네트워크 구조(인코더/디코더 정의)
- `function.py`: AdaIN 핵심 함수 및 보조 함수
- `sampler.py`: 학습/데이터 샘플링 보조 코드
- `torch_to_pytorch.py`: Torch 모델을 PyTorch 형식으로 변환할 때 쓰는 스크립트
- `run_game_tile_seasons.py`: 계절별 style 폴더를 순회하며 기본 방식으로 추론하는 스크립트
- `run_game_tile_seasons_batched.py`: 계절별 style 폴더를 배치 추론으로 빠르게 처리하는 스크립트
- `run_game_tile_interpolation_batched.py`: 같은 style 폴더 안 여러 스타일을 interpolation 해서 결과를 만드는 스크립트
- `build_spritesheets.py`: 원본 RPGpack 배치에 맞춰 결과 타일을 스프라이트시트로 합치는 스크립트

## 데이터/모델/결과
### input
- `input/content/`: content 이미지 폴더
  - `input/content/game_tile/`: 게임 타일 content 이미지
  - `input/content/etc/`: 기타 content 이미지
- `input/style/`: style 이미지 폴더
  - `input/style/spring/`: 봄 스타일 이미지
  - `input/style/summer/`: 여름 스타일 이미지
  - `input/style/fall/`: 가을 스타일 이미지
  - `input/style/winter/`: 겨울 스타일 이미지
  - `input/style/etc/`: 기타 style 이미지
  - `input/mask/`: 마스크 샘플
  - `input/videos/`: 비디오 샘플

### models
- `models/`: 사전학습 가중치 저장 폴더
  - `decoder.pth`: 디코더 가중치
  - `vgg_normalised.pth`: VGG 인코더 가중치

### output
- `output/<season>/2D`, `output/<season>/real`: 개별 style 이미지 기준 결과
- `output/<season>/Spritesheet`: 개별 style 이미지 결과를 합친 스프라이트시트

### output_int
- `output_int/<season>/2D`, `output_int/<season>/real`: interpolation 결과
- `output_int/<season>/Spritesheet`: interpolation 결과를 합친 스프라이트시트

## 기타 파일
- `requirements.txt`: Python 의존성 목록(원본 저장소 기준)
- `results.png`: README에 쓰인 결과 예시 이미지

## 실행 흐름 요약
1. `models/`에 가중치(`decoder.pth`, `vgg_normalised.pth`) 준비
2. `run_game_tile_seasons_batched.py`로 계절별 개별 style 결과 생성
3. `run_game_tile_interpolation_batched.py`로 interpolation 결과 생성
4. `build_spritesheets.py`로 원본 RPGpack 배치에 맞는 스프라이트시트 생성
5. 세부 작업 내용은 `WORKLOG.ko.md` 참고
