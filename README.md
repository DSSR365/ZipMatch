# 🚀 ZipMatch v1.0
> **멀티스레드 기반 고속 이미지 및 ZIP 파일 중복 탐색기**

파이썬 `Tkinter`를 활용해 제작한 독립형 GUI 유틸리티 프로그램입니다. 일반 폴더뿐만 아니라 ZIP 압축 파일 내부까지 초고속으로 탐색하여 유사도가 높은 이미지 복사본을 찾아냅니다. 컴퓨터의 잠자는 용량을 확보하고 중복 이미지를 효율적으로 정리할 수 있습니다.

---

## ✨ 핵심 기능 (Key Features)

- **🏎️ 초고속 병렬 분석:** `ThreadPoolExecutor`를 활용한 멀티스레딩 엔진 탑재로 대용량 파일도 버벅임 없이 고속 대조
- **📦 ZIP 내부 가상 탐색:** 압축을 매번 풀지 않고도 ZIP 파일 내부의 이미지 파일들을 다이렉트로 매칭 및 인덱싱
- **👁️ 실시간 비주얼 뷰어:** 판정된 중복 목록을 마우스로 클릭하면 우측 미리보기 뷰어를 통해 즉시 시각적 비교 가능
- **🎨 사용자 정의 멀티 테마:** 눈이 편안한 `🌙 다크 모드`, 화사한 `✨ 모던 화이트`, 차분한 `🌿 에메랄드 그린` 실시간 테마 스위칭 지원
- **🛡️ 프로덕션 레벨 로그 시스템:** 배포 후 예기치 못한 에러 발생 시 자동 로그 파일(`duplicate_finder_debug.log`)을 생성하여 유지보수 편의성 극대화
- **🗑️ 원클릭 안전 삭제:** 중복 판정된 일반 파일을 프로그램 내부에서 팝업 확인 후 즉시 영구 삭제 가능

---

## 🛠️ 기술 스택 (Tech Stack)

- **Language:** Python 3.14+
- **GUI Framework:** Tkinter (Tcl/Tk)
- **Image Processing:** Pillow (PIL)
- **Hashing Engine:** ImageHash (pHash - Perceptual Hashing)
- **Concurrency:** Concurrent.futures (ThreadPoolExecutor)
- **Executable Compiler:** PyInstaller

---

## 🚀 시작하기 (Getting Started)

### 1. 개발 환경에서 실행 시 (Source Code)
필수 라이브러리를 설치한 후 메인 스크립트를 실행합니다.

```bash
# 필수 외부 패키지 설치
pip install Pillow imagehash pyinstaller

# 프로그램 가동
python "file scan.py"
