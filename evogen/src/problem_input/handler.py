import json
import uuid
from typing import Dict, Any
from evogen.src.common.data_structures import ProblemDefinition

def load_problem_definition_from_json(file_path: str) -> ProblemDefinition:
    """
    Loads a ProblemDefinition from a JSON file.

    Args:
        file_path: The path to the JSON file.

    Returns:
        A ProblemDefinition object.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON is malformed or missing required fields.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Problem definition file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {file_path}: {e}")

    # Basic validation (can be expanded)
    required_fields = ["core_task", "input_spec", "output_spec", "initial_test_cases"]
    for field_name in required_fields:
        if field_name not in data:
            raise ValueError(f"Missing required field '{field_name}' in {file_path}")

    # Create ProblemDefinition object, allowing dataclass to handle defaults for optional fields
    try:
        problem_def = ProblemDefinition(
            id=uuid.UUID(data["id"]) if "id" in data else uuid.uuid4(), # Allow providing ID or generate new
            description_raw=data.get("description_raw", ""),
            core_task=data["core_task"],
            input_spec=data["input_spec"],
            output_spec=data["output_spec"],
            target_language=data.get("target_language", "python"), # Default to python
            optimization_objective=data.get("optimization_objective", "minimize_execution_time"),
            evaluation_function_signature=data.get("evaluation_function_signature", "def evaluate(solution_code_str: str, test_inputs: list) -> any:"),
            initial_test_cases=data["initial_test_cases"]
        )
        return problem_def
    except TypeError as e:
        # This might catch issues if data types in JSON don't match dataclass fields
        raise ValueError(f"Error creating ProblemDefinition from data in {file_path}: {e}")
    except Exception as e: # Catch any other unexpected error during instantiation
        raise ValueError(f"An unexpected error occurred while processing {file_path}: {e}")

if __name__ == '__main__':
    # Create a dummy JSON file for testing
    dummy_problem_data = {
        "id": str(uuid.uuid4()),
        "description_raw": "A test problem for adding two numbers.",
        "core_task": "addition",
        "input_spec": {"type": "list", "elements": [{"name": "a", "type": "int"}, {"name": "b", "type": "int"}]},
        "output_spec": {"type": "int"},
        "target_language": "python",
        "optimization_objective": "minimize_execution_time",
        "evaluation_function_signature": "def solve(a: int, b: int) -> int:",
        "initial_test_cases": [
            {"test_case_id": "tc1", "input": [1, 2], "expected_output": 3},
            {"test_case_id": "tc2", "input": [-5, 10], "expected_output": 5}
        ]
    }
    dummy_file_path = "dummy_problem.json"
    with open(dummy_file_path, 'w') as f:
        json.dump(dummy_problem_data, f, indent=4)

    print(f"Attempting to load problem from {dummy_file_path}")
    try:
        problem = load_problem_definition_from_json(dummy_file_path)
        print("Successfully loaded ProblemDefinition:")
        print(f"  ID: {problem.id}")
        print(f"  Core Task: {problem.core_task}")
        print(f"  Test cases: {len(problem.initial_test_cases)}")
        
        # Test with a file that's missing a required field
        invalid_data = dummy_problem_data.copy()
        del invalid_data["core_task"]
        with open("invalid_problem.json", 'w') as f:
            json.dump(invalid_data, f, indent=4)
        print("\nAttempting to load problem from invalid_problem.json (should fail)")
        load_problem_definition_from_json("invalid_problem.json")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
    finally:
        # Clean up dummy files
        import os
        if os.path.exists(dummy_file_path):
            os.remove(dummy_file_path)
        if os.path.exists("invalid_problem.json"):
            os.remove("invalid_problem.json")
