"""
Saltlux API Client
Saltlux LUXIA PLATFORM API 호출 및 통신
"""

import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from time import sleep

logger = logging.getLogger(__name__)


class SaltluxClient:
    """Saltlux LUXIA PLATFORM API 클라이언트"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.luxiaplatform.com/v1",
                 timeout: int = 30, max_retries: int = 3):
        """
        Args:
            api_key: Saltlux API 키
            base_url: API 기본 URL
            timeout: 요청 타임아웃 (초)
            max_retries: 최대 재시도 횟수
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def _encode_image_to_base64(self, image_path: Union[str, Path]) -> str:
        """
        이미지를 Base64로 인코딩
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            Base64 인코딩된 이미지 문자열
        """
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        API 요청 (재시도 로직 포함)
        
        Args:
            method: HTTP 메서드 (GET, POST, etc.)
            endpoint: API 엔드포인트
            data: 요청 데이터
            
        Returns:
            응답 JSON
        """
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == 'POST':
                    response = requests.post(
                        url,
                        headers=self.headers,
                        json=data,
                        timeout=self.timeout
                    )
                elif method.upper() == 'GET':
                    response = requests.get(
                        url,
                        headers=self.headers,
                        timeout=self.timeout
                    )
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    sleep(2 ** attempt)  # Exponential backoff
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
                if e.response.status_code == 429:  # Rate limited
                    if attempt < self.max_retries - 1:
                        sleep(5 * (attempt + 1))  # Longer wait for rate limit
                elif e.response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        sleep(2 ** attempt)
                        
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    sleep(2 ** attempt)
        
        return None
    
    def analyze_image(self, image_path: Union[str, Path], 
                     analysis_type: str = "manufacturing_defect") -> Optional[Dict[str, Any]]:
        """
        이미지 분석 (Vision API)
        
        Args:
            image_path: 이미지 파일 경로
            analysis_type: 분석 유형
            
        Returns:
            분석 결과 {analysis, confidence, tags, ...}
        """
        try:
            image_path = Path(image_path)
            if not image_path.exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # 이미지를 Base64로 인코딩
            image_base64 = self._encode_image_to_base64(image_path)
            
            # API 요청 데이터 구성
            request_data = {
                'image': image_base64,
                'image_type': 'png' if image_path.suffix == '.png' else 'jpeg',
                'analysis_type': analysis_type,
                'return_raw_analysis': True,
                'confidence_threshold': 0.5
            }
            
            # API 호출
            result = self._make_request('POST', 'vision/analyze', request_data)
            
            if result and result.get('success'):
                return {
                    'analysis': result.get('analysis', ''),
                    'confidence': result.get('confidence', 0.0),
                    'tags': result.get('tags', []),
                    'raw_response': result
                }
            else:
                logger.warning(f"Analysis failed for {image_path}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {e}")
            return None
    
    def classify_image(self, image_path: Union[str, Path],
                      classification_type: str = "binary") -> Optional[Dict[str, Any]]:
        """
        이미지 분류
        
        Args:
            image_path: 이미지 파일 경로
            classification_type: 분류 유형 (binary, multiclass)
            
        Returns:
            분류 결과 {classification, confidence, probabilities}
        """
        try:
            image_path = Path(image_path)
            image_base64 = self._encode_image_to_base64(image_path)
            
            request_data = {
                'image': image_base64,
                'image_type': 'png' if image_path.suffix == '.png' else 'jpeg',
                'classification_type': classification_type,
                'return_probabilities': True
            }
            
            result = self._make_request('POST', 'vision/classify', request_data)
            
            if result and result.get('success'):
                return {
                    'classification': result.get('classification', ''),
                    'confidence': result.get('confidence', 0.0),
                    'probabilities': result.get('probabilities', {}),
                    'raw_response': result
                }
            else:
                logger.warning(f"Classification failed for {image_path}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error classifying image {image_path}: {e}")
            return None
    
    def text_completion(self, prompt: str, max_tokens: int = 500,
                       temperature: float = 0.7) -> Optional[str]:
        """
        텍스트 생성 (LLM API)
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0-1.0)
            
        Returns:
            생성된 텍스트
        """
        try:
            request_data = {
                'prompt': prompt,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'top_p': 0.9
            }
            
            result = self._make_request('POST', 'text/completion', request_data)
            
            if result and result.get('success'):
                return result.get('text', '')
            else:
                logger.warning(f"Text completion failed: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error in text completion: {e}")
            return None
    
    def batch_analyze_images(self, image_paths: list) -> Dict[str, Dict[str, Any]]:
        """
        여러 이미지를 배치 분석
        
        Args:
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            {filename: analysis_result} 딕셔너리
        """
        results = {}
        for i, image_path in enumerate(image_paths):
            logger.info(f"Processing {i+1}/{len(image_paths)}: {image_path}")
            
            result = self.analyze_image(image_path)
            if result:
                results[Path(image_path).name] = result
            else:
                results[Path(image_path).name] = {
                    'analysis': 'Failed',
                    'confidence': 0.0,
                    'tags': [],
                    'error': 'Analysis failed'
                }
            
            # API 속도 제한 회피
            sleep(0.5)
        
        return results
    
    def health_check(self) -> bool:
        """
        API 상태 확인
        
        Returns:
            API 정상 여부
        """
        try:
            result = self._make_request('GET', 'health')
            return result is not None and result.get('status') == 'healthy'
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


if __name__ == '__main__':
    # 테스트
    api_key = os.getenv('SALTLUX_API_KEY', 'test_key')
    client = SaltluxClient(api_key=api_key)
    
    # 헬스 체크
    if client.health_check():
        print("✅ Saltlux API is healthy")
    else:
        print("⚠️  Saltlux API health check failed")
