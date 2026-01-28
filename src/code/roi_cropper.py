"""
ROI Cropper for Multi-Agent Analysis
이미지를 Body(몰딩)와 Lead(리드프레임) 영역으로 분리

핵심: 필터 없이 순수 크로핑만 수행
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict
import logging

logger = logging.getLogger(__name__)


def load_image_safe(image_path: str) -> np.ndarray:
    """
    한글 경로 지원 이미지 로드
    """
    img_array = np.fromfile(image_path, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")
    return img


def crop_body_roi(image_path: str) -> bytes:
    """
    Body ROI (몰딩/패키지 영역) 크로핑
    
    - 이미지 상단 40% 영역
    - 패키지 깨짐, 구멍, 누락 분석용
    - 필터 없음, 원본 그대로
    
    Returns:
        PNG 인코딩된 바이트
    """
    img = load_image_safe(image_path)
    h, w = img.shape[:2]
    
    # 상단 40% 크로핑 (Body 영역)
    body_end = int(h * 0.40)
    body_roi = img[0:body_end, :]
    
    # PNG로 인코딩
    success, encoded = cv2.imencode('.png', body_roi)
    if not success:
        raise ValueError("Failed to encode body ROI")
    
    return encoded.tobytes()


def crop_lead_roi(image_path: str) -> bytes:
    """
    Lead ROI (리드/다리 영역) 크로핑
    
    - 이미지 하단 60% 영역
    - 리드 끊어짐, 쇼트, 연결성 분석용
    - 필터 없음, 원본 그대로
    
    Returns:
        PNG 인코딩된 바이트
    """
    img = load_image_safe(image_path)
    h, w = img.shape[:2]
    
    # 하단 60% 크로핑 (Lead 영역)
    lead_start = int(h * 0.40)
    lead_roi = img[lead_start:, :]
    
    # PNG로 인코딩
    success, encoded = cv2.imencode('.png', lead_roi)
    if not success:
        raise ValueError("Failed to encode lead ROI")
    
    return encoded.tobytes()


def crop_both_rois(image_path: str) -> Dict[str, bytes]:
    """
    Body와 Lead ROI 모두 크로핑
    
    Returns:
        {'body': bytes, 'lead': bytes}
    """
    return {
        'body': crop_body_roi(image_path),
        'lead': crop_lead_roi(image_path)
    }


def save_roi_preview(image_path: str, output_dir: str = "./roi_preview"):
    """
    ROI 미리보기 저장 (디버깅용)
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    img = load_image_safe(image_path)
    h, w = img.shape[:2]
    
    body_end = int(h * 0.40)
    
    # Body ROI
    body_roi = img[0:body_end, :]
    # Lead ROI
    lead_roi = img[body_end:, :]
    
    base_name = Path(image_path).stem
    cv2.imwrite(f"{output_dir}/{base_name}_body.png", body_roi)
    cv2.imwrite(f"{output_dir}/{base_name}_lead.png", lead_roi)
    
    logger.info(f"Saved ROI preview: {base_name}")


if __name__ == "__main__":
    # 테스트
    import sys
    if len(sys.argv) > 1:
        save_roi_preview(sys.argv[1])
        print("ROI preview saved to ./roi_preview/")
