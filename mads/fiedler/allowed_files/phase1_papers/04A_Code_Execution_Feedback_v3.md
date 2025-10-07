# Requirements Validation Through Reconstruction Testing

## Abstract

We present a comprehensive framework for validating requirements extraction quality through reconstruction testing. Unlike subjective requirement reviews, our approach provides objective validation: if extracted requirements enable LLMs to reconstruct a working application with >75% test pass rate, the requirements are high quality. We leverage multiple feedback mechanisms: test pass rates, API compatibility checks, behavioral equivalence testing, and multi-LLM implementation variance. Each feedback type provides structured signals that guide requirements improvement. This paper establishes the foundational validation mechanisms that enable CETs to learn effective requirements engineering through autonomous reconstruction feedback.

**Key Innovation**: Reconstruction testing transforms requirements quality from a subjective assessment into an objective, measurable outcome—making requirements engineering trainable through supervised learning.

## 1. Introduction

The quality of extracted requirements can only be truly measured by implementation success: can an LLM reconstruct the application from the requirements? This paper presents the feedback mechanisms that transform reconstruction outcomes into training signals for requirements optimization.

### 1.1 Why Reconstruction Testing

**Traditional Requirements Validation** (subjective):
- Manual review by requirements engineers
- Checklist compliance (IEEE standards)
- Stakeholder approval
- Document completeness audits

**Reconstruction Testing** (objective):
- Extract requirements from Application A
- LLM implements Application B from requirements
- Execute original tests on Application B
- **Success metric**: Test pass rate >75%

### 1.2 Feedback Mechanisms

We focus on six primary feedback sources:

1. **Test Pass Rates**: Core success metric (functional correctness)
2. **API Compatibility**: Interface preservation validation
3. **Behavioral Equivalence**: Edge case and error handling
4. **Multi-LLM Variance**: Requirements ambiguity detection
5. **Performance Equivalence**: Non-functional requirements validation
6. **Implementation Patterns**: Common failure modes across LLMs

## 2. Reconstruction Testing Pipeline

### 2.1 End-to-End Validation Workflow

```python
class ReconstructionValidator:
    def __init__(self):
        self.llm_team = [
            'llama3.1-70b-q4',
            'deepseek-r1',
            'codellama-70b',
            'qwen2.5-coder-32b',
            'starcoder2-15b'
        ]
        self.docker_executor = DockerExecutor()  # Paper 09

    def validate_requirements(self, application, extracted_requirements):
        """Validate requirements through reconstruction"""

        # Step 1: Multi-LLM implementation
        implementations = []
        for llm in self.llm_team:
            impl = llm.implement_from_requirements(
                requirements=extracted_requirements,
                timeout=300  # 5 minutes per implementation
            )
            implementations.append({
                'llm': llm,
                'code': impl.code,
                'explanation': impl.reasoning
            })

        # Step 2: Execute tests on each implementation
        test_results = []
        for impl in implementations:
            result = self.docker_executor.run_tests(
                code=impl['code'],
                test_suite=application.tests,
                timeout=60
            )
            test_results.append({
                'llm': impl['llm'],
                'pass_rate': result.pass_rate,
                'passed_tests': result.passed,
                'failed_tests': result.failed,
                'errors': result.errors
            })

        # Step 3: Calculate aggregate metrics
        metrics = self.calculate_metrics(
            implementations=implementations,
            test_results=test_results,
            original_app=application
        )

        # Step 4: Generate feedback for CET
        feedback = self.generate_feedback(
            requirements=extracted_requirements,
            implementations=implementations,
            test_results=test_results,
            metrics=metrics
        )

        return metrics, feedback
```

### 2.2 Success Metrics Hierarchy

```python
reconstruction_metrics = {
    'tier_1_critical': {
        'test_pass_rate': {
            'target': 0.75,
            'weight': 0.50,
            'description': 'Percentage of original tests passing'
        },
        'api_compatibility': {
            'target': 0.90,
            'weight': 0.25,
            'description': 'Interface signature preservation'
        }
    },

    'tier_2_important': {
        'behavioral_equivalence': {
            'target': 0.85,
            'weight': 0.15,
            'description': 'Edge case and error handling match'
        },
        'multi_llm_consistency': {
            'target': 0.80,
            'weight': 0.10,
            'description': 'Multiple LLMs implement similarly'
        }
    }
}
```

