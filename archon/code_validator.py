"""
Code Validator for Archon V4

This module provides comprehensive validation for generated AI agent code,
including syntax checking, import validation, and sandbox execution.
"""

import ast
import asyncio
import tempfile
import os
import re
from typing import Tuple, List, Dict, Optional
import sys


class ValidationResult:
    """Result of code validation"""

    def __init__(self, is_valid: bool, message: str, details: Optional[Dict] = None):
        self.is_valid = is_valid
        self.message = message
        self.details = details or {}

    def __str__(self):
        return f"ValidationResult(valid={self.is_valid}, message='{self.message}')"


class CodeValidator:
    """Validates generated Python code for correctness and safety"""

    def __init__(self, timeout: int = 5):
        """
        Initialize code validator

        Args:
            timeout: Maximum seconds to allow code execution (default: 5)
        """
        self.timeout = timeout
        self.common_imports = {
            'pydantic_ai', 'pydantic', 'openai', 'anthropic', 'langgraph',
            'crewai', 'autogen', 'asyncio', 'typing', 'dataclasses',
            'os', 'sys', 'json', 're', 'pathlib', 'dotenv'
        }

    async def validate_syntax(self, code: str) -> ValidationResult:
        """
        Check if code has valid Python syntax

        Args:
            code: Python code string to validate

        Returns:
            ValidationResult with syntax check results
        """
        try:
            ast.parse(code)
            return ValidationResult(
                is_valid=True,
                message="Syntax is valid",
                details={"syntax_tree": "parsed successfully"}
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Syntax error at line {e.lineno}: {e.msg}",
                details={
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text
                }
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Parsing error: {str(e)}",
                details={"error_type": type(e).__name__}
            )

    async def validate_imports(self, code: str) -> ValidationResult:
        """
        Check if all imports are available or commonly used in AI agents

        Args:
            code: Python code string to check

        Returns:
            ValidationResult with import validation results
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # If syntax is invalid, skip import check (will be caught by validate_syntax)
            return ValidationResult(is_valid=True, message="Skipped (syntax error)")

        missing_imports = []
        all_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]  # Get top-level module
                    all_imports.append(module_name)

                    # Check if it's a common/expected import
                    if module_name not in self.common_imports:
                        # Try to import it
                        try:
                            __import__(module_name)
                        except ImportError:
                            missing_imports.append(module_name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    all_imports.append(module_name)

                    if module_name not in self.common_imports:
                        try:
                            __import__(module_name)
                        except ImportError:
                            missing_imports.append(module_name)

        if missing_imports:
            return ValidationResult(
                is_valid=False,
                message=f"Missing imports: {', '.join(set(missing_imports))}",
                details={
                    "missing": list(set(missing_imports)),
                    "all_imports": list(set(all_imports))
                }
            )

        return ValidationResult(
            is_valid=True,
            message=f"All {len(set(all_imports))} imports are valid",
            details={"imports": list(set(all_imports))}
        )

    async def check_for_dangerous_patterns(self, code: str) -> ValidationResult:
        """
        Check for potentially dangerous code patterns

        Args:
            code: Python code to analyze

        Returns:
            ValidationResult indicating if dangerous patterns were found
        """
        dangerous_patterns = [
            (r'os\.system\s*\(', 'os.system() usage detected - potential security risk'),
            (r'eval\s*\(', 'eval() usage detected - code injection risk'),
            (r'exec\s*\(', 'exec() usage detected - code injection risk'),
            (r'__import__\s*\(', 'Dynamic import with __import__() - review needed'),
            (r'open\s*\([^)]*["\']w["\']', 'File write operations detected - review needed'),
            (r'subprocess\.(call|run|Popen)', 'Subprocess execution detected - review needed'),
        ]

        issues = []
        for pattern, warning in dangerous_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                # Find line number
                line_num = code[:match.start()].count('\n') + 1
                issues.append({
                    'pattern': pattern,
                    'warning': warning,
                    'line': line_num
                })

        if issues:
            return ValidationResult(
                is_valid=False,
                message=f"Found {len(issues)} potentially dangerous pattern(s)",
                details={"issues": issues}
            )

        return ValidationResult(
            is_valid=True,
            message="No dangerous patterns detected",
            details={}
        )

    async def validate_agent_structure(self, code: str) -> ValidationResult:
        """
        Validate that the code contains proper agent structure

        Args:
            code: Python code to validate

        Returns:
            ValidationResult indicating if agent structure is valid
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ValidationResult(is_valid=True, message="Skipped (syntax error)")

        has_agent_definition = False
        has_system_prompt = False
        agent_names = []

        for node in ast.walk(tree):
            # Check for Agent instantiation
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in ['Agent', 'CrewAgent', 'AutoGenAgent']:
                    has_agent_definition = True

            # Check for agent assignment (e.g., agent = Agent(...))
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if 'agent' in target.id.lower():
                            agent_names.append(target.id)
                            has_agent_definition = True

            # Check for system_prompt
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and 'system_prompt' in target.id:
                        has_system_prompt = True

            # Check in function/class arguments
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
                is_valid=False,
                message=f"Agent structure issues: {'; '.join(issues)}",
                details={"issues": issues, "agent_names": agent_names}
            )

        return ValidationResult(
            is_valid=True,
            message=f"Valid agent structure (found {len(agent_names)} agent(s))",
            details={"agent_names": agent_names}
        )

    async def run_in_sandbox(self, code: str) -> ValidationResult:
        """
        Run code in isolated environment with timeout (basic version)

        Args:
            code: Python code to execute

        Returns:
            ValidationResult with execution results
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Add basic safety wrapper
            wrapped_code = f"""
