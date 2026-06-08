from pydantic import BaseModel


class UserPreference(BaseModel):
    genres: list[str]
    keywords: list[str]


class RecommendationResult(BaseModel):
    novel_name: str
    novel_url: str