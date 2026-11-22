from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    document_count: int
    segment_count: int
    embedding_model: str
    chunk_method: str
    chunk_size: int
    chunk_overlap: int
    retrieval_strategy: str
    top_k: int
    similarity_threshold: float
    created_by: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    embedding_model: str = "text-embedding-ada-002"
    chunk_method: str = "fixed"
    chunk_size: int = Field(500, ge=50, le=4000)
    chunk_overlap: int = Field(50, ge=0, le=500)
    retrieval_strategy: str = "hybrid"
    top_k: int = Field(5, ge=1, le=50)
    similarity_threshold: float = Field(0.7, ge=0, le=1)


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    embedding_model: str | None = None
    chunk_method: str | None = None
    chunk_size: int | None = Field(None, ge=50, le=4000)
    chunk_overlap: int | None = Field(None, ge=0, le=500)
    retrieval_strategy: str | None = None
    top_k: int | None = Field(None, ge=1, le=50)
    similarity_threshold: float | None = Field(None, ge=0, le=1)


class DocumentRead(BaseModel):
    id: int
    knowledge_base_id: int
    file_name: str
    file_type: str
    file_size: str | None = None
    status: str
    segment_count: int
    word_count: int
    error_message: str | None = None
    uploaded_by: str | None = None
    processed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentUpload(BaseModel):
    file_name: str = Field(min_length=1, max_length=500)
    file_type: str = "txt"
    content: str = Field(min_length=1)
    file_size: str | None = None
    minio_path: str | None = None


class SegmentRead(BaseModel):
    id: int
    knowledge_base_id: int
    document_id: int
    position: int
    content: str
    word_count: int
    token_count: int
    hit_count: int

    model_config = {"from_attributes": True}


class SegmentUpdate(BaseModel):
    content: str = Field(min_length=1)


class RetrievalTestRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int | None = Field(None, ge=1, le=50)


class RetrievalHit(BaseModel):
    segment_id: int
    document_id: int
    content: str
    score: float


class RetrievalTestResult(BaseModel):
    knowledge_base_id: int
    query: str
    hits: list[RetrievalHit] = []


class ReindexResult(BaseModel):
    knowledge_base_id: int
    document_count: int
    segment_count: int
    status: str
