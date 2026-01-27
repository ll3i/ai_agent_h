"""
Reasoner Module
멀티 스텝 추론 엔진
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class Reasoner:
    """추론 엔진 (Think 단계)"""
    
    def __init__(self, api_client=None):
        """
        Args:
            api_client: Saltlux API 클라이언트 (선택)
        """
        self.api_client = api_client
    
    def reason(self, analysis: str, visual_features: List[str],
              confidence: float) -> Optional[Dict[str, Any]]:
        """
        분석 결과에 대한 다단계 추론
        
        Args:
            analysis: Vision API 분석 결과
            visual_features: 추출된 시각적 특징
            confidence: API에서 반환한 신뢰도
            
        Returns:
            추론 결과 {reasoning, abnormal_indicators, normal_indicators, re_analysis_needed}
        """
        try:
            # Step 1: 시각적 특징 분석
            abnormal_indicators = self._identify_abnormal_indicators(analysis, visual_features)
            normal_indicators = self._identify_normal_indicators(analysis, visual_features)
            
            # Step 2: 제조공정 컨텍스트 고려
            manufacturing_context = self._analyze_manufacturing_context(
                abnormal_indicators,
                normal_indicators,
                confidence
            )
            
            # Step 3: 재분석 필요 여부 판단
            re_analysis_needed = len(abnormal_indicators) > 0 and confidence < 0.75
            
            reasoning_output = {
                'reasoning': self._format_reasoning(
                    abnormal_indicators,
                    normal_indicators,
                    manufacturing_context
                ),
                'abnormal_indicators': abnormal_indicators,
                'normal_indicators': normal_indicators,
                'manufacturing_context': manufacturing_context,
                're_analysis_needed': re_analysis_needed,
                'confidence_score': confidence
            }
            
            return reasoning_output
            
        except Exception as e:
            logger.error(f"Error in reasoning: {e}")
            return None
    
    def _identify_abnormal_indicators(self, analysis: str, 
                                     features: List[str]) -> List[Dict[str, Any]]:
        """비정상 지표 식별"""
        abnormal_keywords = {
            'defect': {'severity': 'high', 'category': 'structural'},
            'crack': {'severity': 'high', 'category': 'structural'},
            'scratch': {'severity': 'medium', 'category': 'surface'},
            'contamination': {'severity': 'medium', 'category': 'cleanliness'},
            'misalignment': {'severity': 'medium', 'category': 'alignment'},
            'deformation': {'severity': 'high', 'category': 'shape'},
            'damage': {'severity': 'high', 'category': 'structural'},
            '결함': {'severity': 'high', 'category': 'structural'},
            '손상': {'severity': 'high', 'category': 'structural'},
            '오염': {'severity': 'medium', 'category': 'cleanliness'},
        }
        
        indicators = []
        analysis_lower = analysis.lower()
        
        for keyword, metadata in abnormal_keywords.items():
            if keyword in analysis_lower:
                indicators.append({
                    'indicator': keyword,
                    'severity': metadata['severity'],
                    'category': metadata['category'],
                    'found': True
                })
        
        # 특징 기반 지표
        for feature in features:
            feature_lower = feature.lower()
            if any(kw in feature_lower for kw in abnormal_keywords.keys()):
                indicators.append({
                    'indicator': feature,
                    'severity': 'medium',
                    'category': 'feature',
                    'found': True
                })
        
        return indicators
    
    def _identify_normal_indicators(self, analysis: str,
                                   features: List[str]) -> List[Dict[str, Any]]:
        """정상 지표 식별"""
        normal_keywords = {
            'good': {'confidence': 'high'},
            'normal': {'confidence': 'high'},
            'acceptable': {'confidence': 'medium'},
            'clean': {'confidence': 'high'},
            'proper': {'confidence': 'medium'},
            'ok': {'confidence': 'medium'},
            'perfect': {'confidence': 'high'},
            '정상': {'confidence': 'high'},
            '양호': {'confidence': 'high'},
            '통과': {'confidence': 'medium'},
            '무결': {'confidence': 'high'},
        }
        
        indicators = []
        analysis_lower = analysis.lower()
        
        for keyword, metadata in normal_keywords.items():
            if keyword in analysis_lower:
                indicators.append({
                    'indicator': keyword,
                    'confidence': metadata['confidence'],
                    'found': True
                })
        
        return indicators
    
    def _analyze_manufacturing_context(self, abnormal: List[Dict],
                                      normal: List[Dict],
                                      confidence: float) -> Dict[str, Any]:
        """제조공정 컨텍스트 분석"""
        high_severity_count = sum(1 for ind in abnormal if ind.get('severity') == 'high')
        medium_severity_count = sum(1 for ind in abnormal if ind.get('severity') == 'medium')
        
        return {
            'high_severity_issues': high_severity_count,
            'medium_severity_issues': medium_severity_count,
            'total_abnormal_indicators': len(abnormal),
            'total_normal_indicators': len(normal),
            'api_confidence': confidence,
            'predominant_quality': 'abnormal' if len(abnormal) > len(normal) else 'normal'
        }
    
    def _format_reasoning(self, abnormal: List[Dict],
                         normal: List[Dict],
                         context: Dict[str, Any]) -> str:
        """추론 결과를 텍스트로 포맷"""
        lines = []
        
        lines.append("Reasoning Analysis:")
        lines.append("-" * 40)
        
        if abnormal:
            lines.append(f"Abnormal Indicators ({len(abnormal)}):")
            for ind in abnormal[:3]:  # 상위 3개만 표시
                lines.append(f"  - {ind.get('indicator', 'Unknown')} "
                           f"(severity: {ind.get('severity', 'unknown')})")
        
        if normal:
            lines.append(f"Normal Indicators ({len(normal)}):")
            for ind in normal[:3]:
                lines.append(f"  - {ind.get('indicator', 'Unknown')}")
        
        lines.append(f"Predominant Quality: {context.get('predominant_quality', 'unknown')}")
        lines.append(f"API Confidence: {context.get('api_confidence', 0.0):.2f}")
        
        return "\n".join(lines)


if __name__ == '__main__':
    logger.info("✅ Reasoner module loaded")