## 3. Test Pass Rate Analysis

### 3.1 Test-Level Feedback

**Granular Success Signals:**

```python
class TestResultAnalyzer:
    def analyze_test_results(self, test_results, requirements):
        """Extract learning signals from test execution"""

        analysis = {
            'passing_tests': [],
            'failing_tests': [],
            'requirement_coverage': {}
        }

        # Map each test to requirements
        for test in test_results:
            req_id = self.map_test_to_requirement(test, requirements)

            if test.passed:
                analysis['passing_tests'].append({
                    'test': test.name,
                    'requirement': req_id,
                    'signal': 'Requirement correctly captured'
                })
            else:
                analysis['failing_tests'].append({
                    'test': test.name,
                    'requirement': req_id,
                    'error': test.error_message,
                    'signal': 'Requirement incomplete or incorrect'
                })

        # Calculate requirement-level coverage
        for req in requirements:
            related_tests = self.find_tests_for_requirement(req, test_results)
            pass_rate = sum(t.passed for t in related_tests) / len(related_tests)

            analysis['requirement_coverage'][req.id] = {
                'requirement_text': req.text,
                'tests_count': len(related_tests),
                'pass_rate': pass_rate,
                'status': 'complete' if pass_rate > 0.9 else 'incomplete'
            }

        return analysis
```

### 3.2 Failure Pattern Recognition

**Common Failure Modes:**

```python
failure_patterns = {
    'missing_edge_cases': {
        'indicator': 'Tests pass for happy path, fail for edge cases',
        'root_cause': 'Requirements didn\'t specify edge case handling',
        'example_tests': [
            'test_empty_input',
            'test_null_values',
            'test_boundary_conditions'
        ],
        'fix': 'Add explicit edge case requirements'
    },

    'missing_error_handling': {
        'indicator': 'Tests crash instead of returning errors',
        'root_cause': 'Requirements didn\'t specify error handling',
        'example_tests': [
            'test_invalid_input_raises_error',
            'test_network_failure_handling',
            'test_timeout_behavior'
        ],
        'fix': 'Add error handling requirements with specific exceptions'
    },

    'incomplete_validation': {
        'indicator': 'Tests pass invalid data',
        'root_cause': 'Requirements didn\'t specify validation rules',
        'example_tests': [
            'test_rejects_negative_numbers',
            'test_validates_email_format',
            'test_enforces_string_length'
        ],
        'fix': 'Add explicit validation requirements'
    },

    'ambiguous_functionality': {
        'indicator': 'Different LLMs implement differently, all fail tests',
        'root_cause': 'Requirements ambiguous about expected behavior',
        'example': 'Sort by "date" - ascending or descending?',
        'fix': 'Add precision to ambiguous requirements'
    }
}
```

### 3.3 Test Coverage as Requirements Completeness

```python
def assess_requirements_completeness(requirements, test_suite):
    """Check if requirements cover all tested functionality"""

    coverage_analysis = {
        'covered': [],      # Requirements with passing tests
        'partial': [],      # Requirements with some passing tests
        'uncovered': [],    # Functionality tested but not in requirements
        'missing': []       # Requirements without corresponding tests
    }

    # Forward mapping: Requirements → Tests
    for req in requirements:
        matching_tests = find_tests_for_requirement(req, test_suite)

        if not matching_tests:
            coverage_analysis['missing'].append({
                'requirement': req,
                'issue': 'No tests verify this requirement'
            })
        else:
            pass_rate = calculate_pass_rate(matching_tests)
            if pass_rate >= 0.90:
                coverage_analysis['covered'].append(req)
            else:
                coverage_analysis['partial'].append({
                    'requirement': req,
                    'pass_rate': pass_rate,
                    'failing_tests': [t for t in matching_tests if not t.passed]
                })

    # Reverse mapping: Tests → Requirements
    for test in test_suite:
        matching_reqs = find_requirements_for_test(test, requirements)

        if not matching_reqs:
            coverage_analysis['uncovered'].append({
                'test': test,
                'issue': 'Test validates functionality not in requirements',
                'inferred_requirement': infer_requirement_from_test(test)
            })

    return coverage_analysis
```

## 4. API Compatibility Validation

