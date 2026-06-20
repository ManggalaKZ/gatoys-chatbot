"""
API Models
Pydantic models untuk request/response validation
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ============================================================
# REQUEST MODELS
# ============================================================

class QueryRequest(BaseModel):
    """
    Chat query request model
    
    Example:
        {
            "question": "Ada mainan Molly?",
            "user_id": "user123",
            "session_id": "sess_abc"
        }
    """
    question: str = Field(..., min_length=1, description="User's question")
    user_id: Optional[str] = Field(default="anonymous", description="User ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Ada mainan Molly?",
                "user_id": "user123",
                "session_id": "sess_abc123"
            }
        }


# ============================================================
# RESPONSE MODELS
# ============================================================

class SourceInfo(BaseModel):
    """Information about a retrieved source"""
    rank: int = Field(..., description="Source ranking (1-based)")
    type: str = Field(..., description="Type: 'product' or other")
    product_name: Optional[str] = Field(None, description="Product name if type=product")
    price: Optional[float] = Field(None, description="Product price if type=product")
    image: Optional[str] = Field(None, description="Product image filename (from product_images)")
    product_id: Optional[int] = Field(None, description="Product ID for linking to detail page")
    title: Optional[str] = Field(None, description="Title if not product")


class QueryResponse(BaseModel):
    """
    Chat query response model
    
    Example:
        {
            "answer": "Ya, kami punya Molly...",
            "query_type": "product_search",
            "response_time": 1.234,
            "confidence": 0.85,
            "sources": [...],
            "query_id": 42
        }
    """
    answer: str = Field(..., description="Chatbot's answer")
    query_type: str = Field(..., description="Type of query")
    response_time: float = Field(..., description="Response time in seconds")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[SourceInfo] = Field(default_factory=list, description="Retrieved sources")
    query_id: int = Field(..., description="Unique query ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Ya, kami punya berbagai koleksi Molly blind box...",
                "query_type": "product_search",
                "response_time": 1.234,
                "confidence": 0.85,
                "sources": [
                    {
                        "rank": 1,
                        "type": "product",
                        "product_name": "Molly Career Series",
                        "price": 145000.0
                    }
                ],
                "query_id": 42
            }
        }


class MetricsResponse(BaseModel):
    """Metrics response model"""
    total_queries: int = Field(..., description="Total number of queries")
    avg_response_time: float = Field(..., description="Average response time")
    query_types: Dict[str, int] = Field(..., description="Query type distribution")
    sessions: int = Field(..., description="Number of sessions")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Status: 'healthy' or 'unhealthy'")
    chatbot_initialized: Optional[bool] = Field(None, description="Chatbot init status")
    llm_ready: Optional[bool] = Field(None, description="LLM ready status")
    index_ready: Optional[bool] = Field(None, description="FAISS index ready status")
    total_queries: Optional[int] = Field(None, description="Total queries processed")
    timestamp: str = Field(..., description="Current timestamp")
    error: Optional[str] = Field(None, description="Error message if unhealthy")


class RefreshResponse(BaseModel):
    """Index refresh response model"""
    status: str = Field(..., description="Refresh status message")
    message: Optional[str] = Field(None, description="Additional message")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error detail message")
    timestamp: str = Field(..., description="Error timestamp")