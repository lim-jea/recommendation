from pydantic import BaseModel


class UserPreference(BaseModel):
    id: int
    item: str


class RecommendationResult(BaseModel):
    novel_name: str
    novel_url: str