### 4.1 Interface Signature Checking

**Automated API Comparison:**

```python
class APICompatibilityChecker:
    def validate_api_compatibility(self, original_app, reconstructed_app):
        """Check if reconstructed app preserves API"""

        original_api = self.extract_api(original_app)
        reconstructed_api = self.extract_api(reconstructed_app)

        compatibility = {
            'functions': self.compare_functions(original_api, reconstructed_api),
            'classes': self.compare_classes(original_api, reconstructed_api),
            'endpoints': self.compare_endpoints(original_api, reconstructed_api),
            'data_models': self.compare_data_models(original_api, reconstructed_api)
        }

        compatibility_score = self.calculate_score(compatibility)

        return compatibility_score, compatibility

    def compare_functions(self, original, reconstructed):
        """Compare function signatures"""

        results = {
            'matching': [],
            'missing': [],
            'signature_mismatch': []
        }

        for func_name, orig_func in original.functions.items():
            if func_name not in reconstructed.functions:
                results['missing'].append({
                    'function': func_name,
                    'signature': orig_func.signature,
                    'feedback': 'Requirements missing function specification'
                })
            else:
                recon_func = reconstructed.functions[func_name]
                if orig_func.signature == recon_func.signature:
                    results['matching'].append(func_name)
                else:
                    results['signature_mismatch'].append({
                        'function': func_name,
                        'original': orig_func.signature,
                        'reconstructed': recon_func.signature,
                        'feedback': 'Requirements ambiguous about signature'
                    })

        return results
```

### 4.2 Data Model Validation

```python
def validate_data_models(original_schema, reconstructed_schema):
    """Validate data structure preservation"""

    validation = {
        'field_matches': [],
        'missing_fields': [],
        'type_mismatches': [],
        'constraint_violations': []
    }

    for entity_name, orig_entity in original_schema.items():
        recon_entity = reconstructed_schema.get(entity_name)

        if not recon_entity:
            validation['missing_fields'].append({
                'entity': entity_name,
                'feedback': 'Requirements missing data model specification'
            })
            continue

        # Field-by-field comparison
        for field_name, orig_field in orig_entity.fields.items():
            recon_field = recon_entity.fields.get(field_name)

            if not recon_field:
                validation['missing_fields'].append({
                    'entity': entity_name,
                    'field': field_name,
                    'feedback': 'Field not specified in requirements'
                })
            elif orig_field.type != recon_field.type:
                validation['type_mismatches'].append({
                    'entity': entity_name,
                    'field': field_name,
                    'original_type': orig_field.type,
                    'reconstructed_type': recon_field.type,
                    'feedback': 'Requirements ambiguous about field type'
                })
            else:
                validation['field_matches'].append(f"{entity_name}.{field_name}")

    return validation
```

## 5. Multi-LLM Implementation Variance

### 5.1 Variance as Ambiguity Detection

**Key Insight**: If different LLMs implement requirements differently, the requirements are ambiguous.

```python
class ImplementationVarianceAnalyzer:
    def detect_requirement_ambiguity(self, implementations, requirements):
        """Find ambiguous requirements by analyzing variance"""

        variance_analysis = {
            'consistent_implementations': [],
            'divergent_implementations': [],
            'ambiguous_requirements': []
        }

        # Compare implementations pairwise
        for i, impl_a in enumerate(implementations):
            for impl_b in implementations[i+1:]:
                differences = self.compare_implementations(impl_a, impl_b)

                for diff in differences:
                    # Map difference to requirement
                    req = self.find_responsible_requirement(diff, requirements)

                    if req:
                        variance_analysis['ambiguous_requirements'].append({
                            'requirement': req,
                            'divergence': diff,
                            'llm_a_interpretation': impl_a.approach,
                            'llm_b_interpretation': impl_b.approach,
                            'feedback': 'Requirement needs clarification'
                        })

        return variance_analysis

    def compare_implementations(self, impl_a, impl_b):
        """Find implementation differences"""

        differences = []

        # Algorithm differences
        if impl_a.algorithm != impl_b.algorithm:
            differences.append({
                'type': 'algorithm',
                'detail': f"{impl_a.algorithm} vs {impl_b.algorithm}"
            })

        # Data structure differences
        if impl_a.data_structures != impl_b.data_structures:
            differences.append({
                'type': 'data_structure',
                'detail': f"{impl_a.data_structures} vs {impl_b.data_structures}"
            })

        # Error handling differences
        if impl_a.error_handling != impl_b.error_handling:
            differences.append({
                'type': 'error_handling',
                'detail': 'Different exception handling approaches'
            })

        return differences
```

