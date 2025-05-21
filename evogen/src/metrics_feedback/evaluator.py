import uuid
from typing import List, Dict, Any, Optional

from evogen.src.common.data_structures import (
    RawTestResult, 
    ProblemDefinition, 
    AggregatedEvaluationResult,
    TestStatus
)

def evaluate_results(
    raw_results: List[RawTestResult], 
    problem_def: ProblemDefinition,
    solution_id: uuid.UUID # Pass solution_id explicitly
) -> AggregatedEvaluationResult:
    """
    Evaluates a list of RawTestResults against expected outputs from ProblemDefinition.
    Calculates a simple fitness score and generates feedback for MVP.

    Args:
        raw_results: List of RawTestResult objects from the EvaluationSandbox.
        problem_def: The ProblemDefinition containing expected outputs for test cases.
        solution_id: The ID of the solution these results pertain to.

    Returns:
        An AggregatedEvaluationResult object.
    """
    
    num_tests = len(problem_def.initial_test_cases)
    if not num_tests: # Avoid division by zero if no test cases
        return AggregatedEvaluationResult(
            solution_id=solution_id,
            overall_fitness_score=0.0, # No tests, no score
            is_correct_on_all_tests=False,
            feedback_text="No test cases provided in ProblemDefinition.",
            feedback_structured={"error": "No test cases"}
        )

    correct_tests = 0
    total_execution_time_ms = 0
    all_tests_successful_runtime = True
    
    # Create a mapping from test_case_id to expected_output for easier lookup
    expected_outputs_map: Dict[Any, Any] = {
        tc.get("test_case_id"): tc.get("expected_output") 
        for tc in problem_def.initial_test_cases
    }

    detailed_feedback_parts = []

    for result in raw_results:
        if result.status == TestStatus.SUCCESS:
            total_execution_time_ms += result.execution_time_ms
            expected_output = expected_outputs_map.get(result.test_case_id)
            
            # Simple comparison for MVP. For complex objects, deep comparison would be needed.
            if result.actual_output == expected_output:
                correct_tests += 1
                detailed_feedback_parts.append(f"Test {result.test_case_id}: Correct.")
            else:
                detailed_feedback_parts.append(f"Test {result.test_case_id}: Incorrect output. Expected {expected_output}, Got {result.actual_output}.")
                all_tests_successful_runtime = False # Incorrect output is a form of failure
        elif result.status == TestStatus.FAILURE_TIMEOUT:
            detailed_feedback_parts.append(f"Test {result.test_case_id}: Timeout. {result.stderr}")
            all_tests_successful_runtime = False
        else: # FAILURE_RUNTIME_ERROR, FAILURE_COMPILATION (less relevant for Python MVP)
            detailed_feedback_parts.append(f"Test {result.test_case_id}: Failed with status {result.status}. Error: {result.stderr}")
            all_tests_successful_runtime = False

    is_correct_on_all_tests = (correct_tests == num_tests) and all_tests_successful_runtime

    # Simple fitness score for MVP:
    # 1.0 if all tests pass and are correct.
    # (correct_tests / num_tests) * 0.5 if some are correct but not all, or runtime errors occurred.
    # 0.0 if no tests are correct or major failures.
    # This can be refined significantly later.
    fitness_score = 0.0
    if is_correct_on_all_tests:
        fitness_score = 1.0
        # Could also factor in time for perfect solutions, e.g., score = 1.0 / (1 + avg_exec_time_seconds)
    elif correct_tests > 0 and all_tests_successful_runtime : # Some correct, no runtime errors in any
        fitness_score = (correct_tests / num_tests) * 0.7 # Penalize for not all correct
    elif correct_tests > 0 : # Some correct, but runtime errors in others
         fitness_score = (correct_tests / num_tests) * 0.3
    # else: fitness_score remains 0.0

    avg_execution_time_ms: Optional[float] = None
    if total_execution_time_ms > 0 and num_tests > 0 : # Could be num_successful_tests if only averaging those
        avg_execution_time_ms = total_execution_time_ms / len(raw_results) # Average over all attempted tests

    feedback_summary = f"{correct_tests}/{num_tests} tests correct. "
    if is_correct_on_all_tests:
        feedback_summary += "All tests passed successfully."
    elif all_tests_successful_runtime:
        feedback_summary += "Some tests failed due to incorrect output."
    else:
        feedback_summary += "Some tests failed due to runtime errors, timeouts, or incorrect output."
        
    feedback_text = feedback_summary + "\nDetails:\n" + "\n".join(detailed_feedback_parts)

    return AggregatedEvaluationResult(
        solution_id=solution_id,
        overall_fitness_score=fitness_score,
        is_correct_on_all_tests=is_correct_on_all_tests,
        avg_execution_time_ms=avg_execution_time_ms,
        feedback_text=feedback_text,
        feedback_structured={
            "num_total_tests": num_tests,
            "num_correct_tests": correct_tests,
            "all_tests_had_successful_runtime": all_tests_successful_runtime, # True if no timeouts/runtime errors
            "details": detailed_feedback_parts
        }
    )

