from dataclasses import dataclass


@dataclass(frozen=True)
class Post:
    source: str
    post_id: str
    title: str
    content: str
    author: str
    created_at: int


@dataclass(frozen=True)
class DemandMatch:
    post: Post
    category: str
    intent: str
    keywords: tuple[str, ...]
    score: float

