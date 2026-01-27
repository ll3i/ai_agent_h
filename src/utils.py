"""
Utilities Module
공용 유틸리티 함수 모음
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def setup_logging(log_dir: Union[str, Path], level: str = 'INFO') -> None:
    """
    로깅 설정
    
    Args:
        log_dir: 로그 디렉토리
        level: 로그 레벨
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Logging initialized: {log_file}")


def save_results_to_csv(results: List[Dict[str, Any]], 
                        output_path: Union[str, Path],
                        encoding: str = 'utf-8') -> bool:
    """
    결과를 CSV 파일로 저장
    
    Args:
        results: 결과 리스트 [{'image_name': '...', 'prediction': 0, ...}, ...]
        output_path: 저장 경로
        encoding: 인코딩 (UTF-8 필수)
        
    Returns:
        성공 여부
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False, encoding=encoding)
        
        logger.info(f"Results saved to {output_path} ({len(df)} rows)")
        return True
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        return False


def load_results_from_csv(file_path: Union[str, Path],
                         encoding: str = 'utf-8') -> pd.DataFrame:
    """
    CSV 파일에서 결과 로드
    
    Args:
        file_path: 파일 경로
        encoding: 인코딩
        
    Returns:
        데이터프레임
    """
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        logger.info(f"Loaded results from {file_path} ({len(df)} rows)")
        return df
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return pd.DataFrame()


def calculate_metrics(predictions: List[int], 
                      ground_truth: List[int]) -> Dict[str, float]:
    """
    분류 성능 지표 계산 (Precision, Recall, F1-Score)
    
    Args:
        predictions: 예측값 리스트 [0, 1, 1, 0, ...]
        ground_truth: 실제값 리스트
        
    Returns:
        {precision, recall, f1_score, accuracy} 딕셔너리
    """
    from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
    
    try:
        metrics = {
            'precision': precision_score(ground_truth, predictions, zero_division=0),
            'recall': recall_score(ground_truth, predictions, zero_division=0),
            'f1_score': f1_score(ground_truth, predictions, zero_division=0),
            'accuracy': accuracy_score(ground_truth, predictions)
        }
        return metrics
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        return {}


def print_metrics(metrics: Dict[str, float]) -> None:
    """
    메트릭 출력
    
    Args:
        metrics: 메트릭 딕셔너리
    """
    print("\n" + "="*50)
    print("📊 PERFORMANCE METRICS")
    print("="*50)
    for key, value in metrics.items():
        print(f"  {key.upper()}: {value:.4f}")
    print("="*50 + "\n")


def format_image_name(image_name: str) -> str:
    """
    이미지 이름 정규화
    
    Args:
        image_name: 이미지 이름
        
    Returns:
        정규화된 이름
    """
    return image_name.strip().lower()


def validate_prediction(prediction: Any) -> int:
    """
    예측값 검증 및 정규화
    
    Args:
        prediction: 예측값 (0, 1, 'Normal', 'Abnormal', 등)
        
    Returns:
        정규화된 예측값 (0 또는 1)
    """
    if isinstance(prediction, int):
        return 0 if prediction == 0 else 1
    elif isinstance(prediction, str):
        pred_lower = prediction.lower().strip()
        if pred_lower in ['normal', 'normal']:
            return 0
        elif pred_lower in ['abnormal', 'anomaly', 'defect']:
            return 1
    elif isinstance(prediction, float):
        return 0 if prediction < 0.5 else 1
    
    # 기본값
    return -1


class Timer:
    """실행 시간 측정 클래스"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, *args):
        self.end_time = datetime.now()
        elapsed = (self.end_time - self.start_time).total_seconds()
        logger.info(f"{self.name} completed in {elapsed:.2f} seconds")
    
    def elapsed(self) -> float:
        """경과 시간 (초)"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


def print_agent_flow_chart() -> None:
    """Agent Flow Chart 출력"""
    flow = """
    ╔════════════════════════════════════════════════════════╗
    ║       MANUFACTURING AI AGENT - EXECUTION FLOW          ║
    ╚════════════════════════════════════════════════════════╝
    
    📷 INPUT: Image (224x224, normalized)
         ↓
    ┌──────────────────────────────────────────────────────┐
    │ 1️⃣  JUDGE: Vision Analysis (Saltlux API)           │
    │    └─→ Extract visual features                       │
    │    └─→ Identify anomalies                            │
    │    └─→ Generate confidence score                     │
    └──────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │ 2️⃣  THINK: Reasoning Engine                         │
    │    └─→ Analyze findings                              │
    │    └─→ Consider manufacturing context                │
    │    └─→ Assess confidence level                       │
    └──────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │ 3️⃣  ACT: Decision Making                            │
    │    ├─ If confidence > threshold:                     │
    │    │  └─→ Output prediction (Normal/Abnormal)       │
    │    └─ Else:                                          │
    │       └─→ Trigger re-analysis                       │
    └──────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │ 4️⃣  VERIFY: Validation & Confirmation               │
    │    └─→ Double-check reasoning                        │
    │    └─→ Confirm prediction confidence                 │
    │    └─→ Finalize decision                             │
    └──────────────────────────────────────────────────────┘
         ↓
    [Termination Condition Check]
         ├─ Confidence ≥ 0.85 OR Max iterations reached
         │
         └─→ 📊 OUTPUT: Prediction + Confidence Score
    """
    print(flow)


if __name__ == '__main__':
    # 로깅 테스트
    setup_logging('./logs')
    logger.info("✅ Utilities module loaded")
