from typing import List, Optional, Tuple
import uuid

from evogen.src.common.data_structures import CandidateSolution, AggregatedEvaluationResult

# For MVP, the "population" might just be the set of solutions evaluated in a single batch.
# The engine's job is to select the "best" from this batch to be a "parent".

def select_best_solution_as_parent(
    evaluated_solutions: List[Tuple[CandidateSolution, AggregatedEvaluationResult]]
) -> Optional[CandidateSolution]:
    """
    Selects the best CandidateSolution from a list of evaluated solutions
    to be the parent for the next generation.
    For MVP, "best" is simply the one with the highest overall_fitness_score.

    Args:
        evaluated_solutions: A list of tuples, each containing a 
                             CandidateSolution and its AggregatedEvaluationResult.

    Returns:
        The CandidateSolution deemed best, or None if the input list is empty.
    """
    if not evaluated_solutions:
        return None

    best_solution: Optional[CandidateSolution] = None
    highest_score = -float('inf') # Initialize with a very low score

    for solution, evaluation_result in evaluated_solutions:
        if evaluation_result.overall_fitness_score > highest_score:
            highest_score = evaluation_result.overall_fitness_score
            best_solution = solution
        elif evaluation_result.overall_fitness_score == highest_score:
            # Tie-breaking rule: e.g., prefer newer generation, or shorter code, or just the first one encountered.
            # For MVP, let's just keep the first one encountered with the highest score.
            pass 

    return best_solution

if __name__ == '__main__':
    print("Testing EvolutionaryEngine (MVP Selector)...")

    # Create dummy data for testing
    problem_id = uuid.uuid4()
    
    sol1_id = uuid.uuid4()
    sol1 = CandidateSolution(id=sol1_id, problem_id=problem_id, code="sol1 code", generation=1)
    eval1 = AggregatedEvaluationResult(solution_id=sol1_id, overall_fitness_score=0.75)

    sol2_id = uuid.uuid4()
    sol2 = CandidateSolution(id=sol2_id, problem_id=problem_id, code="sol2 code", generation=1)
    eval2 = AggregatedEvaluationResult(solution_id=sol2_id, overall_fitness_score=0.90)

    sol3_id = uuid.uuid4()
    sol3 = CandidateSolution(id=sol3_id, problem_id=problem_id, code="sol3 code", generation=1)
    eval3 = AggregatedEvaluationResult(solution_id=sol3_id, overall_fitness_score=0.85)
    
    sol4_id = uuid.uuid4() # Another solution with the same highest score
    sol4 = CandidateSolution(id=sol4_id, problem_id=problem_id, code="sol4 code", generation=1)
    eval4 = AggregatedEvaluationResult(solution_id=sol4_id, overall_fitness_score=0.90)


    current_batch_evaluated = [
        (sol1, eval1),
        (sol2, eval2), # Highest score
        (sol3, eval3),
        (sol4, eval4)  # Same highest score as sol2
    ]

    # Test with a populated list
    selected_parent = select_best_solution_as_parent(current_batch_evaluated)
    print(f"Selected parent from batch: {selected_parent.id if selected_parent else 'None'}")
    assert selected_parent is not None
    assert selected_parent.id == sol2.id # Based on current tie-breaking (first one with max score)

    # Test with an empty list
    selected_parent_empty = select_best_solution_as_parent([])
    print(f"Selected parent from empty batch: {'None' if not selected_parent_empty else selected_parent_empty.id}")
    assert selected_parent_empty is None
    
    # Test with one solution
    selected_parent_single = select_best_solution_as_parent([(sol1,eval1)])
    print(f"Selected parent from single solution batch: {selected_parent_single.id if selected_parent_single else 'None'}")
    assert selected_parent_single is not None
    assert selected_parent_single.id == sol1.id


    print("EvolutionaryEngine (MVP Selector) self-tests PASSED.")
