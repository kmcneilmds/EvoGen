import sqlite3
import json
import uuid
from typing import List, Optional, Any

from evogen.src.common.data_structures import (
    ProblemDefinition, 
    CandidateSolution, 
    AggregatedEvaluationResult,
    TargetLanguage # For default values if needed
)

DB_FILE = "evogen_program_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Problems Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Problems (
        id TEXT PRIMARY KEY,
        description_raw TEXT,
        core_task TEXT,
        input_spec TEXT,      -- JSON string
        output_spec TEXT,     -- JSON string
        target_language TEXT,
        optimization_objective TEXT,
        evaluation_function_signature TEXT,
        initial_test_cases TEXT -- JSON string
    )''')

    # Solutions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Solutions (
        id TEXT PRIMARY KEY,
        problem_id TEXT,
        generation INTEGER,
        parent_id TEXT,
        code TEXT,
        generation_prompt TEXT,
        llm_model_used TEXT,
        FOREIGN KEY (problem_id) REFERENCES Problems (id)
    )''')

    # Evaluations Table
    # Storing AggregatedEvaluationResult
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Evaluations (
        id TEXT PRIMARY KEY, -- Could be solution_id if one eval per solution, or own UUID
        solution_id TEXT UNIQUE, -- Assuming one aggregated evaluation per solution for MVP
        overall_fitness_score REAL,
        is_correct_on_all_tests INTEGER, -- Boolean: 0 or 1
        avg_execution_time_ms REAL,
        feedback_text TEXT,
        feedback_structured TEXT, -- JSON string
        FOREIGN KEY (solution_id) REFERENCES Solutions (id)
    )''')
    # Note: RawTestResult objects are not stored individually in DB for MVP,
    # they are processed into AggregatedEvaluationResult.

    conn.commit()
    conn.close()

def save_problem_definition(problem_def: ProblemDefinition):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Problems (id, description_raw, core_task, input_spec, output_spec, 
                              target_language, optimization_objective, 
                              evaluation_function_signature, initial_test_cases)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(problem_def.id), problem_def.description_raw, problem_def.core_task,
            json.dumps(problem_def.input_spec), json.dumps(problem_def.output_spec),
            problem_def.target_language, problem_def.optimization_objective,
            problem_def.evaluation_function_signature, json.dumps(problem_def.initial_test_cases)
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error saving ProblemDefinition (ID: {problem_def.id}): {e}. It might already exist.")
    finally:
        conn.close()

def get_problem_definition(problem_id: uuid.UUID) -> Optional[ProblemDefinition]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Problems WHERE id = ?", (str(problem_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return ProblemDefinition(
            id=uuid.UUID(row["id"]),
            description_raw=row["description_raw"],
            core_task=row["core_task"],
            input_spec=json.loads(row["input_spec"]),
            output_spec=json.loads(row["output_spec"]),
            target_language=row["target_language"],
            optimization_objective=row["optimization_objective"],
            evaluation_function_signature=row["evaluation_function_signature"],
            initial_test_cases=json.loads(row["initial_test_cases"])
        )
    return None

def save_candidate_solution(solution: CandidateSolution):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Solutions (id, problem_id, generation, parent_id, code, 
                               generation_prompt, llm_model_used)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(solution.id), str(solution.problem_id), solution.generation,
            str(solution.parent_id) if solution.parent_id else None,
            solution.code, solution.generation_prompt, solution.llm_model_used
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error saving CandidateSolution (ID: {solution.id}): {e}. Problem ID might not exist or ID collision.")
    finally:
        conn.close()

def get_candidate_solution(solution_id: uuid.UUID) -> Optional[CandidateSolution]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Solutions WHERE id = ?", (str(solution_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return CandidateSolution(
            id=uuid.UUID(row["id"]),
            problem_id=uuid.UUID(row["problem_id"]),
            generation=row["generation"],
            parent_id=uuid.UUID(row["parent_id"]) if row["parent_id"] else None,
            code=row["code"],
            generation_prompt=row["generation_prompt"],
            llm_model_used=row["llm_model_used"]
        )
    return None

def save_aggregated_evaluation(agg_eval: AggregatedEvaluationResult):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO Evaluations (id, solution_id, overall_fitness_score, is_correct_on_all_tests,
                                 avg_execution_time_ms, feedback_text, feedback_structured)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(uuid.uuid4()), # Assign a new UUID for the evaluation entry itself
            str(agg_eval.solution_id),
            agg_eval.overall_fitness_score,
            1 if agg_eval.is_correct_on_all_tests else 0,
            agg_eval.avg_execution_time_ms,
            agg_eval.feedback_text,
            json.dumps(agg_eval.feedback_structured)
        ))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"Error saving AggregatedEvaluationResult (Solution ID: {agg_eval.solution_id}): {e}. Solution ID might not exist or evaluation already exists.")
    finally:
        conn.close()

def get_aggregated_evaluation(solution_id: uuid.UUID) -> Optional[AggregatedEvaluationResult]:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Assuming 'solution_id' is unique in Evaluations table for MVP
    cursor.execute("SELECT * FROM Evaluations WHERE solution_id = ?", (str(solution_id),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return AggregatedEvaluationResult(
            # id=uuid.UUID(row["id"]), # This is the eval's own ID, not what we usually carry around
            solution_id=uuid.UUID(row["solution_id"]),
            overall_fitness_score=row["overall_fitness_score"],
            is_correct_on_all_tests=bool(row["is_correct_on_all_tests"]),
            avg_execution_time_ms=row["avg_execution_time_ms"],
            feedback_text=row["feedback_text"],
            feedback_structured=json.loads(row["feedback_structured"])
        )
    return None

if __name__ == '__main__':
    # Basic test of database operations
    print("Initializing database...")
    initialize_db() # Ensures tables are created

    # Test ProblemDefinition
    test_problem_id = uuid.uuid4()
    problem = ProblemDefinition(
        id=test_problem_id,
        description_raw="Test problem for DB.",
        core_task="db_test",
        input_spec={"type": "int"},
        output_spec={"type": "int"},
        initial_test_cases=[{"input": 1, "expected_output": 1}]
    )
    print(f"Saving problem: {test_problem_id}")
    save_problem_definition(problem)
    retrieved_problem = get_problem_definition(test_problem_id)
    assert retrieved_problem is not None
    assert retrieved_problem.id == test_problem_id
    assert retrieved_problem.core_task == "db_test"
    assert len(retrieved_problem.initial_test_cases) == 1
    print("ProblemDefinition save/retrieve test PASSED.")

    # Test CandidateSolution
    test_solution_id = uuid.uuid4()
    solution = CandidateSolution(
        id=test_solution_id,
        problem_id=test_problem_id,
        code="pass",
        generation=0
    )
    print(f"Saving solution: {test_solution_id}")
    save_candidate_solution(solution)
    retrieved_solution = get_candidate_solution(test_solution_id)
    assert retrieved_solution is not None
    assert retrieved_solution.id == test_solution_id
    assert retrieved_solution.problem_id == test_problem_id
    print("CandidateSolution save/retrieve test PASSED.")

    # Test AggregatedEvaluationResult
    agg_eval = AggregatedEvaluationResult(
        solution_id=test_solution_id,
        overall_fitness_score=0.95,
        is_correct_on_all_tests=True,
        feedback_text="Looks good!"
    )
    print(f"Saving evaluation for solution: {test_solution_id}")
    save_aggregated_evaluation(agg_eval)
    retrieved_eval = get_aggregated_evaluation(test_solution_id)
    assert retrieved_eval is not None
    assert retrieved_eval.solution_id == test_solution_id
    assert retrieved_eval.overall_fitness_score == 0.95
    print("AggregatedEvaluationResult save/retrieve test PASSED.")

    # Test saving another problem to ensure no conflicts with existing DB file
    another_problem_id = uuid.uuid4()
    another_problem = ProblemDefinition(id=another_problem_id, core_task="another_db_test")
    save_problem_definition(another_problem)
    assert get_problem_definition(another_problem_id) is not None
    print("Saving another problem PASSED.")

    print("\nAll DB self-tests completed. Check for 'evogen_program_database.db' file.")
    # Consider removing the DB_FILE after tests for cleanliness in some contexts,
    # but for MVP, keeping it to inspect is fine.
    # import os
    # if os.path.exists(DB_FILE):
    #     os.remove(DB_FILE)
