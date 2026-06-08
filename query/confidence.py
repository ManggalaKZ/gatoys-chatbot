"""
Confidence Calculator
Calculate answer quality confidence score
"""

import re
from typing import List
from langchain.docstore.document import Document

def calculate_confidence(answer: str, sources: List[Document], 
                         question: str) -> float:
    """Calculate confidence score (0.0 - 1.0)"""
    
    confidence = 0.5  # base
    
    # Factor 1: Answer completeness
    if len(answer) > 100:
        confidence += 0.15
    elif len(answer) < 30:
        confidence -= 0.2
    
    # Factor 2: Source quality
    if len(sources) >= 3:
        confidence += 0.2
    elif len(sources) < 2:
        confidence -= 0.15
    
    # Factor 3: Has specific info
    if re.search(r'Rp\s*[\d.,]+', answer):
        confidence += 0.1
    if re.search(r'\d+\s*(cm|kg|tahun)', answer):
        confidence += 0.05
    
    # Factor 4: Uncertainty
    uncertainty = ['tidak ada', 'tidak tersedia', 'maaf', 'tidak tahu']
    if any(phrase in answer.lower() for phrase in uncertainty):
        confidence -= 0.25
    
    # Factor 5: Relevance
    q_keywords = set(re.findall(r'\w+', question.lower()))
    a_keywords = set(re.findall(r'\w+', answer.lower()))
    overlap = len(q_keywords & a_keywords) / max(len(q_keywords), 1)
    confidence += overlap * 0.1
    
    return max(0.0, min(1.0, confidence))