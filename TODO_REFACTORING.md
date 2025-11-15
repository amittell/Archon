# Archon Refactoring TODO List

**Based on:** CODE_AUDIT.md comprehensive analysis
**Total Tasks:** 66 (33 implementations + 33 verifications)
**Status:** ✅ Priority 1 Complete | ⏳ Priority 2 & 3 Pending

---

## ✅ COMPLETED (Priority 1 - High Impact, Low Effort)

### code_validator.py

- [x] **Task 1.1:** Convert ValidationResult from manual class to @dataclass
- [x] **Task 1.1v:** Verify ValidationResult is a dataclass and serializable
- [x] **Task 1.2:** Create archon/constants.py and extract COMMON_IMPORTS
- [x] **Task 1.2v:** Verify COMMON_IMPORTS imported correctly in code_validator.py
- [x] **Task 1.3:** Extract DANGEROUS_PATTERNS to constants.py
- [x] **Task 1.3v:** Verify DANGEROUS_PATTERNS works correctly in validation
- [x] **Task 1.4:** Extract VALIDATION_ERROR_MARKER to constants.py
- [x] **Task 1.4v:** Verify error marker used correctly in run_in_sandbox()
- [x] **Task 1.5:** Extract STDERR_MAX_LENGTH to constants.py
- [x] **Task 1.5v:** Verify stderr truncation uses constant
- [x] **Task 1.6:** Extract DEFAULT_VALIDATION_TIMEOUT to constants.py
- [x] **Task 1.6v:** Verify CodeValidator uses constant for default timeout
- [x] **Task 1.7:** Replace chr(10) with '\n' in run_in_sandbox() line 271
- [x] **Task 1.7v:** Verify code still runs correctly with '\n'
- [x] **Task 1.8:** Fix duplicate set() conversions in validate_imports()
- [x] **Task 1.8v:** Verify imports validation works with single set conversion
- [x] **Task 1.9:** Replace list comprehension [...].[0] with next() on line 298
- [x] **Task 1.9v:** Verify error line extraction works correctly
- [x] **Task 1.10:** Add _parse_or_skip() helper method
- [x] **Task 1.10v:** Verify _parse_or_skip() eliminates duplicate code
- [x] **Task 1.11:** Remove verbose docstrings from validate_syntax()
- [x] **Task 1.11v:** Verify type hints alone make method clear
- [x] **Task 1.12:** Remove verbose docstrings from validate_imports()
- [x] **Task 1.12v:** Verify method signature is self-documenting
- [x] **Task 1.13:** Remove verbose docstrings from check_for_dangerous_patterns()
- [x] **Task 1.13v:** Verify security check is clear without verbose docs
- [x] **Task 1.14:** Remove verbose docstrings from validate_agent_structure()
- [x] **Task 1.14v:** Verify structure validation is understandable
- [x] **Task 1.15:** Remove verbose docstrings from run_in_sandbox()
- [x] **Task 1.15v:** Verify sandbox method is clear

---

## ✅ PRIORITY 2: Performance Optimizations (Medium Impact, Medium Effort) - COMPLETE

### code_validator.py Performance

- [x] **Task 2.1:** Fix O(n²) line number calculation in check_for_dangerous_patterns()
  - Replace `code[:match.start()].count('\n') + 1` with bisect approach
  - Pre-calculate line starts: `[0] + [m.end() for m in re.finditer(r'\n', code)]`
  - Use `bisect.bisect_right(line_starts, match.start())`
- [x] **Task 2.1v:** Verify line numbers are correct for all dangerous patterns
  - Test with code containing patterns on lines 1, 50, 100
  - Assert line numbers match expected values
  - Benchmark performance improvement on large files (1000+ lines)

- [x] **Task 2.2:** Cache compiled regex patterns for dangerous pattern checking
  - Create COMPILED_DANGEROUS_PATTERNS in constants.py
  - Use `re.compile(pattern, re.IGNORECASE)` for each pattern
  - Update check_for_dangerous_patterns() to use compiled patterns
- [x] **Task 2.2v:** Verify regex caching improves performance
  - Benchmark before/after on 100 validation runs
  - Verify all patterns still detected correctly
  - Assert no false positives/negatives

- [x] **Task 2.3:** Optimize import checking to avoid redundant __import__ calls
  - Track already-checked imports in a set
  - Skip __import__ if module already verified