### 5.2 Consensus-Based Validation

```python
def validate_through_consensus(implementations, test_results):
    """Use LLM consensus to validate requirements quality"""

    consensus = {
        'universal_pass': [],  # All LLMs passed this test
        'majority_pass': [],   # >50% LLMs passed
        'universal_fail': [],  # All LLMs failed this test
        'controversial': []    # Mixed results
    }

    for test_name in test_results[0].tests:
        results = [impl.tests[test_name] for impl in test_results]
        pass_count = sum(1 for r in results if r.passed)
        pass_rate = pass_count / len(results)

        if pass_rate == 1.0:
            consensus['universal_pass'].append({
                'test': test_name,
                'feedback': 'Requirement clear and complete'
            })
        elif pass_rate == 0.0:
            consensus['universal_fail'].append({
                'test': test_name,
                'feedback': 'Requirement missing or incorrect'
            })
        elif pass_rate >= 0.5:
            consensus['majority_pass'].append({
                'test': test_name,
                'pass_rate': pass_rate,
                'feedback': 'Requirement mostly clear, some ambiguity'
            })
        else:
            consensus['controversial'].append({
                'test': test_name,
                'pass_rate': pass_rate,
                'feedback': 'Requirement highly ambiguous'
            })

    return consensus
```

## 6. Behavioral Equivalence Testing

### 6.1 Edge Case Validation

```python
class BehavioralEquivalenceTester:
    def test_edge_cases(self, original_app, reconstructed_app):
        """Validate edge case handling equivalence"""

        edge_cases = {
            'empty_input': self.test_empty_input(original_app, reconstructed_app),
            'null_values': self.test_null_values(original_app, reconstructed_app),
            'boundary_conditions': self.test_boundaries(original_app, reconstructed_app),
            'invalid_input': self.test_invalid_input(original_app, reconstructed_app),
            'concurrent_access': self.test_concurrency(original_app, reconstructed_app)
        }

        equivalence_score = sum(
            1 for result in edge_cases.values() if result['equivalent']
        ) / len(edge_cases)

        return equivalence_score, edge_cases

    def test_empty_input(self, original, reconstructed):
        """Test handling of empty/missing input"""

        test_cases = [
            {'input': None},
            {'input': ''},
            {'input': []},
            {'input': {}}
        ]

        results = []
        for case in test_cases:
            orig_result = original.execute(case['input'])
            recon_result = reconstructed.execute(case['input'])

            equivalent = self.compare_behavior(orig_result, recon_result)
            results.append({
                'input': case['input'],
                'equivalent': equivalent,
                'original_output': orig_result,
                'reconstructed_output': recon_result
            })

        return {
            'equivalent': all(r['equivalent'] for r in results),
            'details': results,
            'feedback': 'Edge case requirements complete' if all(r['equivalent'] for r in results)
                       else 'Edge case requirements incomplete'
        }
```

### 6.2 Error Handling Equivalence

```python
def validate_error_handling(original_app, reconstructed_app, error_scenarios):
    """Check if error handling matches"""

    error_equivalence = {
        'matching_errors': [],
        'missing_error_handling': [],
        'incorrect_error_types': []
    }

    for scenario in error_scenarios:
        orig_error = trigger_error(original_app, scenario)
        recon_error = trigger_error(reconstructed_app, scenario)

        if orig_error and recon_error:
            if type(orig_error) == type(recon_error):
                error_equivalence['matching_errors'].append({
                    'scenario': scenario,
                    'error_type': type(orig_error).__name__
                })
            else:
                error_equivalence['incorrect_error_types'].append({
                    'scenario': scenario,
                    'original_error': type(orig_error).__name__,
                    'reconstructed_error': type(recon_error).__name__,
                    'feedback': 'Requirements ambiguous about error types'
                })
        elif orig_error and not recon_error:
            error_equivalence['missing_error_handling'].append({
                'scenario': scenario,
                'original_error': type(orig_error).__name__,
                'feedback': 'Requirements missing error handling specification'
            })

    return error_equivalence
```