if __name__ == '__main__':
    problem_id_test = uuid.uuid4()
    solution_id_test = uuid.uuid4()

    problem_for_eval = ProblemDefinition(
        id=problem_id_test,
        core_task="Evaluation Test",
        initial_test_cases=[
            {"test_case_id": "tc1", "input": [1,1], "expected_output": 2},
            {"test_case_id": "tc2", "input": [2,2], "expected_output": 4},
            {"test_case_id": "tc3", "input": [3,3], "expected_output": 7}, # Intentionally wrong expected for one
            {"test_case_id": "tc4", "input": [4,4], "expected_output": 8},
        ]
    )

    # Scenario 1: All correct
    results_all_correct = [
        RawTestResult(solution_id=solution_id_test, test_case_id="tc1", status=TestStatus.SUCCESS, actual_output=2, execution_time_ms=10),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc2", status=TestStatus.SUCCESS, actual_output=4, execution_time_ms=12),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc3", status=TestStatus.SUCCESS, actual_output=6, execution_time_ms=11), # Corrected actual output for tc3
        RawTestResult(solution_id=solution_id_test, test_case_id="tc4", status=TestStatus.SUCCESS, actual_output=8, execution_time_ms=10),
    ]
    # Modify problem_for_eval for this scenario to have correct expected output for tc3
    problem_for_eval.initial_test_cases[2]["expected_output"] = 6 
    agg_eval_correct = evaluate_results(results_all_correct, problem_for_eval, solution_id_test)
    print("--- Scenario: All Correct ---")
    print(f"  Fitness: {agg_eval_correct.overall_fitness_score}, All Correct: {agg_eval_correct.is_correct_on_all_tests}")
    print(f"  Feedback: {agg_eval_correct.feedback_text}")
    assert agg_eval_correct.is_correct_on_all_tests is True
    assert agg_eval_correct.overall_fitness_score == 1.0

    # Scenario 2: Some incorrect
    problem_for_eval.initial_test_cases[2]["expected_output"] = 7 # Restore intentionally wrong expected for tc3
    results_some_incorrect = [
        RawTestResult(solution_id=solution_id_test, test_case_id="tc1", status=TestStatus.SUCCESS, actual_output=2, execution_time_ms=10),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc2", status=TestStatus.SUCCESS, actual_output=4, execution_time_ms=12),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc3", status=TestStatus.SUCCESS, actual_output=6, execution_time_ms=11), # tc3 actual output is 6, expected is 7
        RawTestResult(solution_id=solution_id_test, test_case_id="tc4", status=TestStatus.SUCCESS, actual_output=8, execution_time_ms=10),
    ]
    agg_eval_some_incorrect = evaluate_results(results_some_incorrect, problem_for_eval, solution_id_test)
    print("\n--- Scenario: Some Incorrect ---")
    print(f"  Fitness: {agg_eval_some_incorrect.overall_fitness_score}, All Correct: {agg_eval_some_incorrect.is_correct_on_all_tests}")
    print(f"  Feedback: {agg_eval_some_incorrect.feedback_text}")
    assert agg_eval_some_incorrect.is_correct_on_all_tests is False
    assert agg_eval_some_incorrect.feedback_structured["num_correct_tests"] == 3
    
    # Scenario 3: Runtime error
    results_runtime_error = [
        RawTestResult(solution_id=solution_id_test, test_case_id="tc1", status=TestStatus.SUCCESS, actual_output=2, execution_time_ms=10),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc2", status=TestStatus.FAILURE_RUNTIME_ERROR, stderr="Big error!", execution_time_ms=5),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc3", status=TestStatus.SUCCESS, actual_output=6, execution_time_ms=11),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc4", status=TestStatus.SUCCESS, actual_output=8, execution_time_ms=10),
    ]
    agg_eval_runtime_error = evaluate_results(results_runtime_error, problem_for_eval, solution_id_test)
    print("\n--- Scenario: Runtime Error ---")
    print(f"  Fitness: {agg_eval_runtime_error.overall_fitness_score}, All Correct: {agg_eval_runtime_error.is_correct_on_all_tests}")
    print(f"  Feedback: {agg_eval_runtime_error.feedback_text}")
    assert agg_eval_runtime_error.is_correct_on_all_tests is False
    assert agg_eval_runtime_error.feedback_structured["all_tests_had_successful_runtime"] is False
    assert agg_eval_runtime_error.feedback_structured["num_correct_tests"] == 3 # tc2 failed runtime, tc3 output is 6 vs expected 7

    # Scenario 4: Timeout
    results_timeout = [
        RawTestResult(solution_id=solution_id_test, test_case_id="tc1", status=TestStatus.SUCCESS, actual_output=2, execution_time_ms=10),
        RawTestResult(solution_id=solution_id_test, test_case_id="tc2", status=TestStatus.FAILURE_TIMEOUT, stderr="Timed out!", execution_time_ms=10000),
    ]
    # Shorten problem def for this test
    problem_for_timeout_eval = ProblemDefinition(
        id=problem_id_test,
        core_task="Evaluation Test Timeout",
        initial_test_cases=[
            problem_for_eval.initial_test_cases[0], # tc1
            problem_for_eval.initial_test_cases[1], # tc2 (where timeout occurs)
        ]
    )
    agg_eval_timeout = evaluate_results(results_timeout, problem_for_timeout_eval, solution_id_test)
    print("\n--- Scenario: Timeout ---")
    print(f"  Fitness: {agg_eval_timeout.overall_fitness_score}, All Correct: {agg_eval_timeout.is_correct_on_all_tests}")
    print(f"  Feedback: {agg_eval_timeout.feedback_text}")
    assert agg_eval_timeout.is_correct_on_all_tests is False
    assert agg_eval_timeout.feedback_structured["all_tests_had_successful_runtime"] is False
    assert agg_eval_timeout.feedback_structured["num_correct_tests"] == 1

    print("\nSelf-tests completed.")
