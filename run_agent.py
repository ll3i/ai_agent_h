#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manufacturing AI Agent - Main Execution Script
제조공정 이미지 분류 AI Agent 실행 파일
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 작업 디렉토리 변경
os.chdir(PROJECT_ROOT)

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# 프로젝트 모듈 임포트
from src.integrated_agent import main

if __name__ == "__main__":
    try:
        print("Manufacturing AI Agent Starting...")
        print("=" * 70)
        main()
        print("=" * 70)
        print("All tasks completed successfully!")
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