## 7. Feedback Generation for CET Training

### 7.1 Structured Learning Signals

```python
class ReconstructionFeedbackGenerator:
    def generate_cet_feedback(self, requirements, implementations, test_results):
        """Generate structured feedback for CET learning"""

        feedback = {
            'overall_score': self.calculate_overall_score(test_results),
            'requirement_quality': {},
            'improvement_suggestions': []
        }

        # Requirement-level feedback
        for req in requirements:
            req_feedback = self.analyze_requirement(
                requirement=req,
                implementations=implementations,
                test_results=test_results
            )

            feedback['requirement_quality'][req.id] = req_feedback

            if req_feedback['quality'] < 0.75:
                feedback['improvement_suggestions'].append({
                    'requirement': req,
                    'issue': req_feedback['issue'],
                    'suggestion': req_feedback['suggestion']
                })

        return feedback

    def analyze_requirement(self, requirement, implementations, test_results):
        """Analyze single requirement quality"""

        related_tests = find_tests_for_requirement(requirement, test_results)

        if not related_tests:
            return {
                'quality': 0.0,
                'issue': 'No tests validate this requirement',
                'suggestion': 'Requirement may be untestable or incorrectly mapped'
            }

        pass_rates = [
            sum(1 for t in impl_tests if t.passed) / len(impl_tests)
            for impl_tests in [find_tests(impl, related_tests) for impl in implementations]
        ]

        avg_pass_rate = sum(pass_rates) / len(pass_rates)
        variance = calculate_variance(pass_rates)

        if avg_pass_rate >= 0.9 and variance < 0.1:
            return {
                'quality': 1.0,
                'issue': None,
                'suggestion': 'Requirement clear and complete'
            }
        elif avg_pass_rate >= 0.75 and variance >= 0.1:
            return {
                'quality': 0.75,
                'issue': 'High variance in implementation success',
                'suggestion': 'Add precision to reduce ambiguity'
            }
        elif avg_pass_rate < 0.75:
            return {
                'quality': avg_pass_rate,
                'issue': 'Low pass rate indicates incomplete requirement',
                'suggestion': 'Add missing details or edge cases'
            }
```

### 7.2 Training Signal Computation

```python
def compute_training_loss(extracted_requirements, reconstruction_metrics):
    """Calculate loss for CET training"""

    # Primary loss: Test pass rate
    test_pass_rate = reconstruction_metrics['avg_test_pass_rate']
    test_loss = max(0, 0.75 - test_pass_rate)  # Target: 75%+

    # Secondary loss: API compatibility
    api_score = reconstruction_metrics['api_compatibility']
    api_loss = max(0, 0.90 - api_score)  # Target: 90%+

    # Tertiary loss: Implementation consistency
    consistency = reconstruction_metrics['llm_consistency']
    consistency_loss = max(0, 0.80 - consistency)  # Target: 80%+

    # Weighted combination
    total_loss = (
        0.5 * test_loss +
        0.3 * api_loss +
        0.2 * consistency_loss
    )

    return {
        'total_loss': total_loss,
        'test_loss': test_loss,
        'api_loss': api_loss,
        'consistency_loss': consistency_loss,
        'gradient': calculate_gradient(extracted_requirements, reconstruction_metrics)
    }
```

## 8. Infrastructure Integration

### 8.1 Docker Execution Environment

**Containerized Testing** (see Paper 09):

```python
class ReconstructionExecutor:
    def __init__(self):
        self.docker_client = DockerClient()
        self.network_mode = 'none'  # Isolated execution

    def execute_reconstruction_test(self, original_app, requirements):
        """Execute full reconstruction test in Docker"""

        # Step 1: Generate implementations
        implementations = self.generate_implementations(requirements)

        # Step 2: Execute each in isolated container
        results = []
        for impl in implementations:
            container = self.docker_client.run(
                image='python:3.9-slim',
                code=impl.code,
                tests=original_app.tests,
                network_mode=self.network_mode,
                timeout=60,
                memory_limit='512m'
            )

            result = container.wait_for_completion()
            results.append(result)

            container.cleanup()

        return results
```

### 8.2 LLM Orchestra Integration

