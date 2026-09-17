#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
최종 테스트 이미지 분류 (개선된 에이전트 사용)
분류 판단 기준이 반영된 최종 결과 생성
"""
import os
import sys
import csv
from pathlib import Path
import io
import logging

# UTF-8 출력 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.integrated_agent import classify_agent_integrated

# 상세 로깅만 출력 (로그 파일에는 상세 기록)
logging.getLogger().setLevel(logging.CRITICAL)

def classify_all_test_images():
    """모든 테스트 이미지 분류 - 최종 버전"""
    
    test_dir = Path(__file__).parent / "test"
    output_file = Path(__file__).parent / "output" / "output.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    results = []
    success_count = 0
    fail_count = 0
    
    print("\n" + "="*80)
    print("100개 테스트 이미지 최종 분류")
    print("="*80)
    
    # TEST_000.png ~ TEST_099.png (100개)
    for i in range(100):
        img_name = f"TEST_{i:03d}"
        img_path = test_dir / f"{img_name}.png"
        
        if not img_path.exists():
            print(f"⚠️  SKIP {img_name}: 파일 없음")
            continue
        
        try:
            result = classify_agent_integrated(str(img_path))
            
            # LABEL: 0 = NORMAL, 1 = ABNORMAL
            label = result.get('prediction', -1)
            confidence = result.get('confidence', 0.0)
            
            label_name = "Abnormal" if label == 1 else "Normal"
            
            results.append({
                'image': img_name,
                'label': label,
                'label_name': label_name,
                'confidence': confidence
            })
            
            success_count += 1
            
            # 진행 상황 표시 (10개마다)
            if (i + 1) % 10 == 0:
                print(f"[{i + 1:3d}/100] 처리됨 ({success_count} 성공, {fail_count} 실패)")
            
        except Exception as e:
            fail_count += 1
            print(f"❌ ERROR {img_name}: {str(e)[:80]}")
    
    # CSV 저장
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['image', 'label', 'label_name', 'confidence'])
        writer.writeheader()
        writer.writerows(results)
    
    # 최종 통계
    print("\n" + "="*80)
    print("최종 결과")
    print("="*80)
    print(f"✅ 처리 완료: {success_count}/100")
    print(f"❌ 처리 실패: {fail_count}/100")
    print(f"📁 결과 저장: {output_file}")
    
    # 통계
    abnormal_count = sum(1 for r in results if r['label'] == 1)
    normal_count = sum(1 for r in results if r['label'] == 0)
    avg_confidence = sum(r['confidence'] for r in results) / len(results) if results else 0
    
    print(f"\n분류 통계:")
    print(f"  Normal:   {normal_count:3d} / {len(results)} ({100*normal_count/len(results):5.1f}%)")
    print(f"  Abnormal: {abnormal_count:3d} / {len(results)} ({100*abnormal_count/len(results):5.1f}%)")
    print(f"  평균 신뢰도: {avg_confidence:.3f}")
    print("="*80 + "\n")

if __name__ == "__main__":
    classify_all_test_images()