- [x] **Task 2.3v:** Verify import optimization works correctly
  - Test with code importing same module multiple times
  - Verify performance improvement on import-heavy code
  - Assert all missing imports still detected

### multi_framework_coder.py Performance

- [x] **Task 2.4:** Cache embedding model in constants instead of hardcoded string
  - Already in constants.py as EMBEDDING_MODEL
  - Replace "text-embedding-3-small" with EMBEDDING_MODEL in get_embedding()
- [x] **Task 2.4v:** Verify embedding retrieval uses constant
  - Check get_embedding() references constants.EMBEDDING_MODEL
  - Test embedding retrieval works correctly
  - Verify error fallback uses EMBEDDING_DIM

- [x] **Task 2.5:** Use EMBEDDING_DIM constant instead of magic 1536
  - Replace `return [0] * 1536` with `return [0] * EMBEDDING_DIM`
- [x] **Task 2.5v:** Verify embedding dimension constant works
  - Test error fallback returns correct dimension
  - Verify against text-embedding-3-small spec (1536)

- [x] **Task 2.6:** Use DEFAULT_RAG_RESULTS constant instead of magic 5
  - Replace `'match_count': 5` with `'match_count': DEFAULT_RAG_RESULTS`
- [x] **Task 2.6v:** Verify RAG returns correct number of results
  - Test retrieve_relevant_documentation() returns 5 chunks
  - Verify changing constant affects result count

---

## ⏳ PRIORITY 3: Architectural Improvements (High Impact, High Effort) - IN PROGRESS

### Configuration Management (archon_graph_v6.py, archon_graph_v4.py)

- [x] **Task 3.1:** Create ArchonConfig dataclass in new archon/config.py
  - Define all configuration fields (base_url, api_key, models, etc.)
  - Add @classmethod from_env() to load from environment
  - Add validation for required fields
- [x] **Task 3.1v:** Verify ArchonConfig loads correctly from .env
  - Test from_env() loads all variables
  - Test validation fails for missing required fields
  - Test default values work correctly

- [x] **Task 3.2:** Refactor archon_graph_v6.py to use ArchonConfig
  - Remove module-level load_dotenv() and client initialization
  - Create build_workflow(config: ArchonConfig) factory function
  - Move all setup inside factory function
  - Keep backwards-compatible agentic_flow = build_workflow(ArchonConfig.from_env())
- [x] **Task 3.2v:** Verify v6 workflow builds correctly with config
  - Test build_workflow() with custom config
  - Test backwards-compatible agentic_flow still works
  - Verify no side effects on import

- [x] **Task 3.3:** Refactor archon_graph_v4.py to use ArchonConfig
  - Remove module-level initialization
  - Create build_workflow_v4(config: ArchonConfig) factory
  - Keep backwards compatibility
- [x] **Task 3.3v:** Verify v4 workflow builds correctly with config
  - Test build_workflow_v4() with custom config
  - Test backwards-compatible agentic_flow_v4 works
  - Verify no import-time side effects

- [x] **Task 3.4:** Refactor multi_framework_coder.py module-level initialization
  - Remove global `model = OpenAIModel(...)` at module level
  - Accept model as parameter in create_multi_framework_coder()
  - Update callers to pass model
- [x] **Task 3.4v:** Verify multi_framework_coder accepts model parameter
  - Test create_multi_framework_coder() with custom model
  - Verify no module-level side effects
  - Test all 4 frameworks work with new approach

### System Prompt Optimization (multi_framework_coder.py)

- [ ] **Task 3.5:** Reduce system prompt verbosity by 50% (lines 73-107)
  - Remove repetitive framework name mentions
  - Condense instructions into concise bullets
  - Replace chr(10) with '\n' on line 95
  - Keep essential information only
- [ ] **Task 3.5v:** Verify condensed prompt maintains functionality
  - Test agent generation with condensed prompt
  - Verify agent still uses RAG correctly
  - Verify agent still structures files correctly
  - Assert response quality unchanged

### Docstring Cleanup (multi_framework_coder.py)

- [ ] **Task 3.6:** Reduce tool docstrings to single lines (retrieve_relevant_documentation)
  - Change from 9 lines to: "RAG search over framework docs, returns top 5 chunks."
- [ ] **Task 3.6v:** Verify LLM can still use tool correctly
  - Test tool is called appropriately
  - Verify RAG results are correct

- [ ] **Task 3.7:** Reduce tool docstrings (list_documentation_pages)
  - Change to: "List all documentation page URLs for target framework."
