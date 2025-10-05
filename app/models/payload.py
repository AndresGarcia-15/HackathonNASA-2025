from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class GeneratedMeta(BaseModel):
    mode: str
    fallback_chain: List[Dict[str, Any]] = []
    final_source: Optional[str] = None
    llm_used: bool | None = None
    tokens_sampled: Optional[int] = None

class GeneratedBlock(BaseModel):
    title: str
    description: str
    meta: GeneratedMeta

class ArticleItem(BaseModel):
    id: str
    title: Optional[str]
    rank_score: float
    organism: Optional[str] = None
    project_type: Optional[str] = None
    release_date: Optional[str] = None
    top_keywords: List[str] = []

class ArticlesBlock(BaseModel):
    important: List[ArticleItem]
    less_relevant: List[ArticleItem]
    page_items: List[ArticleItem]

class EmergingTopicSample(BaseModel):
    id: str
    title: Optional[str]

class EmergingTopic(BaseModel):
    topic: str
    subset_occurrences: int
    global_occurrences: int
    sample_studies: List[EmergingTopicSample]

class TopicsBlock(BaseModel):
    emerging: List[EmergingTopic]
    frequent_subset: List[Dict[str, Any]]
    by_topic_index: Dict[str, List[str]]

class DebugBlock(BaseModel):
    ranking_preview: List[Dict[str, Any]]
    llm_meta: Dict[str, Any]
    generation_time_sec: float
    query_terms: List[str] | None = None
    studies_full_count: Optional[int] = None
    fields_per_record: Optional[int] = None

class FiltersEcho(BaseModel):
    organism: List[str] = []
    project_type: List[str] = []
    keywords: List[str] = []
    q: Optional[str] = None
    query_params: Optional[str] = None

class DataBlock(BaseModel):
    studies_full: List[Dict[str, Any]]
    total_full: int

class CountsBlock(BaseModel):
    total_studies: int
    important: int
    less_relevant: int

class PayloadV2(BaseModel):
    filters: FiltersEcho
    generated: GeneratedBlock
    counts: CountsBlock
    articles: ArticlesBlock
    topics: TopicsBlock
    debug: DebugBlock
    data: Optional[DataBlock] = None
    exported_at: str
