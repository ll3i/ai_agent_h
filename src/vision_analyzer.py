"""
Vision Analyzer Module
Saltlux API를 통한 이미지 시각 분석
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """이미지 시각 분석기 (Vision API 활용)"""
    
    def __init__(self, api_client):
        """
        Args:
            api_client: Saltlux API 클라이언트
        """
        self.api_client = api_client
    
    def analyze(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        이미지 분석 (Saltlux Vision API)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            분석 결과 {analysis, confidence, tags, raw_response}
        """
        try:
            # API 호출
            result = self.api_client.analyze_image(
                image_path=image_path,
                analysis_type='manufacturing_defect'
            )
            
            if result is None:
                logger.warning(f"Vision analysis returned None for {image_path}")
                return None
            
            # 결과 처리
            return {
                'analysis': result.get('analysis', ''),
                'confidence': result.get('confidence', 0.0),
                'tags': result.get('tags', []),
                'raw_response': result.get('raw_response', {})
            }
            
        except Exception as e:
            logger.error(f"Error in vision analysis: {e}")
            return None
    
    def extract_defect_indicators(self, analysis: str, tags: List[str]) -> Dict[str, Any]:
        """
        분석 결과에서 결함 지표 추출
        
        Args:
            analysis: 분석 텍스트
            tags: 태그 리스트
            
        Returns:
            {defect_keywords, confidence_keywords, quality_score}
        """
        defect_keywords = [
            'defect', 'crack', 'scratch', 'contamination',
            'misalignment', 'deformation', 'damage',
            '결함', '손상', '오염', '부정렬', '변형'
        ]
        
        quality_keywords = [
            'good', 'normal', 'acceptable', 'ok', 'perfect',
            'clean', 'proper', '정상', '양호', '통과'
        ]
        
        analysis_lower = analysis.lower()
        
        found_defects = [kw for kw in defect_keywords if kw in analysis_lower]
        found_quality = [kw for kw in quality_keywords if kw in analysis_lower]
        
        return {
            'defect_keywords': found_defects,
            'quality_keywords': found_quality,
            'tags': tags
        }
    
    def extract_confidence_signals(self, analysis: str) -> float:
        """
        분석 텍스트에서 신뢰도 신호 추출
        
        Args:
            analysis: 분석 텍스트
            
        Returns:
            신뢰도 점수 (0.0-1.0)
        """
        high_confidence_signals = ['clearly', 'definitely', 'obvious', 'evident', 'certain']
        medium_confidence_signals = ['likely', 'appears', 'suggests', 'probably']
        low_confidence_signals = ['might', 'could', 'possibly', 'uncertain', 'unclear']
        
        analysis_lower = analysis.lower()
        
        high_count = sum(1 for signal in high_confidence_signals if signal in analysis_lower)
        medium_count = sum(1 for signal in medium_confidence_signals if signal in analysis_lower)
        low_count = sum(1 for signal in low_confidence_signals if signal in analysis_lower)
        
        # 가중 평균
        total_signals = high_count + medium_count + low_count
        if total_signals == 0:
            return 0.5  # 신호 없으면 중간값
        
        confidence = (high_count * 1.0 + medium_count * 0.5 + low_count * 0.2) / total_signals
        return min(1.0, max(0.0, confidence))


if __name__ == '__main__':
    logger.info("✅ Vision analyzer module loaded")
