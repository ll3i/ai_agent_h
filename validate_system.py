#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
System Validation Script
시스템 환경 및 설정 검증
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_python_version():
    """Python 버전 확인"""
    print("✅ Python Version Check")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ Python 3.8+ required!")
        return False
    print("   ✅ OK\n")
    return True


def check_required_packages():
    """필수 패키지 확인"""
    print("✅ Required Packages Check")
    
    required = [
        'pandas',
        'numpy',
        'requests',
        'python-dotenv',
        'opencv-python',
        'pillow'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n   Install missing packages:")
        print(f"   pip install {' '.join(missing)}\n")
        return False
    
    print("   ✅ All required packages installed\n")
    return True


def check_project_structure():
    """프로젝트 구조 확인"""
    print("✅ Project Structure Check")
    
    required_files = [
        'run_agent.py',
        '.env',
        'data.csv',
        'requirements.txt',
        'DEVELOPMENT_PLAN.md',
        'README.md',
        'QUICKSTART.md'
    ]
    
    required_dirs = [
        'src',
        'data',
        'outputs',
        'logs',
        'notebooks'
    ]
    
    all_ok = True
    
    # 파일 확인
    for file in required_files:
        file_path = PROJECT_ROOT / file
        if file_path.exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - NOT FOUND")
            all_ok = False
    
    # 디렉토리 확인
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ❌ {dir_name}/ - NOT FOUND")
            all_ok = False
    
    if all_ok:
        print("   ✅ Project structure complete\n")
    else:
        print("   ⚠️  Some files/directories missing\n")
    
    return all_ok


def check_src_modules():
    """src 패키지 모듈 확인"""
    print("✅ Source Modules Check")
    
    required_modules = [
        'config.py',
        'image_processor.py',
        'saltlux_client.py',
        'vision_analyzer.py',
        'reasoner.py',
        'decision_maker.py',
        'verifier.py',
        'agent_core.py',
        'integrated_agent.py',
        'utils.py',
        '__init__.py'
    ]
    
    all_ok = True
    for module in required_modules:
        module_path = PROJECT_ROOT / 'src' / module
        if module_path.exists():
            print(f"   ✅ {module}")
        else:
            print(f"   ❌ {module} - NOT FOUND")
            all_ok = False
    
    if all_ok:
        print("   ✅ All modules present\n")
    else:
        print("   ⚠️  Some modules missing\n")
    
    return all_ok


def check_env_configuration():
    """환경 설정 확인"""
    print("✅ Environment Configuration Check")
    
    env_file = PROJECT_ROOT / '.env'
    if not env_file.exists():
        print("   ❌ .env file not found\n")
        return False
    
    print("   ✅ .env file exists")
    
    # .env 파일 내용 확인
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'SALTLUX_API_KEY=YOUR_API_KEY_HERE' in content:
        print("   ⚠️  SALTLUX_API_KEY not configured (still has default value)")
        print("      → Run 'python setup_env.py' to configure API key\n")
        return False
    elif 'SALTLUX_API_KEY=' in content:
        print("   ✅ SALTLUX_API_KEY configured\n")
        return True
    else:
        print("   ❌ SALTLUX_API_KEY not found in .env\n")
        return False


def check_data_files():
    """데이터 파일 확인"""
    print("✅ Data Files Check")
    
    data_csv = PROJECT_ROOT / 'data.csv'
    if data_csv.exists():
        print(f"   ✅ data.csv exists")
        
        # CSV 행 수 확인
        try:
            import pandas as pd
            df = pd.read_csv(data_csv)
            print(f"      Rows: {len(df)}")
            print(f"      Columns: {df.columns.tolist()}")
            
            if 'id' in df.columns and 'img_url' in df.columns:
                print(f"   ✅ Required columns present\n")
                return True
            else:
                print(f"   ❌ Missing required columns (id, img_url)\n")
                return False
        except Exception as e:
            print(f"   ❌ Error reading data.csv: {e}\n")
            return False
    else:
        print("   ❌ data.csv not found\n")
        return False


def main():
    """메인 검증"""
    print("\n" + "=" * 70)
    print("🔍 SYSTEM VALIDATION")
    print("=" * 70 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Project Structure", check_project_structure),
        ("Source Modules", check_src_modules),
        ("Environment Configuration", check_env_configuration),
        ("Data Files", check_data_files)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}: {e}\n")
            results.append((name, False))
    
    # 요약
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")
    
    print("=" * 70)
    print(f"Result: {passed}/{total} checks passed\n")
    
    if passed == total:
        print("✅ System is ready! You can run: python run_agent.py")
        return 0
    else:
        print("⚠️  Please fix the failed checks above before running the agent.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
