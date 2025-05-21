import uuid
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional, Union

# Enum for target language (simplified for MVP)
class TargetLanguage:
    PYTHON = "python"
    # CUDA_CPP = "cuda_cpp" # For future phases

# Enum for test result status
class TestStatus:
    SUCCESS = "SUCCESS"
    FAILURE_COMPILATION = "FAILURE_COMPILATION" # More relevant for C++/CUDA
    FAILURE_RUNTIME_ERROR = "FAILURE_RUNTIME_ERROR"
    FAILURE_TIMEOUT = "FAILURE_TIMEOUT"
    FAILURE_WRONG_OUTPUT = "FAILURE_WRONG_OUTPUT"

@dataclass
class ProblemDefinition:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description_raw: str = ""
    core_task: str = "" # e.g., "sort a list of integers"
    input_spec: Dict[str, Any] = field(default_factory=dict) # e.g., {"type": "list", "element_type": "int"}
    output_spec: Dict[str, Any] = field(default_factory=dict) # e.g., {"type": "list", "element_type": "int"}
    target_language: str = TargetLanguage.PYTHON # Default to Python for MVP
    optimization_objective: str = "minimize_execution_time" # e.g., "minimize_execution_time", "maximize_accuracy"
    evaluation_function_signature: str = "def evaluate(solution_code_str: str, test_inputs: List[Any]) -> Any:" # Example
    initial_test_cases: List[Dict[str, Any]] = field(default_factory=list) # e.g., [{"input": [1,2], "expected_output": 3}]

@dataclass
class CandidateSolution:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    problem_id: uuid.UUID = field(default_factory=uuid.uuid4) # Foreign key to ProblemDefinition
    generation: int = 0
    parent_id: Optional[uuid.UUID] = None # Self-referential for lineage
    code: str = "" # The actual source code
    # For MVP, generation_prompt and llm_model_used can be simple placeholders
    # if not directly using LLM for initial generation yet.
    generation_prompt: str = "Initial generation for MVP" 
    llm_model_used: str = "N/A for MVP initial solution"

@dataclass
class RawTestResult:
    solution_id: uuid.UUID
    test_case_id: Union[str, int] # Identifier for the test case used
    status: str # From TestStatus enum
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    actual_output: Any = None # Parsed output from stdout or return value

@dataclass
class AggregatedEvaluationResult:
    solution_id: uuid.UUID
    overall_fitness_score: float = 0.0
    is_correct_on_all_tests: bool = False
    avg_execution_time_ms: Optional[float] = None # Calculated if relevant
    # Feedback text for LLM (even in MVP, good to have the field)
    feedback_text: str = "Evaluation complete." 
    # Optional structured feedback for internal use or more detailed reporting
    feedback_structured: Dict[str, Any] = field(default_factory=dict) 

# Example usage (optional, can be removed or kept for testing)
if __name__ == '__main__':
    problem = ProblemDefinition(
        description_raw="Add two numbers.",
        core_task="addition",
        input_spec={"type": "list", "elements": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}]},
        output_spec={"type": "int"},
        initial_test_cases=[
            {"test_case_id": 1, "input": [1, 2], "expected_output": 3},
            {"test_case_id": 2, "input": [5, 5], "expected_output": 10}
        ]
    )
    print(problem)

    solution = CandidateSolution(
        problem_id=problem.id,
        code="def add(a, b): return a + b"
    )
    print(solution)

    result1 = RawTestResult(
        solution_id=solution.id,
        test_case_id=1,
        status=TestStatus.SUCCESS,
        execution_time_ms=10.5,
        actual_output=3
    )
    print(result1)

    aggregated_eval = AggregatedEvaluationResult(
        solution_id=solution.id,
        overall_fitness_score=1.0,
        is_correct_on_all_tests=True,
        avg_execution_time_ms=10.5,
        feedback_text="Solution is correct and fast enough for MVP."
    )
    print(aggregated_eval)