**Multi-LLM Coordination** (see Paper 10):

```python
llm_orchestra_config = {
    'code_generators': {
        'local': ['llama3.1-70b-q4', 'mistral-large-q4'],
        'together_ai': ['deepseek-r1', 'codellama-70b', 'qwen2.5-coder-32b'],
        'rotation_frequency': '4 hours'
    },

    'test_evaluators': {
        'always_loaded': ['codet5-large', 'graphcodebert'],
        'purpose': 'Analyze test failures and suggest requirement improvements'
    }
}
```

## 9. Success Criteria and Metrics

### 9.1 Reconstruction Success Thresholds

```python
success_thresholds = {
    'minimum_viable': {
        'test_pass_rate': 0.75,
        'api_compatibility': 0.85,
        'behavioral_equivalence': 0.70
    },

    'target_quality': {
        'test_pass_rate': 0.85,
        'api_compatibility': 0.95,
        'behavioral_equivalence': 0.85,
        'llm_consistency': 0.80
    },

    'excellent_quality': {
        'test_pass_rate': 0.95,
        'api_compatibility': 0.99,
        'behavioral_equivalence': 0.95,
        'llm_consistency': 0.90
    }
}
```

### 9.2 Validation Protocol

**Standard Validation Procedure:**

1. Extract requirements from Application A (using CET-D)
2. Generate 5 independent implementations using LLM orchestra
3. Execute original test suite on each implementation
4. Check API compatibility for each implementation
5. Test behavioral equivalence for each implementation
6. Calculate aggregate metrics
7. Generate feedback for CET training
8. Update CET weights based on reconstruction success

**Success Criteria**: Application achieves target quality thresholds across all metrics.

### 9.3 Gold Standard Creation Process

**Manual Requirements Baseline:**

To establish ground truth for CET-D training and evaluation, we create manual gold standard requirements through a rigorous multi-reviewer process:

```python
gold_standard_workflow = {
    'step_1_independent_creation': {
        'reviewers': 2,
        'process': 'Each expert independently creates requirements from codebase',
        'constraints': 'No communication between reviewers',
        'time_limit': '2-4 hours per application',
        'output': 'Two independent requirement sets'
    },

    'step_2_comparison': {
        'method': 'Side-by-side requirement comparison',
        'identification': 'Mark agreements and disagreements',
        'categorization': 'Group by requirement type (functional, non-functional, technical)',
        'output': 'Disagreement catalog with specific items'
    },

    'step_3_conflict_resolution': {
        'trigger': 'Any requirement present in one set but missing/different in other',
        'resolver': 'Third expert reviewer (not involved in step 1)',
        'process': 'Review both versions + original codebase',
        'decision': 'Accept version A, accept version B, or create hybrid',
        'rationale': 'Document reason for each resolution',
        'output': 'Consensus requirements set'
    },

    'step_4_reconstruction_validation': {
        'method': 'Multi-LLM reconstruction testing',
        'implementations': '5 independent LLM implementations from gold standard',
        'validation': 'Test pass rate must be >85% (expert quality target)',
        'iteration': 'If < 85%, refine requirements and retest',
        'output': 'Validated gold standard requirements'
    }
}
```

**Expected Gold Standard Quality:**

| Metric | Target | Rationale |
|--------|--------|-----------|
| Test pass rate | >85% | Human experts not perfect, but high quality |
| Requirements completeness | >92% | Expert domain knowledge captures details |
| Requirements clarity | >95% | Professional technical writing skills |
| Inter-reviewer agreement | >80% | Experts mostly agree on critical requirements |

**Gold Standard Creation Cost:**

- Time per application: 6-10 hours total (2 reviewers × 2-4h + 1 resolver × 2h)
- Applications: 50 total (40 training + 10 hold-out)
- Total effort: 300-500 hours for complete gold standard dataset
- Justification: One-time investment, enables objective CET-D evaluation

**Usage of Gold Standards:**

1. **Training Target**: CET-D learns to match gold standard quality
2. **Evaluation Benchmark**: CET-D compared against expert performance
3. **Disagreement Analysis**: Patterns in expert disagreements inform training
4. **Quality Ceiling**: Establishes realistic performance expectations

### 9.4 Human Validation and Percent Agreement Tracking

**Percent Agreement Methodology:**

