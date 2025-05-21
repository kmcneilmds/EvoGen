import uuid
from evogen.src.common.data_structures import ProblemDefinition, CandidateSolution

def generate_initial_solution(problem_def: ProblemDefinition) -> CandidateSolution:
    """
    Generates a very basic initial CandidateSolution for a given ProblemDefinition.
    For MVP, this returns a hardcoded Python "hello world" or simple function.
    It does not use LLMs in this phase.

    Args:
        problem_def: The ProblemDefinition for which to generate a solution.

    Returns:
        A CandidateSolution object.
    """

    # For MVP, we'll create a very simple, generic Python function.
    # This code doesn't necessarily solve the problem_def, 
    # it's just a placeholder for the evolutionary process to start with.
    placeholder_code = (
        "def solve(*args, **kwargs):\n"
        "    # This is a placeholder solution for EvoGen MVP\n"
        "    print(\"Hello from EvoGen MVP solution!\")\n"
        "    # Try to return a simple value that might match some test cases by chance\n"
        "    if 'input' in kwargs and isinstance(kwargs['input'], list) and len(kwargs['input']) > 0:\n"
        "        return kwargs['input'][0] # Example: return the first input element\n"
        "    return None"
    )

    solution = CandidateSolution(
        problem_id=problem_def.id,
        generation=0, # Initial generation
        parent_id=None, # No parent for initial solution
        code=placeholder_code,
        generation_prompt="Initial MVP placeholder solution",
        llm_model_used="N/A - Hardcoded for MVP"
    )
    return solution

if __name__ == '__main__':
    # Create a dummy ProblemDefinition for testing
    dummy_problem_id = uuid.uuid4()
    problem = ProblemDefinition(
        id=dummy_problem_id,
        core_task="Test Task",
        description_raw="A task to test initial solution generation."
        # Other fields can be default for this test
    )

    print(f"Generating initial solution for problem ID: {problem.id}")
    initial_solution = generate_initial_solution(problem)

    print("Generated CandidateSolution:")
    print(f"  ID: {initial_solution.id}")
    print(f"  Problem ID: {initial_solution.problem_id}")
    print(f"  Generation: {initial_solution.generation}")
    print(f"  Code:\n{initial_solution.code}")
    print(f"  LLM Model: {initial_solution.llm_model_used}")

    assert initial_solution.problem_id == dummy_problem_id
    assert initial_solution.generation == 0
    assert "placeholder solution" in initial_solution.code
    print("\nSelf-tests passed.")
