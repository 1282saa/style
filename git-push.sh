#!/bin/bash

# 깃 초기화
git init

# 모든 파일 스테이징
git add .

# 첫 커밋 생성
git commit -m "Initial commit: 스타일북 MCP 서버"

# 원격 저장소 연결
git remote add origin git@github.com:1282saa/style.git

# 원격 저장소에 푸시
git push -u origin main

echo "깃허브 푸시가 완료되었습니다." 