For our 5-person research lab context, percent agreement provides appropriate validation rigor without requiring formal Inter-Rater Reliability (IRR) statistics:

```python
agreement_tracking = {
    'scoring_dimensions': {
        'completeness': '0-10 scale (all requirements captured?)',
        'clarity': '0-10 scale (unambiguous specifications?)',
        'testability': '0-10 scale (can be objectively validated?)',
        'accuracy': '0-10 scale (match actual implementation?)'
    },

    'agreement_calculation': {
        'method': 'Percent agreement per dimension',
        'agreement_threshold': 'Score difference ≤ 1 point',
        'disagreement_threshold': 'Score difference > 1 point',
        'formula': 'percent_agreement = (agreed_items / total_items) * 100'
    },

    'resolution_protocol': {
        'disagreement_handling': 'Third reviewer resolves (median of 3 scores)',
        'documentation': 'Record reason for disagreement',
        'training_signal': 'High-disagreement items indicate ambiguity',
        'calibration': 'Periodic reviewer alignment discussions'
    }
}
```

**Agreement Metrics Progression:**

| Phase | Percent Agreement | Disagreements | Interpretation |
|-------|------------------|---------------|----------------|
| Initial (Week 1) | 68% | 32% of requirements | Learning phase, calibration needed |
| Month 1 | 79% | 21% of requirements | Reviewers aligning on standards |
| Month 3 | 87% | 13% of requirements | Strong consistency emerging |
| Month 6 (Target) | >90% | <10% of requirements | High inter-reviewer reliability |

**Disagreement Resolution Workflow:**

1. **Independent Scoring**: Reviewers 1 and 2 score requirements independently
2. **Agreement Check**: Calculate percent agreement across all dimensions
3. **Flag Disagreements**: Identify requirements with score difference > 1 point
4. **Third Reviewer Resolution**:
   - Reviews both scores + original requirements
   - Provides independent score
   - Median of three scores becomes final
   - Documents rationale for resolution
5. **Pattern Analysis**: Track common disagreement types for reviewer calibration

**Using Disagreements as Training Signals:**

```python
disagreement_enrichment = {
    'ambiguity_detection': 'High-disagreement requirements reveal unclear aspects',
    'training_examples': 'Add disagreement cases to CET-D training data',
    'requirement_refinement': 'Improve requirements that caused confusion',
    'evaluator_calibration': 'Use disagreements to align reviewer interpretations',
    'continuous_improvement': 'Track agreement trends over time'
}
```

**Expected Benefits:**

- **Quantitative Validation**: Numerical measure of review consistency
- **Improvement Tracking**: Clear progression toward high agreement
- **Training Data Quality**: Disagreements enrich CET-D learning
- **Process Refinement**: Identifies systematic ambiguities for correction
- **Scientific Rigor**: Appropriate methodology for 5-person lab context

**Comparison to Formal IRR:**

| Approach | Our Method (Percent Agreement) | Formal IRR (Cohen's Kappa) |
|----------|-------------------------------|----------------------------|
| Team size | 5-person research lab | Large-scale annotation projects |
| Sample size | 50 applications | Hundreds/thousands of items |
| Statistical rigor | Appropriate for proof-of-concept | Required for production systems |
| Disagreement handling | Third reviewer resolution | Statistical modeling |
| Training signal | Rich qualitative insights | Quantitative reliability only |

Our percent agreement approach balances scientific rigor with practical feasibility for proof-of-concept validation.

## 10. Conclusion

Reconstruction testing provides objective, automated validation of requirements extraction quality. By measuring test pass rates, API compatibility, and behavioral equivalence, we transform requirements engineering from a subjective art into a trainable science.

**Key Contributions:**

1. **Objective Validation**: Test pass rates provide clear success metrics
2. **Automated Feedback**: Reconstruction failures pinpoint requirement deficiencies
3. **Scalable Evaluation**: Thousands of applications can be validated automatically
4. **Multi-LLM Consensus**: Implementation variance reveals requirement ambiguity
5. **Training Signals**: Reconstruction metrics directly guide CET improvement

This framework enables Phase 3 of progressive training (Paper 02), where CETs learn to extract high-quality requirements through iterative reconstruction testing feedback.

---

**Total Length**: ~850 lines (right-sized from 1836)
