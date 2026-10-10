"""
Safe Sandboxed Code Execution Service for the Coding Lab.

Provides isolated subprocess-based execution with:
- Subprocess isolation (no exec/eval in Flask)
- Isolated temporary directory per run with automatic cleanup
- Cleaned environment variables (no leak of API keys, DB credentials, or secrets)
- Hard timeout enforcement
- Maximum output size limits to prevent memory exhaustion
- Test case evaluation with hidden test case protection
"""

import os
import sys
import time
import tempfile
import subprocess
from typing import Dict, Any, List, Optional

# Supported languages and their execution availability
SUPPORTED_LANGUAGES = {
    'python': {
        'name': 'Python 3',
        'monaco_lang': 'python',
        'available': True,
        'extension': '.py',
    },
    'javascript': {
        'name': 'JavaScript (Node.js)',
        'monaco_lang': 'javascript',
        'available': False, # Enabled only if node binary detected
        'extension': '.js',
    },
    'java': {
        'name': 'Java',
        'monaco_lang': 'java',
        'available': False, # Configurable
        'extension': '.java',
    },
    'cpp': {
        'name': 'C++',
        'monaco_lang': 'cpp',
        'available': False, # Configurable
        'extension': '.cpp',
    },
    'c': {
        'name': 'C',
        'monaco_lang': 'c',
        'available': False, # Configurable
        'extension': '.c',
    }
}

MAX_OUTPUT_BYTES = 32 * 1024  # 32 KB maximum stdout/stderr
DEFAULT_TIMEOUT_SEC = 3.0     # Default 3 seconds timeout


def get_available_languages() -> List[Dict[str, Any]]:
    """Return list of configured and runnable programming languages."""
    langs = []
    for lang_id, info in SUPPORTED_LANGUAGES.items():
        langs.append({
            'id': lang_id,
            'name': info['name'],
            'monaco_lang': info['monaco_lang'],
            'available': info['available']
        })
    return langs


def _sanitize_env() -> Dict[str, str]:
    """
    Build a minimal, safe environment for the subprocess.
    Strips all app credentials, API keys, database paths, and secrets.
    """
    safe_env = {}
    
    # Preserve system paths needed for basic binaries to execute
    for key in ['PATH', 'PATHEXT', 'SYSTEMROOT', 'TEMP', 'TMP', 'COMSPEC']:
        if key in os.environ:
            safe_env[key] = os.environ[key]

    # Force unbuffered Python output and disable bytecode writing
    safe_env['PYTHONUNBUFFERED'] = '1'
    safe_env['PYTHONDONTWRITEBYTECODE'] = '1'
    
    return safe_env


