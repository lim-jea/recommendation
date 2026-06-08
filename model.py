from pydantic import BaseModel


class UserPreference(BaseModel):
    genres: list[str]
    keywords: list[str]
    exclude_ids: list[int] | None = None


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class ReadUpdate(BaseModel):
    novel_id: int


class RecommendationResult(BaseModel):
    novel_name: str
    novel_url: str