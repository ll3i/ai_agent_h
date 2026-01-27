"""
Image Processor Module
이미지 전처리 및 로딩 담당
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Union, List
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """이미지 전처리 및 처리 클래스"""
    
    def __init__(self, target_size: Tuple[int, int] = (224, 224), 
                 quality: int = 95):
        """
        Args:
            target_size: 리사이징 목표 크기 (width, height)
            quality: 이미지 품질 (1-100)
        """
        self.target_size = target_size
        self.quality = quality
    
    @staticmethod
    def load_image(image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        이미지 로드
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            이미지 배열 (BGR format, OpenCV)
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                logger.warning(f"Failed to load image: {image_path}")
                return None
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def preprocess(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        이미지 전처리 (리사이징 + 정규화)
        
        Args:
            image: 입력 이미지 (BGR format)
            
        Returns:
            전처리된 이미지
        """
        try:
            # 1. 리사이징
            resized = cv2.resize(image, self.target_size, interpolation=cv2.INTER_LINEAR)
            
            # 2. 정규화 (0-1 범위로)
            normalized = resized.astype(np.float32) / 255.0
            
            return normalized
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return None
    
    @staticmethod
    def enhance_contrast(image: np.ndarray, alpha: float = 1.2, 
                         beta: float = 0) -> np.ndarray:
        """
        대비 강화 (선택적)
        
        Args:
            image: 입력 이미지
            alpha: 명도 조절 계수
            beta: 밝기 조절 값
            
        Returns:
            대비 강화된 이미지
        """
        enhanced = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return enhanced
    
    @staticmethod
    def normalize_colors(image: np.ndarray) -> np.ndarray:
        """
        색상 정규화 (CLAHE - Contrast Limited Adaptive Histogram Equalization)
        
        Args:
            image: 입력 이미지 (0-1 범위)
            
        Returns:
            색상 정규화된 이미지
        """
        # 0-255 범위로 변환
        img_8bit = (image * 255).astype(np.uint8)
        
        # BGR을 LAB로 변환
        lab = cv2.cvtColor(img_8bit, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # L 채널에 CLAHE 적용
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # 다시 합치기
        lab = cv2.merge([l, a, b])
        normalized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 0-1 범위로 정규화
        return normalized.astype(np.float32) / 255.0
    
    def process_from_file(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        파일에서 이미지 로드 및 전처리
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            전처리된 이미지 배열
        """
        image = self.load_image(image_path)
        if image is None:
            return None
        
        processed = self.preprocess(image)
        return processed
    
    @staticmethod
    def save_image(image: np.ndarray, output_path: Union[str, Path], 
                   quality: int = 95) -> bool:
        """
        이미지 저장
        
        Args:
            image: 저장할 이미지
            output_path: 저장 경로
            quality: 저장 품질
            
        Returns:
            성공 여부
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 0-1 범위면 0-255로 변환
            if image.dtype == np.float32 or image.dtype == np.float64:
                image = (image * 255).astype(np.uint8)
            
            success = cv2.imwrite(str(output_path), image, 
                                 [cv2.IMWRITE_PNG_COMPRESSION, 9])
            return success
        except Exception as e:
            logger.error(f"Error saving image to {output_path}: {e}")
            return False
    
    @staticmethod
    def get_image_metadata(image_path: Union[str, Path]) -> Optional[dict]:
        """
        이미지 메타데이터 추출
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            메타데이터 딕셔너리
        """
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return None
            
            height, width, channels = image.shape
            file_size = Path(image_path).stat().st_size
            
            metadata = {
                'filename': Path(image_path).name,
                'width': width,
                'height': height,
                'channels': channels,
                'file_size_bytes': file_size,
                'aspect_ratio': width / height if height > 0 else 0
            }
            return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata from {image_path}: {e}")
            return None
    
    @staticmethod
    def batch_load_images(image_dir: Union[str, Path], 
                         extensions: List[str] = None) -> dict:
        """
        디렉토리에서 일괄 이미지 로드
        
        Args:
            image_dir: 이미지 디렉토리 경로
            extensions: 확장자 필터 (예: ['.png', '.jpg'])
            
        Returns:
            {filename: image_array} 딕셔너리
        """
        if extensions is None:
            extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        
        image_dir = Path(image_dir)
        images = {}
        
        for ext in extensions:
            for image_path in image_dir.glob(f'*{ext}'):
                image = ImageProcessor.load_image(image_path)
                if image is not None:
                    images[image_path.name] = image
        
        logger.info(f"Loaded {len(images)} images from {image_dir}")
        return images


if __name__ == '__main__':
    # 테스트
    processor = ImageProcessor(target_size=(224, 224))
    print("✅ ImageProcessor initialized")
