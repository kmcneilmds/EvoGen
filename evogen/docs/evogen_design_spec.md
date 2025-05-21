Project "EvoGen": Algorithmic Evolution Agent - Design & Implementation Specification
Version: 1.0
Date: October 26, 2023
Author: AI Language Model (acting as Lead Architect)
1. Introduction & Vision
1.1. Goal: To create an autonomous software agent, "EvoGen," capable of understanding complex computational problems described in natural language, generating initial algorithmic solutions, rigorously testing these solutions, learning from successes and failures, and iteratively evolving increasingly sophisticated and efficient algorithms.
1.2. Inspiration: This project draws inspiration from systems like Google DeepMind's AlphaEvolve, aiming to leverage Large Language Models (LLMs) within an evolutionary computation framework.
1.3. Target Hardware: Optimized for a user system with a Ryzen 9 5950X CPU and an NVIDIA GeForce RTX 4090 GPU.
1.4. Core Principle: LLM-guided evolutionary search, grounded by automated code execution and rigorous evaluation, to drive algorithmic discovery and optimization.
1.5. Desired Outcome: A functional system with a user interface (UI) that allows users to define problems, observe the evolutionary process, and retrieve optimized algorithmic solutions.
2. System Architecture Overview
EvoGen will be a modular system. The primary modules are:
OrchestratorCore: The central nervous system, managing workflow and inter-module communication.
ProblemInputModule: Handles ingestion and LLM-based parsing of user problem descriptions.
SolutionGenerationModule: Interfaces with LLMs to generate and modify code.
EvaluationSandbox: Securely executes candidate solutions on CPU/GPU, manages test cases, and gathers raw performance data.
MetricsAndFeedbackModule: Calculates evaluation scores and generates structured feedback for the evolutionary process.
EvolutionaryEngine: Manages the population of candidate solutions and implements selection strategies.
ProgramDatabase: Persistently stores all programs, prompts, evaluation results, and their lineage.
UserInterfaceModule: Provides a visual interface for user interaction and process monitoring.
(High-level architecture diagram would be inserted here, showing modules and primary data flows)
3. Module-Specific Design Specifications
3.1. OrchestratorCore
Responsibilities:
Initialize and manage the main evolutionary loop.
Coordinate tasks between all other modules (e.g., request solution generation, trigger evaluation, store results).
Manage state (current generation, population, best solution found).
Handle task queuing and asynchronous operations.
Error handling and logging for the entire system.
Technologies: Python 3.9+ (utilizing asyncio for concurrent task management).
Core Logic:
Finite state machine to manage stages of the evolutionary cycle.
Dispatch tasks to appropriate modules based on current state.
Aggregate results and decide next steps in the evolution.
Interfaces:
Calls methods on all other modules (e.g., ProblemInputModule.parse_problem(), SolutionGenerationModule.generate_initial_solution(), EvaluationSandbox.execute_solution()).
Receives callbacks or awaited results from other modules.
3.2. ProblemInputModule
Responsibilities:
Receive natural language problem description from the UI.
Utilize an LLM (e.g., Gemini API) to parse the description into a structured ProblemDefinition.
Identify: core task, input/output types, target programming language (Python for CPU, C++/CUDA for GPU), explicit/implicit constraints, and primary optimization objectives (e.g., minimize time, maximize accuracy).
Define or infer evaluation function signature(s).
Technologies: Python, LLM API client library (e.g., google-generativeai).
Core Logic:
Prompt Engineering: Develop robust prompts for the LLM to extract structured information. Example:
You are an AI assistant tasked with parsing a problem description for an algorithmic discovery system. Extract the following:
1. Core Task: (e.g., sorting, matrix multiplication, pathfinding)
2. Input Data Description: (e.g., list of integers, N x M matrix of floats)
3. Output Data Description: (e.g., sorted list, resulting matrix)
4. Target Language: (Infer Python or CUDA C++ based on problem type or keywords, default to Python)
5. Primary Optimization Objective: (e.g., minimize execution time, maximize score on a benchmark)
6. Key Constraints: (e.g., memory limits, correctness criteria)
7. Potential Evaluation Function Name: (Suggest a Python function name like 'evaluate_solution')
Problem Description: "{user_problem_description}"
Output in JSON format.
Use code with caution.
Validation of parsed output.
Data Structures:
ProblemDefinition (dataclass or Pydantic model):
id: UUID
description_raw: str
core_task: str
input_spec: dict (e.g., {"type": "list", "element_type": "float"})
output_spec: dict
target_language: enum (PYTHON, CUDA_CPP)
optimization_objective: str (e.g., "minimize_avg_execution_time")
constraints: list[str]
evaluation_function_signature: str (e.g., def evaluate(solution_code, test_inputs) -> float:)
initial_test_cases: list[dict] (optional, user can provide, or LLM can be asked to generate simple ones)
Interfaces:
Input: User text from UserInterfaceModule.
Output: ProblemDefinition object to OrchestratorCore.
3.3. SolutionGenerationModule
Responsibilities:
Generate initial candidate solutions based on ProblemDefinition using an LLM.
Evolve existing solutions by applying LLM-guided modifications (mutations, refactoring, new approaches).
Parse LLM outputs (code, diffs) into usable CandidateSolution objects.
Technologies: Python, LLM API client(s) (Primary: Gemini Pro/Advanced; Secondary: potentially a faster/cheaper model for simpler mutations if available locally and performant enough).
Core Logic:
Initial Generation Prompt: "Given Problem: {ProblemDefinition.core_task} with inputs {ProblemDefinition.input_spec} and outputs {ProblemDefinition.output_spec}. Write an initial solution in {ProblemDefinition.target_language}. Prioritize correctness. The main evaluation function will be {ProblemDefinition.evaluation_function_signature}."
Evolution Prompt (inspired by AlphaEvolve):
You are an expert {ProblemDefinition.target_language} programmer and algorithmic designer.
Current Problem: {ProblemDefinition.core_task}.
Parent Code (Generation {parent.generation}, Score: {parent.score}):
Use code with caution.
{parent.code}
Feedback & Evaluation Summary: {feedback_text_from_MetricsAndFeedbackModule}
Goal: Improve the solution to {ProblemDefinition.optimization_objective}. You can:
1. Refactor the existing code for clarity or efficiency.
2. Optimize specific bottlenecks.
3. Try a completely different algorithmic approach.
4. Introduce or modify data structures.
Propose changes. If modifying, use SEARCH/REPLACE blocks:
<<<<<<< SEARCH
# Original code block
========
# New code block
>>>>>>> REPLACE
Or provide the complete new function if it's a major rewrite.
Use code with caution.
Parsing of LLM output (handle full code, diff application).
Applying diffs to parent code to create child code.
Data Structures:
CandidateSolution:
id: UUID
problem_id: UUID
generation: int
parent_id: UUID (optional)
code: str
generation_prompt: str (prompt used to create this)
llm_model_used: str
Interfaces:
Input: ProblemDefinition, parent CandidateSolution (optional), FeedbackText from OrchestratorCore.
Output: New CandidateSolution object(s) to OrchestratorCore.
3.4. EvaluationSandbox
Responsibilities:
Receive CandidateSolution code and ProblemDefinition (for test cases and evaluation context).
Set up a secure execution environment (sandboxed).
Compile code if necessary (for C++/CUDA).
Execute the solution against provided or generated test cases.
Monitor resource usage (CPU time, GPU time via nvidia-smi or CUDA events, memory).
Capture standard output, standard error, and return values.
Implement timeout mechanisms to prevent runaway processes.
Technologies:
Python (subprocess for external processes, multiprocessing for parallel Python evaluations).
Docker (optional, for stronger isolation, especially if solutions can install packages).
For C++/CUDA: nvcc (compiler), Python wrappers to launch compiled executables.
Test case generation: can use an LLM initially or rely on user-provided tests from ProblemDefinition.
Core Logic:
Environment Setup: Create temporary directories, write solution code to file.
Compilation (for C++/CUDA):
Construct nvcc command (e.g., nvcc solution.cu -o solution_exec -arch=sm_89 for RTX 4090).
Capture compilation output/errors.
Execution:
CPU (Python): python solution.py <test_input_file> > output.txt 2> error.txt
GPU (C++/CUDA): ./solution_exec <test_input_file> > output.txt 2> error.txt
Wrap execution with timeout logic.
Measure wall-clock time, CPU time. For GPU, use CUDA events for kernel timing or nvidia-smi for overall GPU utilization and time if simpler.
Output Parsing: Read output.txt, error.txt.
Data Structures:
RawTestResult:
solution_id: UUID
test_case_id: str
status: enum (SUCCESS, FAILURE_COMPILATION, FAILURE_RUNTIME_ERROR, FAILURE_TIMEOUT, FAILURE_WRONG_OUTPUT)
stdout: str
stderr: str
execution_time_ms: float
cpu_time_ms: float (if measurable)
gpu_time_ms: float (if applicable)
memory_usage_mb: float
actual_output: any (parsed from stdout)
Interfaces:
Input: CandidateSolution, ProblemDefinition (for test cases) from OrchestratorCore.
Output: List of RawTestResult objects (one per test case) to OrchestratorCore.
3.5. MetricsAndFeedbackModule
Responsibilities:
Receive RawTestResults from the EvaluationSandbox.
Compare actual_output with expected_output from test cases to determine correctness.
Calculate a fitness score based on ProblemDefinition.optimization_objective (e.g., average execution time, accuracy). This is the h function from AlphaEvolve.
Generate structured and natural language feedback for the SolutionGenerationModule.
Technologies: Python.
Core Logic:
Correctness Check: Deep comparison of actual vs. expected outputs.
Scoring Function:
If "minimize_time": score could be 1 / (avg_execution_time + epsilon) or a normalized value.
If "maximize_accuracy": score is accuracy.
Penalize incorrect or failing solutions heavily (e.g., score = 0 or very low).
Feedback Generation:
Structured: {"correct": true/false, "avg_time": X, "errors": ["..."]}
Natural Language: "Solution was correct. Average execution time: X ms. No errors. Suggest focusing on reducing loop complexity." OR "Solution failed 3/10 test cases due to incorrect output. Runtime error on test case Y: [error message]. Execution time was Z ms on successful cases."
Data Structures:
AggregatedEvaluationResult:
solution_id: UUID
overall_fitness_score: float
is_correct_on_all_tests: bool
avg_execution_time_ms: float (if applicable)
detailed_metrics: dict (e.g., accuracy, specific sub-scores)
feedback_text: str (for LLM)
feedback_structured: dict
Interfaces:
Input: List of RawTestResult objects from OrchestratorCore.
Output: AggregatedEvaluationResult to OrchestratorCore.
3.6. EvolutionaryEngine
Responsibilities:
Maintain the current population of CandidateSolutions with their AggregatedEvaluationResult.
Implement selection strategies to choose parents for the next generation (e.g., tournament selection, fitness-proportional, MAP-Elites to maintain diversity across multiple objectives/behaviors).
Manage population size (e.g., elitism, culling).
Technologies: Python.
Core Logic:
Store population in memory or query ProgramDatabase.
Selection Algorithms:
Elitism: Always carry over the top N best solutions.
Tournament Selection: Randomly pick K individuals, the best among them becomes a parent.
MAP-Elites (Advanced): If multiple objectives or behavioral descriptors are defined, maintain a grid of elites, each cell representing a niche.
Provide a list of selected parent CandidateSolution IDs to the OrchestratorCore.
Data Structures:
Internal representation of the population (list of (CandidateSolution, AggregatedEvaluationResult) tuples).
Interfaces:
Input: Receives notifications of new evaluated solutions from OrchestratorCore (indirectly, via ProgramDatabase updates).
Output: List of parent CandidateSolution IDs (or full objects) to OrchestratorCore.
3.7. ProgramDatabase
Responsibilities:
Persistently store all generated CandidateSolutions, their generation prompts, RawTestResults, AggregatedEvaluationResults, and lineage (parent-child relationships).
Provide efficient querying capabilities.
Technologies: Python, SQLite (for initial simplicity and local deployment) or PostgreSQL (for more robustness and scalability). SQLAlchemy as ORM.
Data Schema (Illustrative for SQLite):
Problems (problem_id PK, description_raw, problem_definition_json)
Solutions (solution_id PK, problem_id FK, generation, parent_solution_id FK, code_text, generation_prompt_text, llm_model_used, timestamp)
Evaluations (evaluation_id PK, solution_id FK, fitness_score, is_correct, avg_exec_time, feedback_text, feedback_structured_json, timestamp)
TestRuns (test_run_id PK, solution_id FK, test_case_name, status, stdout, stderr, exec_time, memory_usage, actual_output_json, timestamp)
Interfaces:
Provides CRUD (Create, Read, Update, Delete) methods for all data entities, callable by OrchestratorCore and EvolutionaryEngine.
3.8. UserInterfaceModule (Detailed in Section 5)
4. Core Evolutionary Loop & Data Flow
START: User submits problem via UserInterfaceModule -> ProblemInputModule.
ProblemInputModule -> LLM -> ProblemDefinition -> OrchestratorCore.
OrchestratorCore -> SolutionGenerationModule (with ProblemDefinition) -> Initial CandidateSolution(s).
For each CandidateSolution:
a. OrchestratorCore -> EvaluationSandbox (with CandidateSolution, ProblemDefinition.test_cases).
b. EvaluationSandbox executes -> RawTestResult(s).
c. OrchestratorCore -> MetricsAndFeedbackModule (with RawTestResult(s)).
d. MetricsAndFeedbackModule -> AggregatedEvaluationResult.
e. OrchestratorCore -> ProgramDatabase (store CandidateSolution, AggregatedEvaluationResult, RawTestResult(s)).
OrchestratorCore signals EvolutionaryEngine (or EvolutionaryEngine polls ProgramDatabase).
EvolutionaryEngine selects parent CandidateSolution(s) from ProgramDatabase.
OrchestratorCore -> SolutionGenerationModule (with parent(s), their AggregatedEvaluationResult.feedback_text, ProblemDefinition) -> New CandidateSolution(s).
GOTO Step 4 with new CandidateSolution(s).
UserInterfaceModule continuously polls OrchestratorCore or ProgramDatabase for updates to display.
(Detailed data flow diagram would be inserted here)
5. User Interface (UI) / Visualization Design
Purpose: Enable problem submission, monitor the evolutionary process, inspect solutions and their performance, and retrieve final results.
Technology Choice: Web-based application.
Backend: Python (Flask or FastAPI) serving as an API layer for the OrchestratorCore and ProgramDatabase.
Frontend: React, Vue.js, or Svelte for a dynamic and responsive UI. Visualization libraries like D3.js, Chart.js.
Key UI Panes/Views:
1. Dashboard / Project Selection:
List existing evolution projects (problems).
"Create New Project" button.
2. Project View (Main View for an active evolution):
2.1. Problem Definition Pane:
Displays the ProblemDefinition (raw input, parsed structure).
Large text area for new problem input or editing existing.
Controls: "Start/Resume Evolution," "Pause Evolution," "Stop Evolution."
2.2. Live Metrics Pane:
Line charts: Best Fitness vs. Generation, Average Fitness vs. Generation.
Bar chart: Population size, number of successful/failed evaluations per generation.
Gauge: Evaluations per minute.
2.3. Population Explorer Pane:
Table view of current generation's solutions: ID, Generation, Parent ID, Fitness Score(s), Key Perf. Metric (e.g., Time), Status (Best, Active, Failed).
Sortable, filterable. Clicking a solution opens the Solution Inspector.
Visual cues (color coding) for solution quality/status.
2.4. Solution Inspector Pane (Modal or dedicated section):
Selected CandidateSolution's ID, Generation, Parent.
Code View: Syntax-highlighted code. Option to see diff from parent.
Prompt View: The exact prompt fed to the LLM to generate/modify this solution.
Evaluation Details View:
Overall Fitness Score.
AggregatedEvaluationResult.feedback_text and structured feedback.
Table of RawTestResults for each test case: status, time, memory, actual vs. expected output (if simple enough to display).
Lineage View (Optional, advanced): Small graph showing its ancestors and direct children.
2.5. System Log Pane:
Real-time stream of important log messages from OrchestratorCore.
2.6. Best Solution Pane:
Displays the code of the current best-performing solution found so far.
"Export Code" button.
3. Configuration Pane:
LLM API Keys.
Population size, selection parameters (e.g., tournament size).
Default target language.
Sandbox settings (e.g., timeouts).
6. Development Roadmap (Phased Approach)
Phase 0: Setup & Foundational Libraries
Project structure, version control (Git), dependency management (Poetry/Conda).
Basic LLM API interaction wrapper.
Phase 1: Core CLI Engine (MVP)
OrchestratorCore (basic synchronous loop).
ProblemInputModule (manual JSON ProblemDefinition input, no LLM parsing yet).
SolutionGenerationModule (single LLM, initial generation only).
EvaluationSandbox (Python CPU execution only, simple test cases).
MetricsAndFeedbackModule (basic scoring, text feedback).
ProgramDatabase (SQLite, basic schema).
EvolutionaryEngine (select best N as parents).
Goal: End-to-end evolution for a trivial Python problem via CLI.
Phase 2: LLM Integration & Enhanced Core
Integrate LLM parsing in ProblemInputModule.
Implement LLM-based evolution (mutations) in SolutionGenerationModule.
Refine MetricsAndFeedbackModule for better LLM feedback.
Implement asyncio in OrchestratorCore for parallelism.
Phase 3: GPU Support & Advanced Evaluation
Extend EvaluationSandbox for C++/CUDA compilation and execution on RTX 4090.
Implement robust resource monitoring for GPU.
Develop evaluation cascades (multi-stage testing).
Phase 4: UI Development (Backend First)
Develop FastAPI/Flask backend to expose OrchestratorCore and ProgramDatabase functionality.
Implement basic frontend views for project creation and monitoring (data tables, simple charts).
Phase 5: UI Polish & Advanced Evolutionary Strategies
Enhance frontend UI with richer visualizations, solution inspection.
Implement advanced selection in EvolutionaryEngine (e.g., MAP-Elites if multi-objective problems are tackled).
Integrate LLM ensemble (e.g., different models for different tasks).
Phase 6: Optimization, Robustness, and Documentation
Performance tuning, error handling, scalability testing.
User and developer documentation.
7. LLM Interaction Strategy
Primary LLM: A highly capable, instruction-following model with strong coding and reasoning abilities (e.g., latest Gemini model).
Prompting:
Use clear, structured prompts with examples where appropriate (few-shot).
Provide sufficient context (problem definition, parent code, specific feedback).
Iteratively refine prompts based on LLM output quality.
Chain-of-Thought/Self-Critique (Advanced): For complex refactoring, ask the LLM to first outline its plan, then generate code, then critique its own code against the objectives.
Output Parsing: Expect variability; implement robust parsers for code blocks and diffs.
API Key Management: Securely store and manage API keys (e.g., via environment variables, .env file, or a secrets manager for more complex deployments).
8. Target Hardware Utilization (5950X CPU, RTX 4090 GPU)
Ryzen 9 5950X (CPU):
Primary host for Python-based modules (OrchestratorCore, UI backend, EvolutionaryEngine, etc.).
EvaluationSandbox for Python solutions (can leverage multiple cores via multiprocessing).
Compilation of C++/CUDA code via nvcc.
Running smaller, local LLMs for auxiliary tasks (e.g., code formatting, simple prompt generation) if feasible and VRAM allows without impacting primary GPU tasks.
RTX 4090 (GPU):
Dedicated to the EvaluationSandbox for executing C++/CUDA candidate solutions. Ensure exclusive access during evaluation to get accurate performance metrics.
If running powerful local LLMs for generation/evolution, the 4090 would be the primary inference hardware. This would require careful VRAM management and potentially scheduling LLM tasks and GPU code evaluations to avoid contention. (Cloud LLMs are simpler to start).
Memory (System RAM & GPU VRAM):
Sufficient system RAM is needed for the Python processes, database, and potentially local CPU-based LLMs.
The 24GB VRAM on the RTX 4090 is substantial and can handle large models/kernels, but still needs monitoring if running both complex GPU solutions and local LLMs.
9. Future Considerations (Post-MVP)
Distributed evaluation workers.
Support for more programming languages.
Automated test case generation using LLMs.
Self-adaptation of evolutionary parameters.
Integration with formal verification tools.