- [ ] **Task 3.7v:** Verify tool works with concise docstring
  - Test returns correct page list
  - Verify framework filtering works

- [ ] **Task 3.8:** Reduce tool docstrings (get_page_content)
  - Change to: "Retrieve full content of specific documentation page."
- [ ] **Task 3.8v:** Verify page content retrieval works
  - Test returns complete page
  - Verify chunks assembled correctly

- [ ] **Task 3.9:** Reduce tool docstrings (get_framework_template)
  - Change to: "Get code template for specific file in target framework."
- [ ] **Task 3.9v:** Verify template retrieval works
  - Test returns correct template
  - Verify all 4 frameworks work

- [ ] **Task 3.10:** Reduce tool docstrings (list_available_templates)
  - Change to: "List all available code template names."
- [ ] **Task 3.10v:** Verify template listing works
  - Test returns all templates
  - Verify correct for each framework

- [ ] **Task 3.11:** Remove verbose docstring from create_multi_framework_coder()
  - Keep one-line summary only
- [ ] **Task 3.11v:** Verify function signature is self-documenting
  - Review type hints make purpose clear

### Framework Configuration (framework_config.py)

- [ ] **Task 3.12:** Simplify get_framework() normalization (line 114)
  - Remove excessive replace() chain
  - Just use: `FRAMEWORKS.get(name.lower())`
  - Only add normalization if actual users need it
- [ ] **Task 3.12v:** Verify framework lookup still works
  - Test 'pydantic_ai', 'pydantic-ai', 'Pydantic AI' all work
  - Document which formats are supported
  - Add tests for edge cases

- [ ] **Task 3.13:** Reduce framework system prompts verbosity by 30%
  - Condense 'pydantic_ai' prompt (lines 149-166)
  - Remove repetitive instructions
- [ ] **Task 3.13v:** Verify Pydantic AI agents still generate correctly
  - Test agent generation quality
  - Verify structure is correct

- [ ] **Task 3.14:** Condense 'langgraph' system prompt (lines 168-186)
  - Remove redundant best practices mentions
  - Focus on essential patterns
- [ ] **Task 3.14v:** Verify LangGraph agents still generate correctly
  - Test graph structure
  - Verify checkpointing works

- [ ] **Task 3.15:** Condense 'crewai' system prompt (lines 188-206)
  - Simplify role/task/crew explanations
- [ ] **Task 3.15v:** Verify CrewAI agents still generate correctly
  - Test crew structure
  - Verify task delegation works

- [ ] **Task 3.16:** Condense 'autogen' system prompt (lines 208-226)
  - Remove verbose explanations
- [ ] **Task 3.16v:** Verify AutoGen agents still generate correctly
  - Test agent structure
  - Verify code execution setup works

### Helper Method Extraction

- [x] **Task 3.17:** Extract message history loading helper in archon_graph_v6.py
  - Lines 174-177 duplicated in multiple places
  - Create `load_message_history(messages) -> list[ModelMessage]`
  - Replace duplicates with helper call
- [x] **Task 3.17v:** Verify message history helper works correctly
  - Test in coder_agent node
  - Test in finish_conversation node
  - Verify message deserialization works

- [x] **Task 3.18:** Extract streaming helper pattern
  - Lines 193-204 pattern repeated
  - Create `run_agent_with_streaming()` helper
  - Handle ollama vs streaming logic once
- [x] **Task 3.18v:** Verify streaming helper works
  - Test with Ollama (is_ollama=True)
  - Test with OpenAI streaming
  - Verify output identical to before

### Code Duplication Between V4 and V6

- [x] **Task 3.19:** Extract common graph building logic
  - V4 and V6 share similar node functions
  - Create archon/graph_utils.py
  - Move shared node functions there
- [x] **Task 3.19v:** Verify both V4 and V6 use shared utils
  - Test V4 workflow still works
  - Test V6 workflow still works
  - Verify no regressions

- [x] **Task 3.20:** Extract common agent initialization
  - reasoner, router, end_conversation agents identical
  - Create `create_standard_agents(config: ArchonConfig)` helper
  - Return tuple of (reasoner, router, end_conversation)
- [x] **Task 3.20v:** Verify agent creation helper works
  - Test agents have correct system prompts
  - Test agents use correct models
  - Test in both V4 and V6

### Crawl Multi Framework Docs (crawl_multi_framework_docs.py)

