"""
Configuration Management
프로젝트 설정 및 환경 변수 관리
"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class Config:
    """프로젝트 설정 클래스"""
    
    # 기본 경로
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DEV_DATA_DIR = DATA_DIR / "dev"
    TEST_DATA_DIR = DATA_DIR / "test"
    OUTPUT_DIR = PROJECT_ROOT / "outputs"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # API 설정
    SALTLUX_API_KEY = os.getenv('SALTLUX_API_KEY', 'your_api_key_here')
    SALTLUX_API_BASE_URL = os.getenv('SALTLUX_API_BASE_URL', 'https://api.luxiaplatform.com/v1')
    SALTLUX_API_TIMEOUT = 30  # seconds
    SALTLUX_MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # ======= 다중 모델 설정 (Luxia Platform) =======
    # https://platform.luxiacloud.com/docs/chat 의 사용 가능한 모델들
    LUXIA_MODELS = {
        # Judge (관찰) - 이미지 분석에 최적화 (Luxia 최신)
        'judge': 'luxia3-llm-32b-0731',  # 최고 성능, 상세 분석
        
        # Think (추론) - 복잡한 분석에 최적화 (Luxia 최신)
        'think': 'luxia3-llm-32b-0731',  # 깊이 있는 추론, 도메인 분석
        
        # Act (의사결정) - 빠른 판단 (Luxia 고성능)
        'act': 'luxia3-llm-13b-0731',  # 빠른 응답, 정확한 판단
        
        # Verify (검증) - 최종 확인 (Luxia 최고 성능)
        'verify': 'luxia3-llm-32b-0731',  # 강력한 분석, 최종 판단
    }
    
    # 모델별 특성 및 최적화 설정
    MODEL_PROFILES = {
        'judge': {
            'purpose': 'Detailed Vision Analysis (상세 이미지 분석)',
            'capabilities': ['detailed_analysis', 'korean_optimized', 'technical_description'],
            'cost_level': 'medium',
            'response_time': 'fast',
            'reasoning_depth': 'detailed'
        },
        'think': {
            'purpose': 'Deep Reasoning & Domain Analysis (깊이 있는 추론)',
            'capabilities': ['extended_thinking', 'domain_knowledge', 'root_cause_analysis'],
            'cost_level': 'medium',
            'response_time': 'fast',
            'reasoning_depth': 'very_deep'
        },
        'act': {
            'purpose': 'Fast Decision Making (빠른 의사결정)',
            'capabilities': ['json_output', 'rule_application', 'confidence_scoring'],
            'cost_level': 'low',
            'response_time': 'very_fast',
            'reasoning_depth': 'minimal'
        },
        'verify': {
            'purpose': 'Final Verification & Confirmation (최종 검증)',
            'capabilities': ['detailed_analysis', 'deep_reasoning', 'confidence_recalculation'],
            'cost_level': 'medium',
            'response_time': 'fast',
            'reasoning_depth': 'very_deep'
        }
    }
    
    # Luxia 지원 모델 전체 목록
    AVAILABLE_MODELS = [
        # Luxia 최신 모델 (한국어 최적화)
        'luxia3-llm-32b-0731',   # 32B, 최고 성능
        'luxia3-llm-13b-0731',   # 13B, 고성능
        'luxia3-llm-8b-0731',    # 8B, 기본
        
        # OpenAI Models
        'gpt-4o-2024-11-20',
        'gpt-4o-2024-08-06',
        'gpt-4o-2024-05-13',
        'gpt-4o-mini-2024-07-18',
        'gpt-4-turbo',
        'gpt-4-turbo-2024-04-09',
        'gpt-3.5-turbo',
        
        # Claude Models
        'claude-3.5-sonnet',
        'claude-3-opus',
        'claude-3-sonnet',
        'claude-3-haiku',
    ]
    
    # 프로젝트 설정
    PROJECT_NAME = os.getenv('PROJECT_NAME', 'Manufacturing_AI_Agent')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Agent 설정
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.85'))
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '5'))
    MAX_AGENT_ITERATIONS = 3  # Agent 최대 반복 횟수
    
    # 이미지 처리 설정
    IMAGE_SIZE = int(os.getenv('IMAGE_SIZE', '224'))
    IMAGE_QUALITY = int(os.getenv('IMAGE_QUALITY', '95'))
    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    
    # 출력 설정
    OUTPUT_CSV_FILENAME = 'output.csv'
    RESULTS_CSV_ENCODING = 'utf-8'
    
    # 분류 레이블
    CLASS_LABELS = {
        0: 'Normal',
        1: 'Abnormal'
    }
    REVERSE_LABELS = {
        'Normal': 0,
        'Abnormal': 1,
        'normal': 0,
        'abnormal': 1
    }
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """설정값 조회"""
        return getattr(cls, key, default)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        config_dict = {}
        for attr in dir(cls):
            if not attr.startswith('_') and attr.isupper():
                config_dict[attr] = getattr(cls, attr)
        return config_dict
    
    @classmethod
    def validate(cls) -> bool:
        """설정 유효성 검증"""
        errors = []
        
        # API 키 확인
        if cls.SALTLUX_API_KEY == 'your_api_key_here':
            errors.append("SALTLUX_API_KEY is not set. Please configure .env file.")
        
        # 필수 디렉토리 확인
        required_dirs = [cls.OUTPUT_DIR, cls.LOGS_DIR]
        for dir_path in required_dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # 데이터 디렉토리 확인
        if not cls.DEV_DATA_DIR.exists():
            errors.append(f"Development data directory not found: {cls.DEV_DATA_DIR}")
        
        if errors:
            for error in errors:
                print(f"⚠️  {error}")
            return False
        
        return True


if __name__ == '__main__':
    # 설정 검증 테스트
    print("🔧 Configuration:")
    print(f"  Project Root: {Config.PROJECT_ROOT}")
    print(f"  Data Dir: {Config.DATA_DIR}")
    print(f"  Output Dir: {Config.OUTPUT_DIR}")
    print(f"  Confidence Threshold: {Config.CONFIDENCE_THRESHOLD}")
    print(f"  Batch Size: {Config.BATCH_SIZE}")
    print(f"\n✅ Configuration loaded successfully!")
