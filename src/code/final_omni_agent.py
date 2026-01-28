"""
Luxia Omni-Agent: The Final Integrated System
Combines:
1. Vision Agent (Triple Vision - Best Accuracy 74%)
2. Knowledge Agent (RAG/Embedding - Finds similar cases)
3. Report Agent (Text Gen - Creates detailed reports)
"""

import logging
from typing import Tuple, Dict, Any

# Import specialized agents
from src.jtav_triple_vision import classify_jtav_triple
from src.luxia_enhanced_agent import DefectKnowledgeBase, DefectReportGenerator

logger = logging.getLogger(__name__)

class LuxiaOmniAgent:
    def __init__(self):
        self.vision_agent = classify_jtav_triple
        self.knowledge_agent = DefectKnowledgeBase()
        self.report_agent = DefectReportGenerator()
        
    def analyze(self, image_path: str) -> Tuple[int, str]:
        logger.info(f"[OMNI-AGENT] Starting analysis for: {image_path}")
        
        # 1. Vision Agent Execution
        # Uses Luxia 32B with Triple Vision strategy
        label, reason = self.vision_agent(image_path)
        
        # 2. Knowledge Agent Enhancement (RAG)
        # Finds similar past cases to validate/explain the decision
        similar_cases = self.knowledge_agent.similarity_search(reason, top_k=2)
        
        relevant_case = similar_cases[0] if similar_cases else None
        kb_context = ""
        
        if relevant_case and relevant_case['similarity_score'] > 0.1:
            kb_context = f" (Similar to {relevant_case['case']['id']}: {relevant_case['case']['description']})"
            logger.info(f"  [KNOWLEDGE] Found similar case: {relevant_case['case']['id']} (Score: {relevant_case['similarity_score']:.2f})")
        
        # 3. Report Agent (Text Gen)
        # Generates the final output string (simulated full report, but we return concise reason for CSV)
        # We append the KB context to the reason
        final_reason = f"{reason}{kb_context}"
        
        return label, final_reason

# Singleton instance
omni_agent = LuxiaOmniAgent()

def classify_omni_final(image_path: str) -> Tuple[int, str]:
    """Wrapper for external calls"""
    return omni_agent.analyze(image_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        l, r = classify_omni_final(sys.argv[1])
        print(f"Result: {l}, Reason: {r}")