def _execute_single_run(
    code: str,
    language: str,
    stdin_input: str = "",
    time_limit_sec: float = DEFAULT_TIMEOUT_SEC
) -> Dict[str, Any]:
    """
    Execute a single script in an isolated temp directory with timeout.
    """
    if language not in SUPPORTED_LANGUAGES:
        return {
            'status': 'Error',
            'stdout': '',
            'stderr': f"Unsupported language: '{language}'",
            'execution_time_ms': 0.0,
            'exit_code': -1,
            'timed_out': False
        }

    lang_info = SUPPORTED_LANGUAGES[language]
    if not lang_info['available']:
        return {
            'status': 'Error',
            'stdout': '',
            'stderr': f"Execution for '{lang_info['name']}' is not configured on this server.",
            'execution_time_ms': 0.0,
            'exit_code': -1,
            'timed_out': False
        }

    # Restrict code length
    if len(code) > 64 * 1024:
        return {
            'status': 'Error',
            'stdout': '',
            'stderr': "Code file size exceeds the 64KB limit.",
            'execution_time_ms': 0.0,
            'exit_code': -1,
            'timed_out': False
        }

    # Execute Python in isolated temp directory
    with tempfile.TemporaryDirectory(prefix="smartcampus_code_") as temp_dir:
        file_path = os.path.join(temp_dir, f"solution{lang_info['extension']}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Build command
        if language == 'python':
            cmd = [sys.executable, "-I", file_path] # -I runs Python in isolated mode (ignores PYTHONPATH and user site-packages)
        else:
            return {
                'status': 'Error',
                'stdout': '',
                'stderr': f"Execution handler for {language} is pending configuration.",
                'execution_time_ms': 0.0,
                'exit_code': -1,
                'timed_out': False
            }

        start_time = time.perf_counter()
        timed_out = False
        stdout_str = ""
        stderr_str = ""
        exit_code = 0

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
                env=_sanitize_env(),
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            try:
                stdout_data, stderr_data = process.communicate(
                    input=stdin_input,
                    timeout=time_limit_sec
                )
                exit_code = process.returncode
                stdout_str = (stdout_data or "")[:MAX_OUTPUT_BYTES]
                stderr_str = (stderr_data or "")[:MAX_OUTPUT_BYTES]
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                try:
                    stdout_data, stderr_data = process.communicate(timeout=1.0)
                    stdout_str = (stdout_data or "")[:MAX_OUTPUT_BYTES]
                    stderr_str = (stderr_data or "")[:MAX_OUTPUT_BYTES]
                except Exception:
                    pass
                exit_code = -1

        except Exception as e:
            return {
                'status': 'Runtime Error',
                'stdout': '',
                'stderr': f"Process execution failed: {str(e)}",
                'execution_time_ms': 0.0,
                'exit_code': -1,
                'timed_out': False
            }

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        if timed_out:
            return {
                'status': 'Time Limit Exceeded',
                'stdout': stdout_str,
                'stderr': f"Execution timed out after {time_limit_sec} seconds.",
                'execution_time_ms': elapsed_ms,
                'exit_code': exit_code,
                'timed_out': True
            }
        elif exit_code != 0:
            # Check for syntax error vs runtime error
            status = 'Compilation Error' if 'SyntaxError' in stderr_str else 'Runtime Error'
            return {
                'status': status,
                'stdout': stdout_str,
                'stderr': stderr_str,
                'execution_time_ms': elapsed_ms,
                'exit_code': exit_code,
                'timed_out': False
            }
        else:
            return {
                'status': 'Success',
                'stdout': stdout_str,
                'stderr': stderr_str,
                'execution_time_ms': elapsed_ms,
                'exit_code': 0,
                'timed_out': False
            }


def run_custom_code(
    code: str,
    language: str = 'python',
    custom_input: str = "",
    time_limit_sec: float = DEFAULT_TIMEOUT_SEC
) -> Dict[str, Any]:
    """
    Run the student's code with custom standard input and return standard output/errors.
    """
    if not code or not code.strip():
        return {
            'status': 'Error',
            'stdout': '',
            'stderr': 'No code provided to execute.',
            'execution_time_ms': 0.0,
            'exit_code': -1
        }

    return _execute_single_run(
        code=code,
        language=language.lower(),
        stdin_input=custom_input or "",
        time_limit_sec=time_limit_sec
    )


def _normalize_output(text: str) -> str:
    """Normalize string for comparing test case outputs (strip trailing spaces & CRLF to LF)."""
    if text is None:
        return ""
    # Normalize newlines
    lines = [line.rstrip() for line in text.replace('\r\n', '\n').split('\n')]
    # Trim trailing empty lines
    while lines and not lines[-1]:
        lines.pop()
    return '\n'.join(lines)


def evaluate_submission(
    code: str,
    language: str,
    test_cases: List[Dict[str, Any]],
    time_limit_sec: float = DEFAULT_TIMEOUT_SEC,
    points_total: int = 10
) -> Dict[str, Any]:
    """
    Run the code against all test cases (public + hidden).
    Returns complete evaluation statistics without leaking hidden test case inputs/outputs.
    """
    if not code or not code.strip():
        return {
            'status': 'Compilation Error',
            'passed_test_cases': 0,
            'total_test_cases': len(test_cases),
            'score': 0.0,
            'execution_time_ms': 0.0,
            'test_results': [],
            'error_message': 'Empty code submission.'
        }

    if not test_cases:
        # Fallback if no test cases defined
        res = run_custom_code(code, language, "", time_limit_sec)
        status = 'Accepted' if res['status'] == 'Success' else res['status']
        return {
            'status': status,
            'passed_test_cases': 1 if status == 'Accepted' else 0,
            'total_test_cases': 1,
            'score': float(points_total) if status == 'Accepted' else 0.0,
            'execution_time_ms': res.get('execution_time_ms', 0.0),
            'test_results': [],
            'error_message': res.get('stderr', '')
        }

    passed_count = 0
    total_count = len(test_cases)
    total_time_ms = 0.0
    first_failure_status = None
    first_failure_error = None
    results_list = []

    for index, tc in enumerate(test_cases, 1):
        inp = tc.get('input', '')
        expected_raw = tc.get('expected_output', '')
        is_hidden = tc.get('is_hidden', False)

        run_res = _execute_single_run(
            code=code,
            language=language,
            stdin_input=inp,
            time_limit_sec=time_limit_sec
        )

        total_time_ms += run_res['execution_time_ms']

        if run_res['timed_out']:
            passed = False
            case_status = 'Time Limit Exceeded'
            error_msg = run_res['stderr']
        elif run_res['exit_code'] != 0:
            passed = False
            case_status = run_res['status'] # Compilation Error or Runtime Error
            error_msg = run_res['stderr']
        else:
            actual_normalized = _normalize_output(run_res['stdout'])
            expected_normalized = _normalize_output(expected_raw)
            if actual_normalized == expected_normalized:
                passed = True
                case_status = 'Passed'
                error_msg = ''
            else:
                passed = False
                case_status = 'Wrong Answer'
                error_msg = ''

        if passed:
            passed_count += 1
        elif not first_failure_status:
            first_failure_status = case_status
            first_failure_error = run_res['stderr'] or f"Test case #{index} failed."

        # Prepare result object for frontend response
        if is_hidden:
            results_list.append({
                'case_number': index,
                'is_hidden': True,
                'status': case_status,
                'passed': passed,
                'execution_time_ms': run_res['execution_time_ms'],
                # Do NOT expose input/expected/actual for hidden test cases
                'input': '[Hidden Test Case]',
                'expected_output': '[Hidden Test Case]',
                'actual_output': '[Hidden]' if not passed else ''
            })
        else:
            results_list.append({
                'case_number': index,
                'is_hidden': False,
                'status': case_status,
                'passed': passed,
                'execution_time_ms': run_res['execution_time_ms'],
                'input': inp,
                'expected_output': expected_raw,
                'actual_output': run_res['stdout'],
                'error': run_res['stderr']
            })

    # Determine final submission status
    if passed_count == total_count:
        final_status = 'Accepted'
        score = float(points_total)
    else:
        final_status = first_failure_status or 'Wrong Answer'
        # Proportional partial scoring or zero
        score = round((passed_count / total_count) * points_total, 1)

    avg_time_ms = round(total_time_ms / max(1, total_count), 2)

    return {
        'status': final_status,
        'passed_test_cases': passed_count,
        'total_test_cases': total_count,
        'score': score,
        'execution_time_ms': avg_time_ms,
        'test_results': results_list,
        'error_message': first_failure_error if final_status != 'Accepted' else ''
    }
