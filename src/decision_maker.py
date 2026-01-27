"""
Decision Maker Module
의사결정 모듈 (Act 단계)
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class DecisionMaker:
    """의사결정 모듈 (Act 단계)"""
    
    def __init__(self, confidence_threshold: float = 0.85):
        """
        Args:
            confidence_threshold: 최종 판단 신뢰도 임계값
        """
        self.confidence_threshold = confidence_threshold
    
    def decide(self, reasoning: str, confidence: float,
              abnormal_indicators: List[Dict],
              normal_indicators: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        최종 판단 결정
        
        Args:
            reasoning: 추론 결과 텍스트
            confidence: 신뢰도 점수
            abnormal_indicators: 비정상 지표 리스트
            normal_indicators: 정상 지표 리스트
            
        Returns:
            {decision, justification, should_retry}
            decision: 0 (Normal) 또는 1 (Abnormal)
        """
        try:
            # Step 1: 지표 기반 초기 판단
            initial_decision = self._evaluate_indicators(
                abnormal_indicators,
                normal_indicators
            )
            
            # Step 2: 신뢰도 기반 조정
            adjusted_decision = self._adjust_by_confidence(
                initial_decision,
                confidence
            )
            
            # Step 3: 최종 판단 및 근거 작성
            final_decision = adjusted_decision['decision']
            justification = self._generate_justification(
                final_decision,
                abnormal_indicators,
                normal_indicators,
                confidence
            )
            
            # Step 4: 재분석 필요 여부
            should_retry = confidence < 0.7 and len(abnormal_indicators) > 0
            
            decision_output = {
                'decision': final_decision,  # 0: Normal, 1: Abnormal
                'decision_label': 'Normal' if final_decision == 0 else 'Abnormal',
                'justification': justification,
                'confidence': confidence,
                'should_retry': should_retry,
                'reasoning_path': {
                    'initial_decision': initial_decision,
                    'adjusted_decision': adjusted_decision
                }
            }
            
            return decision_output
            
        except Exception as e:
            logger.error(f"Error in decision making: {e}")
            return None
    
    def _evaluate_indicators(self, abnormal: List[Dict],
                            normal: List[Dict]) -> int:
        """
        지표 기반으로 초기 판단
        
        Returns:
            0 (Normal) 또는 1 (Abnormal)
        """
        # 고심각도 비정상 지표 우선
        high_severity_abnormal = sum(
            1 for ind in abnormal if ind.get('severity') == 'high'
        )
        
        if high_severity_abnormal > 0:
            return 1  # Abnormal
        
        # 비정상 지표 개수 비교
        if len(abnormal) > len(normal):
            return 1  # Abnormal
        
        # 기본값: Normal
        return 0
    
    def _adjust_by_confidence(self, initial_decision: int,
                             confidence: float) -> Dict[str, Any]:
        """
        신뢰도에 따른 판단 조정
        
        Args:
            initial_decision: 초기 판단
            confidence: 신뢰도 점수
            
        Returns:
            {decision, adjustment_reason}
        """
        # 신뢰도가 높으면 초기 판단 유지
        if confidence >= 0.80:
            return {
                'decision': initial_decision,
                'adjustment_reason': 'High confidence, maintaining initial decision'
            }
        
        # 신뢰도가 낮으면 좀 더 보수적인 판단
        if confidence < 0.60:
            # 비정상이 아닌 한 정상으로 판단 (False Positive 최소화)
            adjusted = 0 if initial_decision == 0 else 1
            return {
                'decision': adjusted,
                'adjustment_reason': 'Low confidence, applying conservative threshold'
            }
        
        # 신뢰도 중간 범위
        return {
            'decision': initial_decision,
            'adjustment_reason': 'Medium confidence, proceeding with initial decision'
        }
    
    def _generate_justification(self, decision: int,
                               abnormal: List[Dict],
                               normal: List[Dict],
                               confidence: float) -> str:
        """
        판단 근거 생성
        
        Args:
            decision: 최종 판단 (0 or 1)
            abnormal: 비정상 지표
            normal: 정상 지표
            confidence: 신뢰도
            
        Returns:
            근거 텍스트
        """
        justification = []
        
        decision_label = 'ABNORMAL' if decision == 1 else 'NORMAL'
        justification.append(f"Final Decision: {decision_label}")
        justification.append(f"Confidence Score: {confidence:.2%}")
        
        if abnormal:
            high_severity = [ind for ind in abnormal if ind.get('severity') == 'high']
            if high_severity:
                justification.append(f"Critical Issues Found: {len(high_severity)}")
                for ind in high_severity[:2]:
                    justification.append(f"  - {ind.get('indicator', 'Unknown')}")
        
        if normal:
            justification.append(f"Positive Indicators: {len(normal)}")
        
        if confidence < 0.75:
            justification.append("⚠️  Low confidence - may require re-analysis")
        
        return "\n".join(justification)


if __name__ == '__main__':
    logger.info("✅ Decision maker module loaded")
