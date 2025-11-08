"""Code Validator for Archon V4."""

import ast
import asyncio
import bisect
import tempfile
import os
import re
from typing import Tuple, List, Dict, Optional, Set
from dataclasses import dataclass, field
import sys

from archon.constants import (
    COMMON_IMPORTS,
    COMPILED_DANGEROUS_PATTERNS,
    VALIDATION_ERROR_MARKER,
    STDERR_MAX_LENGTH,
    DEFAULT_VALIDATION_TIMEOUT
)


@dataclass
class ValidationResult:
    """Code validation result."""
    is_valid: bool
    message: str
    details: Dict = field(default_factory=dict)


class CodeValidator:
    """Validates generated Python code for correctness and safety."""

    def __init__(self, timeout: int = DEFAULT_VALIDATION_TIMEOUT):
        self.timeout = timeout
        self._checked_imports: Set[str] = set()  # Cache for import checking

    def _parse_or_skip(self, code: str) -> Optional[ast.AST]:
        """Parse code, return None if syntax invalid."""
        try:
            return ast.parse(code)
        except SyntaxError:
            return None

    async def validate_syntax(self, code: str) -> ValidationResult:
        """Validate Python syntax via AST parsing."""
        try:
            ast.parse(code)
            return ValidationResult(True, "Syntax is valid", {"syntax_tree": "parsed successfully"})
        except SyntaxError as e:
            return ValidationResult(
                False,
                f"Syntax error at line {e.lineno}: {e.msg}",
                {"line": e.lineno, "offset": e.offset, "text": e.text}
            )
        except Exception as e:
            return ValidationResult(False, f"Parsing error: {str(e)}", {"error_type": type(e).__name__})

    async def validate_imports(self, code: str) -> ValidationResult:
        """Check if all imports are available or commonly used in AI agents."""
        tree = self._parse_or_skip(code)
        if tree is None:
            return ValidationResult(True, "Skipped (syntax error)")

        missing_imports = []
        all_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    all_imports.append(module_name)
                    if module_name not in COMMON_IMPORTS and module_name not in self._checked_imports:
                        try:
                            __import__(module_name)
                            self._checked_imports.add(module_name)
                        except ImportError:
                            missing_imports.append(module_name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    all_imports.append(module_name)
                    if module_name not in COMMON_IMPORTS and module_name not in self._checked_imports:
                        try:
                            __import__(module_name)
                            self._checked_imports.add(module_name)
                        except ImportError:
                            missing_imports.append(module_name)

        unique_imports = set(all_imports)
        unique_missing = set(missing_imports)

        if unique_missing:
            return ValidationResult(
                False,
                f"Missing imports: {', '.join(unique_missing)}",
                {"missing": list(unique_missing), "all_imports": list(unique_imports)}
            )

        return ValidationResult(
            True,
            f"All {len(unique_imports)} imports are valid",
            {"imports": list(unique_imports)}
        )

    async def check_for_dangerous_patterns(self, code: str) -> ValidationResult:
        """Check for potentially dangerous code patterns."""
        # Pre-calculate line starts for O(n log n) line number lookup
        line_starts = [0] + [m.end() for m in re.finditer(r'\n', code)]

        issues = []
        for compiled_pattern, warning in COMPILED_DANGEROUS_PATTERNS:
            for match in compiled_pattern.finditer(code):
                line_num = bisect.bisect_right(line_starts, match.start())
                issues.append({
                    'pattern': compiled_pattern.pattern,
                    'warning': warning,
                    'line': line_num
                })

        if issues:
            return ValidationResult(
                False,
                f"Found {len(issues)} potentially dangerous pattern(s)",
                {"issues": issues}
            )

        return ValidationResult(True, "No dangerous patterns detected")

    async def validate_agent_structure(self, code: str) -> ValidationResult:
        """Validate that the code contains proper agent structure."""
        tree = self._parse_or_skip(code)
        if tree is None:
            return ValidationResult(True, "Skipped (syntax error)")

        has_agent_definition = False
        has_system_prompt = False
        agent_names = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['Agent', 'CrewAgent', 'AutoGenAgent']:
                    has_agent_definition = True

            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and 'agent' in target.id.lower():
                        agent_names.append(target.id)
                        has_agent_definition = True
                    if isinstance(target, ast.Name) and 'system_prompt' in target.id:
                        has_system_prompt = True

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Call)):
                for keyword in getattr(node, 'keywords', []):
                    if keyword.arg == 'system_prompt':
                        has_system_prompt = True

        issues = []
        if not has_agent_definition:
            issues.append("No agent definition found (expected Agent, CrewAgent, etc.)")
        if not has_system_prompt:
            issues.append("No system_prompt found - agents should have instructions")

        if issues:
            return ValidationResult(
                False,
                f"Agent structure issues: {'; '.join(issues)}",
                {"issues": issues, "agent_names": agent_names}
            )

        return ValidationResult(
            True,
            f"Valid agent structure (found {len(agent_names)} agent(s))",
            {"agent_names": agent_names}
        )

    async def run_in_sandbox(self, code: str) -> ValidationResult:
        """Run code in isolated environment with timeout."""
        indented_code = '\n'.join('    ' + line for line in code.split('\n'))
        wrapped_code = f"""
import sys
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.timeout})

try:
{indented_code}
except Exception as e:
    print(f"{VALIDATION_ERROR_MARKER}{{type(e).__name__}}: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
finally:
    signal.alarm(0)
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(wrapped_code)
            temp_file = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout + 1
                )

                stderr_str = stderr.decode('utf-8', errors='ignore')
                stdout_str = stdout.decode('utf-8', errors='ignore')

                if VALIDATION_ERROR_MARKER in stderr_str:
                    error_line = next(
                        (line for line in stderr_str.split('\n') if VALIDATION_ERROR_MARKER in line),
                        ''
                    )
                    return ValidationResult(
                        False,
                        error_line.replace(VALIDATION_ERROR_MARKER, '').strip(),
                        {"stderr": stderr_str, "stdout": stdout_str}
                    )

                if proc.returncode != 0:
                    return ValidationResult(
                        False,
                        f"Execution failed with code {proc.returncode}",
                        {"stderr": stderr_str, "stdout": stdout_str}
                    )

                return ValidationResult(
                    True,
                    "Code executed successfully",
                    {"stdout": stdout_str, "stderr": stderr_str}
                )

            except asyncio.TimeoutError:
                proc.kill()
                return ValidationResult(False, f"Execution timeout ({self.timeout}s)")

        except Exception as e:
            return ValidationResult(False, f"Sandbox error: {str(e)}", {"error_type": type(e).__name__})
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    async def validate_all(
        self, code: str, skip_execution: bool = False
    ) -> Tuple[bool, List[Tuple[str, ValidationResult]]]:
        """Run all validation checks on code."""
        results = []

        syntax_result = await self.validate_syntax(code)
        results.append(("Syntax", syntax_result))

        if not syntax_result.is_valid:
            return False, results

        import_result = await self.validate_imports(code)
        results.append(("Imports", import_result))

        danger_result = await self.check_for_dangerous_patterns(code)
        results.append(("Security", danger_result))

        structure_result = await self.validate_agent_structure(code)
        results.append(("Structure", structure_result))

        if not skip_execution:
            execution_result = await self.run_in_sandbox(code)
            results.append(("Execution", execution_result))

        all_valid = all(result.is_valid for _, result in results)
        return all_valid, results


def format_validation_feedback(results: List[Tuple[str, ValidationResult]]) -> str:
    """Format validation results into human-readable feedback."""
    feedback_lines = ["## Code Validation Results\n"]
    failed_checks = [name for name, result in results if not result.is_valid]

    if not failed_checks:
        feedback_lines.append("✅ **All validation checks passed!**\n")
        for name, result in results:
            feedback_lines.append(f"- {name}: {result.message}")
    else:
        feedback_lines.append(f"❌ **{len(failed_checks)} validation check(s) failed:**\n")

        for name, result in results:
            status = "✅" if result.is_valid else "❌"
            feedback_lines.append(f"{status} **{name}**: {result.message}")

            if not result.is_valid and result.details:
                if 'issues' in result.details:
                    for issue in result.details['issues']:
                        if isinstance(issue, dict):
                            feedback_lines.append(f"  - Line {issue.get('line', '?')}: {issue.get('warning', issue)}")
                        else:
                            feedback_lines.append(f"  - {issue}")
                elif 'stderr' in result.details and result.details['stderr']:
                    feedback_lines.append(f"  ```\n{result.details['stderr'][:STDERR_MAX_LENGTH]}\n  ```")

    return "\n".join(feedback_lines)


async def validate_code(code: str, skip_execution: bool = False) -> Tuple[bool, str]:
    """Validate code and return formatted feedback."""
    validator = CodeValidator()
    is_valid, results = await validator.validate_all(code, skip_execution=skip_execution)
    feedback = format_validation_feedback(results)
    return is_valid, feedback