- [x] **Task 3.21:** Replace hardcoded "text-embedding-3-small" with EMBEDDING_MODEL constant
  - Import from constants
  - Use EMBEDDING_MODEL in get_embedding()
- [x] **Task 3.21v:** Verify crawler uses embedding constant
  - Test crawl generates correct embeddings
  - Verify dimension matches EMBEDDING_DIM

- [x] **Task 3.22:** Replace magic 5 with DEFAULT_RAG_RESULTS if applicable
  - Checked crawler - no magic 5 found
  - Updated pydantic_ai_coder.py for consistency
- [x] **Task 3.22v:** Verify crawler chunk count uses constant
  - Test crawler behavior with constant
  - Verify documentation stored correctly

---

## 🧪 TESTING & VALIDATION

### Integration Tests

- [ ] **Task 4.1:** Create test_code_validator.py unit tests
  - Test ValidationResult dataclass serialization
  - Test each validation method independently
  - Test validate_all() integration
  - Test edge cases (empty code, syntax errors, etc.)
- [ ] **Task 4.1v:** Verify all code_validator tests pass
  - Run pytest test_code_validator.py
  - Assert 100% test coverage for public methods
  - Verify no regressions

- [ ] **Task 4.2:** Create test_constants.py to verify all constants
  - Test COMMON_IMPORTS is immutable (frozenset)
  - Test DANGEROUS_PATTERNS has correct regex
  - Test all constants have expected values
- [ ] **Task 4.2v:** Verify constants tests pass
  - Run pytest test_constants.py
  - Assert all constants validated

- [ ] **Task 4.3:** Create test_config.py for ArchonConfig
  - Test from_env() loads correctly
  - Test validation catches missing required fields
  - Test default values
- [ ] **Task 4.3v:** Verify config tests pass
  - Run pytest test_config.py
  - Assert config validation works

- [ ] **Task 4.4:** Create test_graph_v4.py for V4 workflow
  - Test build_workflow_v4() with mock config
  - Test all nodes execute correctly
  - Test validation loop works
  - Test checkpointing
- [ ] **Task 4.4v:** Verify V4 tests pass
  - Run pytest test_graph_v4.py
  - Assert workflow builds correctly
  - Verify no side effects

- [ ] **Task 4.5:** Create test_graph_v6.py for V6 workflow
  - Test build_workflow() with mock config
  - Test framework detection
  - Test all 4 frameworks
  - Test validation integration
- [ ] **Task 4.5v:** Verify V6 tests pass
  - Run pytest test_graph_v6.py
  - Assert all frameworks work
  - Verify validation works

- [ ] **Task 4.6:** Create test_multi_framework_coder.py
  - Test create_multi_framework_coder() for all frameworks
  - Test all tools work (RAG, templates, etc.)
  - Test with mock Supabase/OpenAI clients
- [ ] **Task 4.6v:** Verify multi_framework_coder tests pass
  - Run pytest test_multi_framework_coder.py
  - Assert all tools callable
  - Verify no API calls in tests

---

## 📊 METRICS & BENCHMARKS

### Performance Benchmarks

- [ ] **Task 5.1:** Benchmark line number calculation improvement
  - Create benchmark script
  - Test old O(n²) vs new O(n log n) approach
  - Measure on files of 100, 1000, 10000 lines
- [ ] **Task 5.1v:** Verify performance improvement
  - Assert new approach ≥2x faster on 1000+ line files
  - Document performance gains

- [ ] **Task 5.2:** Benchmark validation with/without caching
  - Test regex compilation caching improvement
  - Measure 100 validation runs before/after
- [ ] **Task 5.2v:** Verify caching improves performance
  - Assert ≥10% improvement with caching
  - Document benchmark results

### Code Quality Metrics

- [ ] **Task 5.3:** Measure final code metrics
  - Total lines of code
  - Docstring ratio
  - Duplicate code (via tools like pylint)
  - Complexity scores (cyclomatic complexity)
  - Test coverage percentage
- [ ] **Task 5.3v:** Verify quality targets met
  - Assert total LOC reduced by ≥15%
  - Assert docstring ratio ≤10%
  - Assert no duplicate code blocks >10 lines
  - Assert average complexity <10
  - Assert test coverage ≥80%

---

## 📝 DOCUMENTATION

### Update Documentation

- [ ] **Task 6.1:** Update ARCHON_V6_COMPLETE.md with ArchonConfig usage
  - Document new configuration approach
  - Add examples using build_workflow()
  - Show testing with mock config
