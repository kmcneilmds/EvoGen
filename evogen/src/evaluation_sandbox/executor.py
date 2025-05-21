import subprocess
import time
import tempfile
import os
import uuid
import json
from typing import List, Any, Dict

from evogen.src.common.data_structures import CandidateSolution, ProblemDefinition, RawTestResult, TestStatus

def execute_python_solution(
    solution: CandidateSolution, 
    problem_def: ProblemDefinition
) -> List[RawTestResult]:
    """
    Executes a Python CandidateSolution against test cases defined in ProblemDefinition.
    For MVP, this runs Python code using subprocess.

    Args:
        solution: The CandidateSolution to evaluate.
        problem_def: The ProblemDefinition containing test cases and evaluation signature.

    Returns:
        A list of RawTestResult objects, one for each test case.
    """
    results: List[RawTestResult] = []
    
    # Basic parsing of the function signature to get the function name
    # E.g., "def solve(a: int, b: int) -> int:" -> "solve"
    # This is a simplification for MVP. Robust parsing would be more complex.
    try:
        eval_func_name = problem_def.evaluation_function_signature.split("def ")[1].split("(")[0].strip()
    except IndexError:
        # Fallback or error if signature is not as expected
        # For MVP, we might hardcode or raise an error if this parsing fails
        # For now, let's assume a common name like 'solve' if parsing fails,
        # or better, make it a requirement for ProblemDefinition for MVP.
        # Let's assume it's 'solve' if parsing fails, and it's documented as such for MVP.
        # A better MVP approach might be to require problem_def.evaluation_function_name
        print(f"Warning: Could not parse function name from signature: {problem_def.evaluation_function_signature}. Assuming 'solve'.")
        eval_func_name = "solve"


    for test_case in problem_def.initial_test_cases:
        test_case_id = test_case.get("test_case_id", str(uuid.uuid4()))
        test_input = test_case.get("input")
        # expected_output = test_case.get("expected_output") # Not used for execution, but for Metrics module

        raw_result = RawTestResult(
            solution_id=solution.id,
            test_case_id=test_case_id,
            status=TestStatus.FAILURE_RUNTIME_ERROR # Default status
        )

        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            tmp_file_name = tmp_file.name
            
            # Write the solution's code
            tmp_file.write(solution.code + "\n\n")
            
            # Prepare the function call with the current test input
            # This is a simplified way for MVP. Assumes input is a list of args.
            # More robust: handle different input types, kwargs, etc.
            input_args_str = ", ".join(map(repr, test_input)) if isinstance(test_input, list) else repr(test_input)
            
            # Write the calling scaffold
            # We'll print the result in a specific format (JSON) to parse it easily.
            tmp_file.write(f"import json\n")
            tmp_file.write(f"if __name__ == '__main__':\n")
            tmp_file.write(f"    try:\n")
            tmp_file.write(f"        result = {eval_func_name}(*{input_args_str if isinstance(test_input, list) else (input_args_str,)})\n")
            tmp_file.write(f"        print(json.dumps({{'output': result}}))\n") # Output as JSON
            tmp_file.write(f"    except Exception as e:\n")
            # Print error to stderr for capture, if any runtime error in the solution code
            tmp_file.write(f"        import sys\n")
            tmp_file.write(f"        print(str(e), file=sys.stderr)\n")
            tmp_file.write(f"        sys.exit(1)\n") # Exit with error code

        start_time = time.time()
        try:
            # Execute the temporary file
            # Timeout is important for real scenarios, but simplified for MVP's first pass
            process = subprocess.run(
                ["python", tmp_file_name],
                capture_output=True,
                text=True,
                timeout=10 # MVP timeout: 10 seconds
            )
            raw_result.execution_time_ms = (time.time() - start_time) * 1000
            raw_result.stdout = process.stdout.strip()
            raw_result.stderr = process.stderr.strip()

            if process.returncode == 0:
                try:
                    # Try to parse the JSON output from stdout
                    output_data = json.loads(raw_result.stdout)
                    raw_result.actual_output = output_data.get('output')
                    raw_result.status = TestStatus.SUCCESS # Tentative, Metrics will confirm correctness
                except json.JSONDecodeError:
                    raw_result.stderr += "\nError: Output was not valid JSON."
                    raw_result.status = TestStatus.FAILURE_RUNTIME_ERROR 
            else:
                raw_result.status = TestStatus.FAILURE_RUNTIME_ERROR
        
        except subprocess.TimeoutExpired:
            raw_result.execution_time_ms = (time.time() - start_time) * 1000
            raw_result.status = TestStatus.FAILURE_TIMEOUT
            raw_result.stderr = "Execution timed out."
        except Exception as e:
            raw_result.execution_time_ms = (time.time() - start_time) * 1000
            raw_result.status = TestStatus.FAILURE_RUNTIME_ERROR
            raw_result.stderr = f"Sandbox execution error: {str(e)}"
        finally:
            os.remove(tmp_file_name) # Clean up the temporary file
        
        results.append(raw_result)
        
    return results

