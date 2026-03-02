"""Data models and enums for kkreview."""

from enum import Enum

from pydantic import BaseModel


class Language(str, Enum):
    PYTHON = "python"
    GO = "go"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    C = "c"
    CPP = "cpp"
    JAVA = "java"


class Category(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    LOGIC = "logic"
    QUALITY = "quality"
    DESIGN = "design"
    CONCURRENCY = "concurrency"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class HiddenIssue(BaseModel):
    id: int
    category: str
    subcategory: str
    severity: str  # "critical", "major", "minor"
    line_start: int
    line_end: int
    description: str
    explanation: str


class GeneratedChallenge(BaseModel):
    language: str
    title: str
    context: str
    code: str
    issues: list[HiddenIssue]


class FindingMatch(BaseModel):
    issue_id: int
    found: bool
    user_text: str
    quality: str  # "precise", "partial", "vague"


class EvaluationResult(BaseModel):
    matches: list[FindingMatch]
    false_positives: list[str]
    score: float
    found_count: int
    total_count: int
    feedback: str
    tips: list[str]
