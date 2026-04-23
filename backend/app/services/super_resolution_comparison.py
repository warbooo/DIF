"""
Super Resolution Comparison Service
Provides comparison functions for SR results
"""
from typing import List, Dict, Any


def compare_sr_ocr_improvement(
    original_text: str,
    original_confidences: List[float],
    repaired_text: str,
    repaired_confidences: List[float]
) -> Dict[str, Any]:
    """
    Compare OCR results before and after super-resolution
    
    Args:
        original_text: OCR text from original image
        original_confidences: OCR confidences from original image
        repaired_text: OCR text from repaired image
        repaired_confidences: OCR confidences from repaired image
        
    Returns:
        Comparison result dictionary
    """
    # Calculate basic statistics
    original_line_count = len(original_text.split('\n')) if original_text else 0
    repaired_line_count = len(repaired_text.split('\n')) if repaired_text else 0
    
    original_char_count = len(original_text.replace(' ', '').replace('\n', '')) if original_text else 0
    repaired_char_count = len(repaired_text.replace(' ', '').replace('\n', '')) if repaired_text else 0
    
    # Calculate average confidences
    original_avg_confidence = sum(original_confidences) / len(original_confidences) if original_confidences else 0
    repaired_avg_confidence = sum(repaired_confidences) / len(repaired_confidences) if repaired_confidences else 0
    
    # Calculate improvements
    line_improvement = repaired_line_count - original_line_count
    char_improvement = repaired_char_count - original_char_count
    confidence_improvement = repaired_avg_confidence - original_avg_confidence
    
    return {
        "original": {
            "text_length": len(original_text),
            "line_count": original_line_count,
            "char_count": original_char_count,
            "avg_confidence": original_avg_confidence,
        },
        "repaired": {
            "text_length": len(repaired_text),
            "line_count": repaired_line_count,
            "char_count": repaired_char_count,
            "avg_confidence": repaired_avg_confidence,
        },
        "improvement": {
            "line_count_change": line_improvement,
            "char_count_change": char_improvement,
            "confidence_change": confidence_improvement,
        },
        "text_comparison": {
            "original_text": original_text,
            "repaired_text": repaired_text,
        }
    }