if __name__ == '__main__':
    # Create dummy Solution and ProblemDefinition for testing
    problem_id = uuid.uuid4()
    sol_id = uuid.uuid4()

    # Test case 1: Correct simple addition
    solution_code_correct = "def solve(a, b):\n    return a + b"
    # Test case 2: Code with a runtime error
    solution_code_runtime_error = "def solve(a, b):\n    return a / 0 # Division by zero"
    # Test case 3: Code that times out (simulated by sleep)
    solution_code_timeout = "import time\ndef solve(a,b):\n    time.sleep(15)\n    return a+b" # timeout is 10s

    problem = ProblemDefinition(
        id=problem_id,
        core_task="Test Execution",
        evaluation_function_signature="def solve(a, b):", # For MVP, ensure this is parsable or fixed
        initial_test_cases=[
            {"test_case_id": "tc_correct", "input": [5, 3], "expected_output": 8},
            {"test_case_id": "tc_runtime_error", "input": [1, 0], "expected_output": "Error"},
            {"test_case_id": "tc_timeout", "input": [1,1], "expected_output": "Timeout"}
        ]
    )

    solution_correct = CandidateSolution(id=sol_id, problem_id=problem_id, code=solution_code_correct)
    solution_error = CandidateSolution(id=uuid.uuid4(), problem_id=problem_id, code=solution_code_runtime_error)
    solution_timeout = CandidateSolution(id=uuid.uuid4(), problem_id=problem_id, code=solution_code_timeout)

    print("--- Testing correct solution ---")
    results_correct = execute_python_solution(solution_correct, problem)
    for res in results_correct:
        print(f"  TC_ID: {res.test_case_id}, Status: {res.status}, Output: {res.actual_output}, Time: {res.execution_time_ms:.2f}ms, Stderr: {res.stderr}")
        if res.test_case_id == "tc_correct":
             assert res.status == TestStatus.SUCCESS and res.actual_output == 8
        # The other test cases will also run with the correct code, likely producing valid output if the function is general
        # For this test, we only care about tc_correct's output with solution_correct
    
    print("\n--- Testing solution with runtime error ---")
    results_error = execute_python_solution(solution_error, problem)
    for res in results_error:
        print(f"  TC_ID: {res.test_case_id}, Status: {res.status}, Output: {res.actual_output}, Time: {res.execution_time_ms:.2f}ms, Stderr: {res.stderr}")
        if res.test_case_id == "tc_runtime_error": # This is the specific case we expect to fail
            assert res.status == TestStatus.FAILURE_RUNTIME_ERROR and "division by zero" in res.stderr

    print("\n--- Testing solution that should timeout ---")
    # Only run the timeout test case for the timeout solution to save time
    problem_timeout_single_tc = ProblemDefinition(
        id=problem_id,
        core_task="Test Timeout Execution",
        evaluation_function_signature="def solve(a, b):",
        initial_test_cases=[
            {"test_case_id": "tc_timeout_specific", "input": [1,1], "expected_output": "Timeout"}
        ]
    )
    results_timeout = execute_python_solution(solution_timeout, problem_timeout_single_tc)
    for res in results_timeout:
        print(f"  TC_ID: {res.test_case_id}, Status: {res.status}, Output: {res.actual_output}, Time: {res.execution_time_ms:.2f}ms, Stderr: {res.stderr}")
        assert res.status == TestStatus.FAILURE_TIMEOUT

    print("\nSelf-tests completed.")
