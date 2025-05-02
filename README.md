# 스타일북 MCP 서버

서울경제신문 기자들을 위한 스타일북 교열 MCP 서버입니다. Claude Desktop과 연동하여 문장 교정 작업을 지원합니다.

## 주요 기능

1. **단어/표현 검색** (`search-stylebook`): 스타일북에서 특정 어휘나 표현에 대한 정보를 검색합니다.
2. **문장 교정 검사** (`check-sentence`): 문장을 입력받아 스타일북 규칙에 따라 교정 제안을 제공합니다.
3. **섹션 목록 조회** (`list-sections`): 스타일북의 모든 섹션 목록을 가져옵니다.

## 파일 구조

- `mcp_server.py`: MCP 서버 코드 (stdio 통신)
- `app.py`: Flask 웹 서버 (HTTP API 제공)
- `Dockerfile`: 컨테이너 이미지 설정
- `requirements.txt`: 필요한 패키지 의존성
- `7_2자주 틀리는 말01.json`: 스타일북 데이터
- `claude-desktop-tools.json`: Claude Desktop 연동 설정

## 스미더리 배포 방법

1. 깃허브에 코드 푸시

```bash
git init
git add .
git commit -m "Initial commit: 스타일북 MCP 서버"
git remote add origin git@github.com:1282saa/style.git
git push -u origin main
```

2. 스미더리 배포

   - 스미더리 계정으로 로그인
   - 새 프로젝트 생성
   - 깃허브 저장소 연결 (https://github.com/1282saa/style)
   - 배포 설정 (포트: 8080)
   - 배포 시작

3. 배포 후 설정
   - 배포된 URL을 확인
   - `claude-desktop-tools.json` 파일의 URL 값을 실제 배포 URL로 업데이트
   - 업데이트된 파일을 기자들에게 공유

## Claude Desktop 설정 방법

1. `claude-desktop-tools.json` 파일을 다음 경로에 저장:

   - Windows: `%APPDATA%\Claude\claude-desktop-tools.json`
   - macOS: `~/Library/Application Support/Claude/claude-desktop-tools.json`

2. Claude Desktop을 실행하여 도구 사용 가능 여부 확인

## 로컬 개발 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# MCP 서버 실행 (stdio 통신)
python mcp_server.py

# Flask 웹 서버 실행 (HTTP API)
python app.py
```
