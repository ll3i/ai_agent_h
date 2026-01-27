"""
Verifier Module
검증 모듈 (Verify 단계)
"""

import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class Verifier:
    """검증 모듈 (Verify 단계)"""
    
    def __init__(self, confidence_threshold: float = 0.85):
        """
        Args:
            confidence_threshold: 최종 판단 신뢰도 임계값
        """
        self.confidence_threshold = confidence_threshold
    
    def verify(self, decision: Optional[int], confidence: float,
              analysis: str, justification: str,
              abnormal_indicators: List[Dict],
              normal_indicators: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        의사결정 결과 검증
        
        Args:
            decision: 의사결정 (0 or 1)
            confidence: 신뢰도 점수
            analysis: 원본 분석 텍스트
            justification: 의사결정 근거
            abnormal_indicators: 비정상 지표
            normal_indicators: 정상 지표
            
        Returns:
            {verified, confidence, final_decision}
        """
        try:
            # Step 1: 의사결정 일관성 확인
            consistency = self._check_consistency(
                decision,
                abnormal_indicators,
                normal_indicators
            )
            
            # Step 2: 신뢰도 재평가
            verified_confidence = self._recalculate_confidence(
                confidence,
                consistency,
                abnormal_indicators,
                normal_indicators
            )
            
            # Step 3: 최종 확인
            verified = self._finalize_verification(
                decision,
                verified_confidence,
                consistency
            )
            
            verify_output = {
                'verified': verified,
                'confidence': verified_confidence,
                'final_decision': decision,
                'decision_label': 'Normal' if decision == 0 else 'Abnormal',
                'consistency_check': consistency,
                'justification': justification
            }
            
            return verify_output
            
        except Exception as e:
            logger.error(f"Error in verification: {e}")
            return None
    
    def _check_consistency(self, decision: Optional[int],
                          abnormal: List[Dict],
                          normal: List[Dict]) -> Dict[str, Any]:
        """
        의사결정과 지표의 일관성 확인
        
        Returns:
            {is_consistent, consistency_score, conflicts}
        """
        if decision is None:
            return {
                'is_consistent': False,
                'consistency_score': 0.0,
                'conflicts': ['No decision made']
            }
        
        conflicts = []
        
        # 비정상 결정인데 정상 지표만 있는 경우
        if decision == 1 and len(abnormal) == 0 and len(normal) > 0:
            conflicts.append('Abnormal decision but only normal indicators found')
        
        # 정상 결정인데 비정상 지표가 많은 경우
        if decision == 0 and len(abnormal) > len(normal) * 2:
            conflicts.append('Normal decision but multiple abnormal indicators found')
        
        consistency_score = 1.0 if len(conflicts) == 0 else 0.7
        
        return {
            'is_consistent': len(conflicts) == 0,
            'consistency_score': consistency_score,
            'conflicts': conflicts,
            'abnormal_count': len(abnormal),
            'normal_count': len(normal)
        }
    
    def _recalculate_confidence(self, api_confidence: float,
                               consistency: Dict[str, Any],
                               abnormal: List[Dict],
                               normal: List[Dict]) -> float:
        """
        신뢰도 재평가
        
        Returns:
            조정된 신뢰도 (0.0-1.0)
        """
        # API 신뢰도 (50% 가중치)
        weighted_api_conf = api_confidence * 0.5
        
        # 일관성 점수 (30% 가중치)
        weighted_consistency = consistency.get('consistency_score', 0.5) * 0.3
        
        # 지표 기반 신뢰도 (20% 가중치)
        total_indicators = len(abnormal) + len(normal)
        if total_indicators > 0:
            indicator_confidence = (max(len(abnormal), len(normal)) / total_indicators) * 0.2
        else:
            indicator_confidence = 0.5 * 0.2
        
        final_confidence = weighted_api_conf + weighted_consistency + indicator_confidence
        
        return min(1.0, max(0.0, final_confidence))
    
    def _finalize_verification(self, decision: Optional[int],
                              confidence: float,
                              consistency: Dict[str, Any]) -> bool:
        """
        최종 검증 수행
        
        Returns:
            검증 성공 여부
        """
        if decision is None:
            logger.warning("No decision to verify")
            return False
        
        # 일관성이 낮고 신뢰도도 낮으면 실패
        if not consistency.get('is_consistent', False) and confidence < 0.60:
            return False
        
        # 기본적으로 성공 (재분석은 Agent 레벨에서 처리)
        return True
    
    def confidence_summary(self, verification_result: Dict[str, Any]) -> str:
        """
        검증 결과 요약
        
        Args:
            verification_result: 검증 결과
            
        Returns:
            요약 텍스트
        """
        decision = verification_result.get('decision_label', 'Unknown')
        confidence = verification_result.get('confidence', 0.0)
        verified = verification_result.get('verified', False)
        
        status = "✅ Verified" if verified else "⚠️  Unverified"
        
        summary = f"{status} | Decision: {decision} | Confidence: {confidence:.2%}"
        
        return summary


if __name__ == '__main__':
    logger.info("✅ Verifier module loaded")
