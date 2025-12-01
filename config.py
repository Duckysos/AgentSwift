from dataclasses import dataclass


@dataclass
class ModelConfig:
    jd_model: str = "gemini-1.5-pro"
    matcher_model: str = "gemini-1.5-pro"
    writer_model: str = "gemini-1.5-flash"
    editor_model: str = "gemini-1.5-pro"
    max_retries: int = 2


@dataclass
class ValidationConfig:
    max_words: int = 1500


@dataclass
class ExportConfig:
    default_format: str = "md"

