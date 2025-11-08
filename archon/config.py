"""Configuration management for Archon V4/V6."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv


@dataclass
class ArchonConfig:
    """Archon configuration loaded from environment variables."""

    # LLM Configuration
    base_url: str
    api_key: str
    primary_model: str
    reasoner_model: str

    # OpenAI (for embeddings)
    openai_api_key: str

    # Supabase (for RAG)
    supabase_url: str
    supabase_key: str

    # Validation
    validation_timeout: int = 5

    # Checkpointing
    checkpoint_db: str = 'workbench/checkpoints.db'

    # Logfire
    send_to_logfire: str = 'never'

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'ArchonConfig':
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file

        Returns:
            ArchonConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Required fields
        required = {
            'BASE_URL': os.getenv('BASE_URL'),
            'LLM_API_KEY': os.getenv('LLM_API_KEY'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'SUPABASE_URL': os.getenv('SUPABASE_URL'),
            'SUPABASE_SERVICE_KEY': os.getenv('SUPABASE_SERVICE_KEY'),
        }

        # Check for missing required fields
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please check your .env file."
            )

        return cls(
            base_url=required['BASE_URL'],
            api_key=required['LLM_API_KEY'],
            primary_model=os.getenv('PRIMARY_MODEL', 'gpt-4o-mini'),
            reasoner_model=os.getenv('REASONER_MODEL', 'o3-mini'),
            openai_api_key=required['OPENAI_API_KEY'],
            supabase_url=required['SUPABASE_URL'],
            supabase_key=required['SUPABASE_SERVICE_KEY'],
            validation_timeout=int(os.getenv('VALIDATION_TIMEOUT', '5')),
            checkpoint_db=os.getenv('CHECKPOINT_DB', 'workbench/checkpoints.db'),
            send_to_logfire=os.getenv('LOGFIRE_SEND_TO_LOGFIRE', 'never'),
        )

    def is_ollama(self) -> bool:
        """Check if using Ollama (local models)."""
        return "localhost" in self.base_url.lower()

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        if self.validation_timeout < 1:
            raise ValueError("validation_timeout must be >= 1")

        if not self.checkpoint_db:
            raise ValueError("checkpoint_db cannot be empty")

        # Validate URLs
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid base_url: {self.base_url}")

        if not self.supabase_url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid supabase_url: {self.supabase_url}")
