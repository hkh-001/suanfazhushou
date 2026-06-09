from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_topics: int
    started_topics: int
    mastered_topics: int
    learning_topics: int
    progress_percent: int