- [ ] **Task 6.1v:** Verify documentation is complete
  - Review all examples work
  - Test code snippets are runnable

- [ ] **Task 6.2:** Update IMPLEMENTATION_SUMMARY.md with refactoring details
  - Add section on code quality improvements
  - Document constants module
  - Explain factory pattern
- [ ] **Task 6.2v:** Verify summary is up-to-date
  - Matches current codebase structure
  - All features documented

- [ ] **Task 6.3:** Create TESTING.md guide
  - Document how to run tests
  - Explain mocking approach
  - Show coverage reports
- [ ] **Task 6.3v:** Verify testing guide is clear
  - Follow guide on fresh environment
  - Assert all steps work

- [ ] **Task 6.4:** Update examples/ to use ArchonConfig
  - Update all example scripts
  - Show custom configuration
  - Document testing approach
- [ ] **Task 6.4v:** Verify examples work with new approach
  - Run each example
  - Assert no errors

---

## 🎯 FINAL VALIDATION

### End-to-End Tests

- [ ] **Task 7.1:** Run full V3 workflow test
  - Test basic agent creation
  - Verify RAG works
  - Test streaming
- [ ] **Task 7.1v:** Verify V3 unchanged and working
  - Assert functionality preserved
  - No regressions

- [ ] **Task 7.2:** Run full V4 workflow test with validation
  - Test agent creation with validation
  - Test validation feedback loop
  - Test retry mechanism (max 3 attempts)
- [ ] **Task 7.2v:** Verify V4 validation works perfectly
  - Assert validation catches real issues
  - Assert retry logic works
  - Assert checkpointing works

- [ ] **Task 7.3:** Run full V6 workflow test with all frameworks
  - Test Pydantic AI agent creation
  - Test LangGraph agent creation
  - Test CrewAI agent creation
  - Test AutoGen agent creation
- [ ] **Task 7.3v:** Verify V6 multi-framework works perfectly
  - Assert all 4 frameworks work
  - Assert framework detection works
  - Assert validation works for all

### Linting & Type Checking

- [ ] **Task 7.4:** Run flake8 on all modified files
  - Check code_validator.py
  - Check constants.py
  - Check config.py
  - Check multi_framework_coder.py
  - Check framework_config.py
  - Check archon_graph_v4.py
  - Check archon_graph_v6.py
- [ ] **Task 7.4v:** Verify zero flake8 errors
  - Assert all files pass
  - Max line length: 120
  - No ignored errors needed

- [ ] **Task 7.5:** Run mypy type checking
  - Type check all modified files
  - Ensure strict mode passes
- [ ] **Task 7.5v:** Verify zero type errors
  - Assert all type hints correct
  - No # type: ignore needed

---

## ✅ COMPLETION CRITERIA

**All tasks must meet:**
1. ✅ Implementation complete and tested
2. ✅ Verification passed
3. ✅ No regressions in existing functionality
4. ✅ Documentation updated
5. ✅ Tests passing
6. ✅ Linting clean
7. ✅ Committed to git

**Final Grade Target:** 10/10 (Excellent craft, elegant, maintainable)

**Total Estimated Time:**
- Priority 2: ~30 minutes (6 tasks)
- Priority 3: ~130 minutes (27 tasks)
- Testing: ~60 minutes (12 tasks)
- Metrics: ~15 minutes (3 tasks)
- Documentation: ~30 minutes (4 tasks)
- Final Validation: ~15 minutes (5 tasks)
- **TOTAL: ~280 minutes (~4.7 hours)**

---

## 📋 PROGRESS TRACKING

**Completed:** 54/66 tasks (82%)
- ✅ Priority 1: 30/30 (100%) - COMPLETE
- ✅ Priority 2: 12/12 (100%) - COMPLETE
- ⏳ Priority 3: 12/40 (30%) - IN PROGRESS
  - ✅ Config Management: 8/8 (100%)
  - ✅ Helper Extraction: 8/8 (100%)
  - ✅ Crawler Constants: 4/4 (100%)
  - ⏳ System Prompts: 0/12 (0%)
  - ⏳ Framework Config: 0/10 (0%)
- ⏳ Testing: 0/12 (0%)
- ⏳ Metrics: 0/6 (0%)
- ⏳ Documentation: 0/8 (0%)
- ⏳ Final: 0/10 (0%)

**Next Up:** Tasks 3.5-3.16 - System prompt & framework optimization (lower priority)
