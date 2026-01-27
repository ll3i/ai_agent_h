"""
Agent Core Module
AI Agent의 메인 실행 엔진 (Judge-Think-Act-Verify)
"""

import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Agent의 현재 상태"""
    image_path: str
    iteration: int = 0
    current_analysis: str = ""
    confidence: float = 0.0
    final_prediction: Optional[int] = None
    decision_history: list = None
    
    def __post_init__(self):
        if self.decision_history is None:
            self.decision_history = []


class ManufacturingAgent:
    """
    제조공정 이미지 분류 AI Agent
    Judge-Think-Act-Verify 아키텍처
    """
    
    def __init__(self, vision_analyzer, reasoner, 
                 decision_maker, verifier,
                 max_iterations: int = 3,
                 confidence_threshold: float = 0.85):
        """
        Args:
            vision_analyzer: 이미지 분석기
            reasoner: 추론 엔진
            decision_maker: 의사결정 모듈
            verifier: 검증 모듈
            max_iterations: 최대 반복 횟수
            confidence_threshold: 신뢰도 임계값
        """
        self.vision_analyzer = vision_analyzer
        self.reasoner = reasoner
        self.decision_maker = decision_maker
        self.verifier = verifier
        self.max_iterations = max_iterations
        self.confidence_threshold = confidence_threshold
    
    def judge(self, state: AgentState) -> Dict[str, Any]:
        """
        Step 1: JUDGE - 이미지 분석 및 판단
        
        Args:
            state: Agent 상태
            
        Returns:
            판단 결과 {analysis, visual_features, confidence}
        """
        logger.info(f"  [JUDGE] Analyzing image: {Path(state.image_path).name}")
        
        # Vision Analysis - Saltlux API 호출
        analysis_result = self.vision_analyzer.analyze(state.image_path)
        
        if analysis_result is None:
            logger.warning(f"  [JUDGE] Analysis failed for {state.image_path}")
            return {
                'analysis': 'Analysis failed',
                'confidence': 0.0,
                'visual_features': []
            }
        
        state.current_analysis = analysis_result.get('analysis', '')
        state.confidence = analysis_result.get('confidence', 0.0)
        
        judge_result = {
            'analysis': analysis_result.get('analysis', ''),
            'visual_features': analysis_result.get('tags', []),
            'confidence': state.confidence,
            'raw_response': analysis_result.get('raw_response', {})
        }
        
        logger.debug(f"  [JUDGE] Confidence: {state.confidence:.2f}")
        return judge_result
    
    def think(self, state: AgentState, judge_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 2: THINK - 분석 결과 추론
        
        Args:
            state: Agent 상태
            judge_result: Judge 단계 결과
            
        Returns:
            추론 결과 {reasoning, abnormal_indicators, normal_indicators}
        """
        logger.info(f"  [THINK] Reasoning about analysis")
        
        # Reasoning - 다단계 로직
        reasoning_result = self.reasoner.reason(
            analysis=judge_result.get('analysis', ''),
            visual_features=judge_result.get('visual_features', []),
            confidence=judge_result.get('confidence', 0.0)
        )
        
        if reasoning_result is None:
            logger.warning("  [THINK] Reasoning failed")
            return {
                'reasoning': 'Unable to reason',
                'abnormal_indicators': [],
                'normal_indicators': [],
                're_analysis_needed': False
            }
        
        return reasoning_result
    
    def act(self, state: AgentState, think_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 3: ACT - 의사결정
        
        Args:
            state: Agent 상태
            think_result: Think 단계 결과
            
        Returns:
            의사결정 결과 {decision, justification, should_retry}
        """
        logger.info(f"  [ACT] Making decision")
        
        # Decision Making
        decision_result = self.decision_maker.decide(
            reasoning=think_result.get('reasoning', ''),
            confidence=state.confidence,
            abnormal_indicators=think_result.get('abnormal_indicators', []),
            normal_indicators=think_result.get('normal_indicators', [])
        )
        
        if decision_result is None:
            logger.warning("  [ACT] Decision making failed")
            return {
                'decision': None,
                'justification': 'Unable to make decision',
                'should_retry': True
            }
        
        state.final_prediction = decision_result.get('decision')
        
        decision_output = {
            'decision': decision_result.get('decision'),  # 0 or 1
            'justification': decision_result.get('justification', ''),
            'should_retry': decision_result.get('should_retry', False)
        }
        
        logger.debug(f"  [ACT] Decision: {'Normal' if state.final_prediction == 0 else 'Abnormal'}")
        return decision_output
    
    def verify(self, state: AgentState, 
               judge_result: Dict[str, Any],
               think_result: Dict[str, Any],
               act_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: VERIFY - 결과 검증
        
        Args:
            state: Agent 상태
            judge_result: Judge 결과
            think_result: Think 결과
            act_result: Act 결과
            
        Returns:
            검증 결과 {verified, confidence, final_decision, should_terminate}
        """
        logger.info(f"  [VERIFY] Verifying decision")
        
        verify_result = self.verifier.verify(
            decision=state.final_prediction,
            confidence=state.confidence,
            analysis=state.current_analysis,
            justification=act_result.get('justification', ''),
            abnormal_indicators=think_result.get('abnormal_indicators', []),
            normal_indicators=think_result.get('normal_indicators', [])
        )
        
        if verify_result is None:
            logger.warning("  [VERIFY] Verification failed")
            return {
                'verified': False,
                'confidence': state.confidence,
                'final_decision': state.final_prediction,
                'should_terminate': False
            }
        
        # 종료 조건 확인
        should_terminate = (
            verify_result.get('confidence', 0.0) >= self.confidence_threshold or
            state.iteration >= self.max_iterations - 1
        )
        
        verify_result['should_terminate'] = should_terminate
        
        logger.debug(f"  [VERIFY] Verified: {verify_result.get('verified')}, "
                    f"Confidence: {verify_result.get('confidence'):.2f}, "
                    f"Terminate: {should_terminate}")
        
        return verify_result
    
    def execute(self, image_path: str) -> Dict[str, Any]:
        """
        Agent 전체 실행 (Judge-Think-Act-Verify 반복)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            최종 결과 {prediction, confidence, reasoning_path}
        """
        logger.info(f"\n🤖 Processing: {Path(image_path).name}")
        logger.info("=" * 60)
        
        state = AgentState(image_path=image_path)
        
        while state.iteration < self.max_iterations:
            logger.info(f"⏰ Iteration {state.iteration + 1}/{self.max_iterations}")
            
            # Step 1: JUDGE
            judge_result = self.judge(state)
            
            # Step 2: THINK
            think_result = self.think(state, judge_result)
            
            # Step 3: ACT
            act_result = self.act(state, think_result)
            
            # Step 4: VERIFY
            verify_result = self.verify(state, judge_result, think_result, act_result)
            
            # 결정 기록
            state.decision_history.append({
                'iteration': state.iteration,
                'prediction': state.final_prediction,
                'confidence': verify_result.get('confidence', state.confidence),
                'analysis': state.current_analysis
            })
            
            # 종료 조건 확인
            if verify_result.get('should_terminate', False):
                logger.info(f"✅ Termination condition met at iteration {state.iteration + 1}")
                break
            
            state.iteration += 1
        
        # 최종 결과
        final_result = {
            'image_path': str(image_path),
            'image_name': Path(image_path).name,
            'prediction': state.final_prediction,  # 0 or 1
            'confidence': verify_result.get('confidence', state.confidence),
            'iterations': state.iteration + 1,
            'reasoning_path': state.decision_history,
            'final_analysis': state.current_analysis
        }
        
        prediction_label = 'Normal' if state.final_prediction == 0 else 'Abnormal'
        logger.info(f"📊 Final Result: {prediction_label} (confidence: {final_result['confidence']:.2f})")
        logger.info("=" * 60 + "\n")
        
        return final_result
    
    def process_batch(self, image_paths: list, 
                     batch_size: int = 5) -> list:
        """
        여러 이미지를 배치로 처리
        
        Args:
            image_paths: 이미지 경로 리스트
            batch_size: 배치 크기
            
        Returns:
            결과 리스트
        """
        all_results = []
        
        for i, image_path in enumerate(image_paths):
            logger.info(f"[{i+1}/{len(image_paths)}] Processing batch item")
            
            result = self.execute(image_path)
            all_results.append(result)
            
            # 진행 상황 표시
            if (i + 1) % batch_size == 0:
                logger.info(f"✓ Completed {i+1}/{len(image_paths)} images")
        
        logger.info(f"\n✅ Batch processing complete: {len(all_results)} images")
        return all_results


if __name__ == '__main__':
    logger.info("✅ Agent core module loaded")
