"""Constants for Archon V4/V6."""

import re

# Embedding
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

# Validation
VALIDATION_ERROR_MARKER = "VALIDATION_ERROR:"
STDERR_MAX_LENGTH = 500
DEFAULT_VALIDATION_TIMEOUT = 5

# RAG
DEFAULT_RAG_RESULTS = 5

# Common imports expected in AI agent code
COMMON_IMPORTS = frozenset({
    'pydantic_ai', 'pydantic', 'openai', 'anthropic', 'langgraph',
    'crewai', 'autogen', 'asyncio', 'typing', 'dataclasses',
    'os', 'sys', 'json', 're', 'pathlib', 'dotenv'
})

# Dangerous code patterns (pattern, warning message)
DANGEROUS_PATTERNS = [
    (r'os\.system\s*\(', 'os.system() usage detected - potential security risk'),
    (r'eval\s*\(', 'eval() usage detected - code injection risk'),
    (r'exec\s*\(', 'exec() usage detected - code injection risk'),
    (r'__import__\s*\(', 'Dynamic import with __import__() - review needed'),
    (r'open\s*\([^)]*["\']w["\']', 'File write operations detected - review needed'),
    (r'subprocess\.(call|run|Popen)', 'Subprocess execution detected - review needed'),
]

# Compiled regex patterns for performance
COMPILED_DANGEROUS_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), warning)
    for pattern, warning in DANGEROUS_PATTERNS
]