import sys
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Execution timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm({self.timeout})

try:
{chr(10).join('    ' + line for line in code.split(chr(10)))}
except Exception as e:
    print(f"VALIDATION_ERROR: {{type(e).__name__}}: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
finally:
    signal.alarm(0)
"""
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

                if "VALIDATION_ERROR:" in stderr_str:
                    error_line = [line for line in stderr_str.split('\n') if 'VALIDATION_ERROR:' in line][0]
                    return ValidationResult(
                        is_valid=False,
                        message=error_line.replace('VALIDATION_ERROR:', '').strip(),
                        details={"stderr": stderr_str, "stdout": stdout_str}
                    )

                if proc.returncode != 0:
                    return ValidationResult(
                        is_valid=False,
                        message=f"Execution failed with code {proc.returncode}",
                        details={"stderr": stderr_str, "stdout": stdout_str}
                    )

                return ValidationResult(
                    is_valid=True,
                    message="Code executed successfully",
                    details={"stdout": stdout_str, "stderr": stderr_str}
                )

            except asyncio.TimeoutError:
                proc.kill()
                return ValidationResult(
                    is_valid=False,
                    message=f"Execution timeout ({self.timeout}s)",
                    details={}
                )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Sandbox error: {str(e)}",
                details={"error_type": type(e).__name__}
            )
        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass  # Ignore cleanup errors

    async def validate_all(self, code: str, skip_execution: bool = False) -> Tuple[bool, List[ValidationResult]]:
        """
        Run all validation checks on code

        Args:
            code: Python code to validate
            skip_execution: If True, skip sandbox execution (default: False)

        Returns:
            Tuple of (all_valid, list of ValidationResults)
        """
        results = []

        # 1. Syntax check
        syntax_result = await self.validate_syntax(code)
        results.append(("Syntax", syntax_result))

        if not syntax_result.is_valid:
            # If syntax is invalid, skip other checks
            return False, results

        # 2. Import check
        import_result = await self.validate_imports(code)
        results.append(("Imports", import_result))

        # 3. Dangerous patterns check
        danger_result = await self.check_for_dangerous_patterns(code)
        results.append(("Security", danger_result))

        # 4. Agent structure check
        structure_result = await self.validate_agent_structure(code)
        results.append(("Structure", structure_result))

        # 5. Sandbox execution (optional)
        if not skip_execution:
            execution_result = await self.run_in_sandbox(code)
            results.append(("Execution", execution_result))

        # Check if all results are valid
        all_valid = all(result.is_valid for _, result in results)

        return all_valid, results


def format_validation_feedback(results: List[Tuple[str, ValidationResult]]) -> str:
    """
    Format validation results into human-readable feedback

    Args:
        results: List of (check_name, ValidationResult) tuples

    Returns:
        Formatted feedback string
    """
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
                # Add details for failed checks
                if 'issues' in result.details:
                    for issue in result.details['issues']:
                        if isinstance(issue, dict):
                            feedback_lines.append(f"  - Line {issue.get('line', '?')}: {issue.get('warning', issue)}")
                        else:
                            feedback_lines.append(f"  - {issue}")
                elif 'stderr' in result.details and result.details['stderr']:
                    feedback_lines.append(f"  ```\n{result.details['stderr'][:500]}\n  ```")

    return "\n".join(feedback_lines)


# Convenience function for quick validation
async def validate_code(code: str, skip_execution: bool = False) -> Tuple[bool, str]:
    """
    Validate code and return formatted feedback

    Args:
        code: Python code to validate
        skip_execution: If True, skip sandbox execution

    Returns:
        Tuple of (is_valid, feedback_message)
    """
    validator = CodeValidator()
    is_valid, results = await validator.validate_all(code, skip_execution=skip_execution)
    feedback = format_validation_feedback(results)
    return is_valid, feedback
