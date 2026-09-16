"""M4 — Project-proposal generation component.

Converts Potential Research Opportunities into 3–5 concrete, buildable
ProjectProposal objects grounded directly in the opportunities and their
underlying evidence.

Operates deterministically and locally without LLM or external dependencies.
Flexible across ResearchOpportunity objects, plain objects, and dictionaries.

Responsible AI constraints:
- Generated items represent buildable engineering/research project directions.
- Does NOT claim that a proposal is definitely novel or that a research gap
  has been discovered.
- Uses exact novelty_confidence = "Requires human validation".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from backend.app.research_intelligence.models import (
    ProjectProposal,
    ResearchOpportunity,
)

# Desired range of proposals to generate
MIN_PROPOSALS = 3
MAX_PROPOSALS = 5


@dataclass(frozen=True)
class ProposalDirection:
    """A concrete implementation direction for a research opportunity."""

    title: str
    summary: str
    problem_statement: str
    objectives: tuple[str, ...]
    proposed_methods: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    key_features: tuple[str, ...]
    technical_approach: tuple[str, ...]
    feasibility_notes: str


@dataclass(frozen=True)
class DomainBlueprint:
    """Blueprint providing distinct buildable directions for a domain."""

    domain_id: str
    trigger_terms: frozenset[str]
    directions: tuple[ProposalDirection, ...]


DOMAIN_BLUEPRINTS: tuple[DomainBlueprint, ...] = (
    DomainBlueprint(
        domain_id="data_efficiency",
        trigger_terms=frozenset({
            "data", "dataset", "datasets", "sample", "samples", "scarcity",
            "few-shot", "examples", "corpus", "labeled", "data-efficient",
        }),
        directions=(
            ProposalDirection(
                title="Data-Efficient Learning Benchmark Platform",
                summary=(
                    "A reproducible benchmarking framework to systematically evaluate semi-supervised, "
                    "self-supervised, and synthetic augmentation methods on low-data regimes."
                ),
                problem_statement=(
                    "Modern deep learning models depend heavily on massive labeled datasets, "
                    "making training costly and difficult in low-resource domains."
                ),
                objectives=(
                    "Benchmark multiple data-efficient learning strategies under varying data budgets (1%, 5%, 10%).",
                    "Measure downstream generalization and data efficiency curves across standard datasets.",
                    "Provide standardized evaluation metrics for sample efficiency.",
                ),
                proposed_methods=(
                    "PyTorch empirical testbed",
                    "Semi-supervised algorithms (FixMatch, pseudo-labeling)",
                    "Synthetic data generation",
                    "Automated sample ablation harness",
                ),
                expected_outcomes=(
                    "Open-source comparative benchmark suite",
                    "Empirical data-efficiency Pareto frontiers",
                    "Actionable selection guidelines for resource-constrained practitioners",
                ),
                key_features=(
                    "Modular data loader with fractional sampling",
                    "Automated hyperparameter grid runner",
                    "Sample efficiency leaderboard visualization",
                ),
                technical_approach=(
                    "Python", "PyTorch", "Hugging Face Datasets", "Weights & Biases",
                ),
                feasibility_notes="High feasibility. Runs on consumer-grade GPU hardware with public datasets.",
            ),
            ProposalDirection(
                title="Automated Synthetic Data Augmentation Pipeline",
                summary=(
                    "An end-to-end augmentation pipeline integrating generative sampling with "
                    "validation filtering to expand scarce training corpora."
                ),
                problem_statement=(
                    "Manual data collection and labeling is prohibitive for niche domains with scarce samples."
                ),
                objectives=(
                    "Generate class-conditional synthetic training samples.",
                    "Filter low-fidelity synthetic data via confidence thresholding.",
                    "Demonstrate performance improvements on downstream classifiers.",
                ),
                proposed_methods=(
                    "Generative data synthesis",
                    "Feature distribution fidelity scoring",
                    "Curriculum data mixing",
                ),
                expected_outcomes=(
                    "Plug-and-play augmentation module",
                    "Validated performance gains over classical heuristics",
                ),
                key_features=(
                    "Class balance adjuster",
                    "Semantic fidelity filter",
                    "Exportable augmented dataset bundles",
                ),
                technical_approach=(
                    "Python", "PyTorch", "Diffusers / Generative Models", "Scikit-learn",
                ),
                feasibility_notes="Moderate feasibility. Requires pre-trained generative checkpoints.",
            ),
            ProposalDirection(
                title="Active Learning and Weak Supervision Toolkit",
                summary=(
                    "A framework combining uncertainty sampling and programmatic labeling heuristics "
                    "to minimize manual annotation costs."
                ),
                problem_statement=(
                    "Label acquisition budget is strictly limited, requiring optimal sample selection for annotation."
                ),
                objectives=(
                    "Implement diversity and uncertainty active learning query strategies.",
                    "Integrate programmatic labeling functions.",
                    "Achieve 90% full-data performance with under 20% labeled data.",
                ),
                proposed_methods=(
                    "Uncertainty estimation",
                    "Core-set selection",
                    "Programmatic weak supervision integration",
                ),
                expected_outcomes=(
                    "Interactive active learning labeling loop",
                    "Documented sample reduction metrics",
                ),
                key_features=(
                    "Query strategy selector",
                    "Labeling function matrix debugger",
                    "Annotation budget tracker",
                ),
                technical_approach=(
                    "Python", "modAL", "Snorkel", "FastAPI backend",
                ),
                feasibility_notes="High feasibility. Can be evaluated on existing academic benchmarks.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="compute_optimization",
        trigger_terms=frozenset({
            "compute", "computational", "gpu", "gpus", "hardware", "memory",
            "flops", "footprint", "vram", "ram", "compression", "quantization", "peft",
        }),
        directions=(
            ProposalDirection(
                title="Model Compression and Quantization Toolkit",
                summary=(
                    "A modular toolkit for post-training quantization and structured pruning to "
                    "reduce GPU memory footprint and compute overhead."
                ),
                problem_statement=(
                    "Large model architectures demand excessive computational resources and VRAM, "
                    "hindering practical deployment on standard hardware."
                ),
                objectives=(
                    "Quantize model weights to 4-bit and 8-bit precision with minimal accuracy degradation.",
                    "Profile memory footprint and FLOPs reduction.",
                    "Deploy compressed models to consumer-grade hardware.",
                ),
                proposed_methods=(
                    "BitsAndBytes / AWQ quantization",
                    "Structured magnitude pruning",
                    "ONNX runtime inference",
                ),
                expected_outcomes=(
                    "Reproducible compression pipeline",
                    "Hardware profiling benchmarks",
                    "Deployment runtimes",
                ),
                key_features=(
                    "Automated quantization profiler",
                    "Per-layer sensitivity analysis",
                    "Latency vs VRAM Pareto plots",
                ),
                technical_approach=(
                    "Python", "PyTorch", "BitsAndBytes", "AutoAWQ", "ONNX Runtime",
                ),
                feasibility_notes="High feasibility. Runs on single-GPU hardware using open-source libraries.",
            ),
            ProposalDirection(
                title="Parameter-Efficient Fine-Tuning (PEFT) Benchmark",
                summary=(
                    "A comparative benchmarking harness evaluating LoRA, QLoRA, and Prefix Tuning "
                    "across diverse model scales and tasks."
                ),
                problem_statement=(
                    "Full model fine-tuning incurs prohibitive computational and storage overhead."
                ),
                objectives=(
                    "Compare parameter efficiency, convergence speed, and memory usage across PEFT methods.",
                    "Evaluate multi-task adapter composability.",
                ),
                proposed_methods=(
                    "Adapter-based parameter isolation",
                    "Low-rank matrix decomposition",
                    "Memory-profiling telemetry",
                ),
                expected_outcomes=(
                    "Comprehensive PEFT empirical report",
                    "Reusable adapter checkpoint library",
                ),
                key_features=(
                    "Adapter modular switcher",
                    "VRAM telemetry logger",
                    "Cross-task evaluation harness",
                ),
                technical_approach=(
                    "Python", "PEFT", "Transformers", "Accelerate",
                ),
                feasibility_notes="High feasibility. Minimal compute overhead required.",
            ),
            ProposalDirection(
                title="Knowledge Distillation Acceleration Suite",
                summary=(
                    "A teacher-student distillation pipeline compressing heavy foundational models "
                    "into lightweight task-specific student models."
                ),
                problem_statement=(
                    "Deploying large teacher models at scale produces excessive computational operational expenses."
                ),
                objectives=(
                    "Transfer soft-label logits and intermediate representations to compact students.",
                    "Retain 95% of teacher accuracy with a 4x reduction in parameter count.",
                ),
                proposed_methods=(
                    "Logit distillation",
                    "Hidden state feature alignment",
                    "Student architecture optimization",
                ),
                expected_outcomes=(
                    "Lightweight student model weights",
                    "Distillation training recipe repository",
                ),
                key_features=(
                    "Loss balancing configurator",
                    "Intermediate layer projection mapping",
                    "Throughput validation test suite",
                ),
                technical_approach=(
                    "Python", "PyTorch", "TorchDistill", "Hugging Face",
                ),
                feasibility_notes="Moderate feasibility. Requires teacher inference passes.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="latency_acceleration",
        trigger_terms=frozenset({
            "latency", "inference", "runtime", "speed", "throughput", "delay",
            "response time", "lag", "low-latency",
        }),
        directions=(
            ProposalDirection(
                title="Low-Latency Speculative Decoding Accelerator",
                summary=(
                    "An inference acceleration framework implementing speculative decoding and "
                    "KV-cache compression for real-time applications."
                ),
                problem_statement=(
                    "Autoregressive generation suffers from sequential token bottlenecks, "
                    "causing high latency during interactive queries."
                ),
                objectives=(
                    "Implement small draft model speculative verification.",
                    "Compress KV-cache with minimal accuracy loss.",
                    "Reduce latency by at least 40% on interactive queries.",
                ),
                proposed_methods=(
                    "Speculative sampling",
                    "Paged attention / KV-cache quantization",
                    "Streaming response profiling",
                ),
                expected_outcomes=(
                    "Inference acceleration engine",
                    "Latency vs quality evaluation harness",
                ),
                key_features=(
                    "Draft-target model coordinator",
                    "Speculative token verification tree",
                    "Time-to-first-token benchmark reporter",
                ),
                technical_approach=(
                    "Python", "vLLM / TGI", "PyTorch", "C++ bindings",
                ),
                feasibility_notes="High feasibility with open-source draft and target model pairs.",
            ),
            ProposalDirection(
                title="Dynamic KV-Cache Compression and Memory Manager",
                summary=(
                    "A runtime memory management system compressing attention keys and values "
                    "to preserve throughput during high-concurrency bursts."
                ),
                problem_statement=(
                    "KV-cache expansion consumes memory linearly with sequence length, causing bottlenecks."
                ),
                objectives=(
                    "Implement dynamic token eviction and quantization on attention caches.",
                    "Preserve generation coherence across multi-thousand token contexts.",
                ),
                proposed_methods=(
                    "Attention sink preservation",
                    "Adaptive cache pruning",
                    "Int8 cache quantization",
                ),
                expected_outcomes=(
                    "High-throughput inference cache manager",
                    "Memory conservation benchmark suite",
                ),
                key_features=(
                    "Attention head significance analyzer",
                    "Streaming token eviction queue",
                    "Context retention evaluator",
                ),
                technical_approach=(
                    "Python", "FlashAttention", "PyTorch", "Triton",
                ),
                feasibility_notes="Moderate feasibility. High technical value for long-context apps.",
            ),
            ProposalDirection(
                title="Real-Time Query Response Caching and Prefetching Engine",
                summary=(
                    "A semantic caching and speculative prefetching proxy that serves frequent "
                    "or similar query patterns with sub-millisecond response times."
                ),
                problem_statement=(
                    "Repeated or semantically close queries trigger redundant forward passes, wasting compute."
                ),
                objectives=(
                    "Develop vector-indexed semantic response caching.",
                    "Implement predictive query prefetching for conversational flows.",
                ),
                proposed_methods=(
                    "Embedding similarity lookup",
                    "Cache invalidation heuristic rules",
                    "Asynchronous background prefetching",
                ),
                expected_outcomes=(
                    "Semantic caching proxy middleware",
                    "Latency reduction audit logs",
                ),
                key_features=(
                    "Vector distance cache lookup",
                    "Dynamic TTL freshness policies",
                    "Hit-rate telemetry dashboard",
                ),
                technical_approach=(
                    "Python", "FastAPI", "FAISS / ChromaDB", "Redis",
                ),
                feasibility_notes="High feasibility. Easily testable with standard HTTP client requests.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="scalability",
        trigger_terms=frozenset({
            "scalability", "scale", "scaling", "large-scale", "unscalable", "bottlenecks",
        }),
        directions=(
            ProposalDirection(
                title="Sub-Quadratic Architecture and Scaling Benchmark",
                summary=(
                    "A comparative framework evaluating linear-attention, state-space models (Mamba), "
                    "and standard Transformers on sequence scaling limits."
                ),
                problem_statement=(
                    "Quadratic attention complexity prevents standard Transformer models from "
                    "scaling efficiently to ultra-long contexts."
                ),
                objectives=(
                    "Benchmark throughput and memory scaling as context lengths scale from 4k to 64k tokens.",
                    "Evaluate task retention and retrieval accuracy across architectures.",
                ),
                proposed_methods=(
                    "State-space model benchmarking",
                    "Linear attention approximations",
                    "Synthetic long-context needle-in-a-haystack testing",
                ),
                expected_outcomes=(
                    "Comprehensive architecture scaling empirical study",
                    "Standardized long-sequence benchmarking harness",
                ),
                key_features=(
                    "Configurable context length stress-tester",
                    "Memory vs sequence length telemetry",
                    "Retrieval accuracy evaluator",
                ),
                technical_approach=(
                    "Python", "PyTorch", "Mamba / SSM", "FlashAttention-2",
                ),
                feasibility_notes="High feasibility using public pre-trained checkpoints.",
            ),
            ProposalDirection(
                title="Distributed Pipeline and Activation Partitioning Testbed",
                summary=(
                    "An experimental platform evaluating model-parallel, pipeline-parallel, and "
                    "ZeRO memory partitioning configurations for medium-scale training."
                ),
                problem_statement=(
                    "Scaling model sizes across multi-GPU setups suffers from pipeline bubbles and bandwidth bottlenecks."
                ),
                objectives=(
                    "Measure communication overhead across pipeline stages.",
                    "Optimize activation checkpointing schedules to maximize hardware utilization.",
                ),
                proposed_methods=(
                    "DeepSpeed ZeRO stages 1-3",
                    "Activation recomputation scheduling",
                    "Inter-node bandwidth telemetry",
                ),
                expected_outcomes=(
                    "Optimal distributed configuration guidelines",
                    "Automated cluster scaling profiler",
                ),
                key_features=(
                    "Distributed topology mapper",
                    "Communication bubble visualizer",
                    "Throughput scaling curve generator",
                ),
                technical_approach=(
                    "Python", "PyTorch Distributed", "DeepSpeed", "Ray",
                ),
                feasibility_notes="Moderate feasibility. Simulates or runs across available local/cloud GPUs.",
            ),
            ProposalDirection(
                title="Hierarchical Query Routing System for Large Workloads",
                summary=(
                    "A hierarchical routing system dispatching queries to tiered models of varying "
                    "capacities based on query complexity."
                ),
                problem_statement=(
                    "Routing all queries to massive models creates scaling bottlenecks and unsustainable operating costs."
                ),
                objectives=(
                    "Train an ultra-lightweight complexity classifier router.",
                    "Achieve 80% routing to small models while preserving 98% overall quality.",
                ),
                proposed_methods=(
                    "Query embedding classification",
                    "Confidence thresholding cascade",
                    "Fallback verification routing",
                ),
                expected_outcomes=(
                    "Hierarchical routing proxy",
                    "Cost and latency saving metrics report",
                ),
                key_features=(
                    "Query hardness estimator",
                    "Tiered model fallback controller",
                    "Quality parity verification suite",
                ),
                technical_approach=(
                    "Python", "FastAPI", "Scikit-learn", "LiteLLM",
                ),
                feasibility_notes="High feasibility. Can be prototyped with local open models.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="domain_generalization",
        trigger_terms=frozenset({
            "generalization", "generalize", "domain", "transfer", "transferability",
            "out-of-distribution", "ood", "unseen", "cross-domain",
        }),
        directions=(
            ProposalDirection(
                title="Cross-Domain Robustness and Adaptation Testbed",
                summary=(
                    "A testing and adaptation framework evaluating model robustness and out-of-distribution "
                    "transfer across distinct target domains."
                ),
                problem_statement=(
                    "Models perform poorly when exposed to distribution shifts and domain differences "
                    "between training and operational data."
                ),
                objectives=(
                    "Evaluate performance drop across 4+ out-of-distribution domain datasets.",
                    "Implement domain-adversarial representation alignment.",
                    "Quantify correlation between representation distance and performance degradation.",
                ),
                proposed_methods=(
                    "Maximum Mean Discrepancy (MMD) minimization",
                    "Domain-adversarial neural networks (DANN)",
                    "Covariate shift perturbation testing",
                ),
                expected_outcomes=(
                    "Cross-domain robustness evaluation benchmark",
                    "Domain-invariant representation module",
                ),
                key_features=(
                    "Automated domain distance metric logger",
                    "Adversarial feature aligner",
                    "Generalization gap visualizer",
                ),
                technical_approach=(
                    "Python", "PyTorch", "DomainBed", "Torchvision / Hugging Face",
                ),
                feasibility_notes="High feasibility. Utilizes established cross-domain academic benchmark sets.",
            ),
            ProposalDirection(
                title="Test-Time Adaptation and Invariant Representation Toolkit",
                summary=(
                    "A toolkit enabling models to adapt dynamically to test-time distribution shifts "
                    "without requiring ground-truth labels."
                ),
                problem_statement=(
                    "Unlabeled test samples exhibit unseen stylistic or environmental shifts, degrading accuracy."
                ),
                objectives=(
                    "Implement test-time entropy minimization (TENT).",
                    "Stabilize normalization statistics on streaming test batches.",
                ),
                proposed_methods=(
                    "Entropy minimization",
                    "Batch-norm statistics adaptation",
                    "Contrastive pseudo-labeling",
                ),
                expected_outcomes=(
                    "Test-time adaptation pipeline",
                    "Adaptation stability verification suite",
                ),
                key_features=(
                    "Streaming batch adapter",
                    "Model drift prevention safeguard",
                    "Real-time accuracy recovery monitor",
                ),
                technical_approach=(
                    "Python", "PyTorch", "TorchAdaptive", "Scikit-learn",
                ),
                feasibility_notes="High feasibility. Operates purely during inference.",
            ),
            ProposalDirection(
                title="Domain Shift Stress-Testing and Calibration Suite",
                summary=(
                    "A systematic stress-testing suite subjecting models to synthetic corruptions, "
                    "stylistic shifts, and calibration assessments."
                ),
                problem_statement=(
                    "Models frequently exhibit overconfidence under severe domain shift without detection."
                ),
                objectives=(
                    "Measure Expected Calibration Error (ECE) under escalating distribution shifts.",
                    "Evaluate temperature scaling and Platt scaling calibration methods.",
                ),
                proposed_methods=(
                    "Image/text corruption libraries",
                    "Reliability diagram generation",
                    "Post-hoc uncertainty calibration",
                ),
                expected_outcomes=(
                    "Calibration and stress-testing toolkit",
                    "Out-of-distribution reliability dashboard",
                ),
                key_features=(
                    "Perturbation generator",
                    "Reliability and confidence curve plotter",
                    "Failure case clusterer",
                ),
                technical_approach=(
                    "Python", "Uncertainty Toolbox", "PyTorch", "Matplotlib",
                ),
                feasibility_notes="High feasibility. Straightforward post-processing evaluation.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="hallucination_mitigation",
        trigger_terms=frozenset({
            "hallucination", "hallucinations", "factuality", "factual",
            "faithfulness", "grounding", "confabulation",
        }),
        directions=(
            ProposalDirection(
                title="Retrieval-Grounded Factuality Verification Engine",
                summary=(
                    "An evidence-grounded verification system that validates generated assertions "
                    "against authoritative external passages with citation attribution."
                ),
                problem_statement=(
                    "Generative models hallucinate plausible but ungrounded claims, eroding user trust."
                ),
                objectives=(
                    "Extract atomic factual claims from generated output.",
                    "Retrieve supporting evidence passages and verify claim entailment.",
                    "Assign fine-grained evidence attribution scores.",
                ),
                proposed_methods=(
                    "Atomic claim decomposition",
                    "Dense passage retrieval",
                    "Natural Language Inference (NLI) verification",
                ),
                expected_outcomes=(
                    "Claim-level factuality auditing pipeline",
                    "Evidence-attribution reporting engine",
                ),
                key_features=(
                    "Atomic statement splitter",
                    "NLI entailment classifier",
                    "Citation grounding visualizer",
                ),
                technical_approach=(
                    "Python", "spaCy", "Transformers", "FAISS", "FastAPI",
                ),
                feasibility_notes="High feasibility. Can leverage open NLI and dense retrieval models.",
            ),
            ProposalDirection(
                title="Citation-Enforced Decoding and Self-Consistency Checker",
                summary=(
                    "A constrained decoding and consistency validation framework ensuring every output sentence "
                    "is strictly anchored in retrieved source documents."
                ),
                problem_statement=(
                    "Unconstrained language generation deviates from reference documents during long answers."
                ),
                objectives=(
                    "Enforce citation token constraints during sequence generation.",
                    "Compute multi-sample self-consistency consensus scores.",
                ),
                proposed_methods=(
                    "Constrained beam search",
                    "Self-consistency majority voting",
                    "Token-level grounding attribution",
                ),
                expected_outcomes=(
                    "Constrained citation decoding library",
                    "Consistency scoring harness",
                ),
                key_features=(
                    "Grammar-constrained decoder",
                    "Sample agreement matrix",
                    "Hallucination probability heatmap",
                ),
                technical_approach=(
                    "Python", "vLLM", "Guidance / Outlines", "PyTorch",
                ),
                feasibility_notes="High feasibility using open language models.",
            ),
            ProposalDirection(
                title="Automated Hallucination Detection and Benchmark Suite",
                summary=(
                    "A benchmark platform containing curated adversarial queries designed to stress-test "
                    "model hallucination rates across diverse tasks."
                ),
                problem_statement=(
                    "Evaluating hallucination requires comprehensive testbeds with verified factual ground truth."
                ),
                objectives=(
                    "Curate a test suite of counterfactual and unanswerable questions.",
                    "Evaluate hallucination frequency across different model architectures.",
                ),
                proposed_methods=(
                    "Adversarial prompt crafting",
                    "Automated contradiction checking",
                    "Ground truth comparison metrics",
                ),
                expected_outcomes=(
                    "Open hallucination benchmarking dataset",
                    "Automated hallucination scoring harness",
                ),
                key_features=(
                    "Trap question catalog",
                    "Automated fact-checking evaluator",
                    "Model hallucination comparison leaderboard",
                ),
                technical_approach=(
                    "Python", "Datasets", "Pandas", "Streamlit",
                ),
                feasibility_notes="High feasibility. Pure evaluation framework.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="bias_fairness",
        trigger_terms=frozenset({
            "bias", "biases", "demographic", "diversity", "representation",
            "fairness", "skew", "skewed",
        }),
        directions=(
            ProposalDirection(
                title="Algorithmic Debiasing and Balanced Evaluation Platform",
                summary=(
                    "A fairness evaluation suite and reweighting toolkit to audit and mitigate "
                    "representation disparities across demographic groups."
                ),
                problem_statement=(
                    "Training data skews perpetuate unfair performance disparities and stereotypes in predictions."
                ),
                objectives=(
                    "Audit disparate impact and equalized odds across demographic subgroups.",
                    "Implement fairness-regularized loss objectives and sample reweighting.",
                ),
                proposed_methods=(
                    "Disparate impact calculation",
                    "Adversarial debiasing",
                    "Importance reweighting",
                ),
                expected_outcomes=(
                    "Demographic parity audit framework",
                    "Debiased model checkpoints",
                ),
                key_features=(
                    "Subgroup disparity visualizer",
                    "Fairness-accuracy tradeoff curve generator",
                    "Automated bias metric logger",
                ),
                technical_approach=(
                    "Python", "Fairlearn", "AIF360", "PyTorch",
                ),
                feasibility_notes="High feasibility with open demographic fairness datasets.",
            ),
            ProposalDirection(
                title="Counterfactual Data Perturbation and Bias Auditing Suite",
                summary=(
                    "An auditing suite perturbing demographic attributes in test instances to measure "
                    "individual fairness and decision invariance."
                ),
                problem_statement=(
                    "Models produce conflicting decisions when names or protected attributes are swapped."
                ),
                objectives=(
                    "Generate paired counterfactual test instances via name and pronoun substitution.",
                    "Quantify model flip rates and individual fairness violations.",
                ),
                proposed_methods=(
                    "Named entity swapping",
                    "Counterfactual logit divergence measurement",
                    "Robustness score aggregation",
                ),
                expected_outcomes=(
                    "Counterfactual perturbation test generator",
                    "Model sensitivity report",
                ),
                key_features=(
                    "Attribute replacement dictionary",
                    "Decision flip rate analyzer",
                    "Interactive bias audit report",
                ),
                technical_approach=(
                    "Python", "spaCy", "CheckList", "Streamlit",
                ),
                feasibility_notes="High feasibility. Inference-only auditing.",
            ),
            ProposalDirection(
                title="Inclusive Curation and Demographic Parity Dashboard",
                summary=(
                    "A dataset curation assistance dashboard identifying underrepresented clusters "
                    "and recommending targeted data collection."
                ),
                problem_statement=(
                    "Practitioners lack visibility into dataset representation imbalances before training."
                ),
                objectives=(
                    "Cluster training data to surface underrepresented demographic intersections.",
                    "Recommend optimal synthetic or real data balancing quotas.",
                ),
                proposed_methods=(
                    "Unsupervised density estimation",
                    "Representation parity scoring",
                    "Interactive curation recommendations",
                ),
                expected_outcomes=(
                    "Dataset diversity auditing tool",
                    "Data balancing guideline generator",
                ),
                key_features=(
                    "Representation distribution charts",
                    "Underrepresented cluster highlighter",
                    "Data balancing export utility",
                ),
                technical_approach=(
                    "Python", "FastAPI", "UMAP / t-SNE", "React / Plotly",
                ),
                feasibility_notes="High feasibility. Pre-training analysis tool.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="interpretability",
        trigger_terms=frozenset({
            "interpretability", "explainability", "black-box", "transparency",
            "interpretable", "explainable", "attribution",
        }),
        directions=(
            ProposalDirection(
                title="Mechanistic Interpretability and Attribution Dashboard",
                summary=(
                    "An interactive visualization and inspection tool for attention heads, "
                    "neuron activations, and gradient-based concept attributions."
                ),
                problem_statement=(
                    "Deep learning models function as opaque black boxes, preventing users from validating reasoning."
                ),
                objectives=(
                    "Extract Integrated Gradients and attention rollout scores.",
                    "Visualize circuit activations for specific linguistic features.",
                ),
                proposed_methods=(
                    "Integrated gradients",
                    "Attention rollout tracking",
                    "Neuron activation patching",
                ),
                expected_outcomes=(
                    "Interactive interpretability dashboard",
                    "Model explanation export API",
                ),
                key_features=(
                    "Attention heatmap viewer",
                    "Token attribution highlighter",
                    "Neuron activation probe explorer",
                ),
                technical_approach=(
                    "Python", "Captum", "TransformerLens", "Streamlit",
                ),
                feasibility_notes="High feasibility using open pre-trained Transformer models.",
            ),
            ProposalDirection(
                title="Concept Bottleneck and Post-Hoc Rationalization Engine",
                summary=(
                    "An architecture framework constraining intermediate representations to human-understandable "
                    "concepts before predicting outcomes."
                ),
                problem_statement=(
                    "Post-hoc explanations can be unfaithful to the model's actual computational decision path."
                ),
                objectives=(
                    "Train explicit concept predictor layers.",
                    "Provide human-interpretable reasoning chains alongside predictions.",
                ),
                proposed_methods=(
                    "Concept bottleneck architectures",
                    "Faithfulness metric evaluation",
                    "Counterfactual concept intervention",
                ),
                expected_outcomes=(
                    "Concept bottleneck model implementation",
                    "Explanation faithfulness benchmark",
                ),
                key_features=(
                    "Concept intervention panel",
                    "Explanation faithfulness score calculator",
                    "Decision tree surrogate visualizer",
                ),
                technical_approach=(
                    "Python", "PyTorch", "Scikit-learn", "Matplotlib",
                ),
                feasibility_notes="High feasibility on standard classification tasks.",
            ),
            ProposalDirection(
                title="Feature Attribution Verification and Faithfulness Harness",
                summary=(
                    "An evaluation harness testing the true faithfulness of explainability algorithms "
                    "against feature removal and sanity checks."
                ),
                problem_statement=(
                    "Explainability methods often produce plausible visual maps that fail basic sanity checks."
                ),
                objectives=(
                    "Subject attribution methods to model parameter randomization tests.",
                    "Evaluate faithfulness via progressive feature erasure (comprehensiveness and sufficiency).",
                ),
                proposed_methods=(
                    "Pixel/token erasure ablation",
                    "Sanity check randomization",
                    "Area Under the Precision-Recall Perturbation Curve",
                ),
                expected_outcomes=(
                    "Faithfulness benchmarking suite",
                    "Comparative explainability audit report",
                ),
                key_features=(
                    "Progressive feature ablator",
                    "Randomization sanity check runner",
                    "Faithfulness leaderboard",
                ),
                technical_approach=(
                    "Python", "Captum", "PyTorch", "SciPy",
                ),
                feasibility_notes="High feasibility. Strictly empirical evaluation.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="annotation_efficiency",
        trigger_terms=frozenset({
            "annotation", "labeling", "annotators", "human feedback", "rlhf", "curation",
            "active learning", "weak supervision", "supervision", "pseudo-labeling",
        }),
        directions=(
            ProposalDirection(
                title="Weak Supervision and Programmatic Labeling Framework",
                summary=(
                    "A programmatic labeling system combining noisy heuristics, pattern matching, "
                    "and small generative models to synthesize training annotations."
                ),
                problem_statement=(
                    "Manual gold-standard annotation is too slow and expensive for domain-specific projects."
                ),
                objectives=(
                    "Encode domain rules into programmatic labeling functions.",
                    "Combine noisy labels using a generative label aggregator model.",
                ),
                proposed_methods=(
                    "Snorkel label aggregation",
                    "Keyword and regex heuristic modeling",
                    "Uncertainty-aware label smoothing",
                ),
                expected_outcomes=(
                    "Programmatic weak labeling pipeline",
                    "Synthetic label quality assessment report",
                ),
                key_features=(
                    "Labeling function IDE interface",
                    "Label conflict and coverage matrix",
                    "Downstream classifier training bridge",
                ),
                technical_approach=(
                    "Python", "Snorkel", "FastAPI", "PyTorch",
                ),
                feasibility_notes="High feasibility. Substantially reduces human labeling needs.",
            ),
            ProposalDirection(
                title="Human-in-the-Loop Active Curation Studio",
                summary=(
                    "An intelligent annotation workspace prioritizing boundary cases and model uncertainty "
                    "to maximize labeler utility."
                ),
                problem_statement=(
                    "Human annotators waste effort labeling redundant, high-confidence samples."
                ),
                objectives=(
                    "Route high-uncertainty instances to annotators.",
                    "Continuously fine-tune lightweight model adapters as new labels arrive.",
                ),
                proposed_methods=(
                    "Active learning uncertainty sampling",
                    "Online model adaptation",
                    "Inter-annotator agreement tracking",
                ),
                expected_outcomes=(
                    "Human-in-the-loop annotation tool",
                    "Annotation efficiency metric report",
                ),
                key_features=(
                    "Interactive labeling interface",
                    "Confidence threshold router",
                    "Real-time adapter update loop",
                ),
                technical_approach=(
                    "Python", "Label Studio API", "FastAPI", "React",
                ),
                feasibility_notes="High feasibility. Integrates with standard labeling tools.",
            ),
            ProposalDirection(
                title="Self-Training and Pseudo-Label Filtering Suite",
                summary=(
                    "A self-training pipeline filtering pseudo-labels on unlabeled data via confidence "
                    "calibration and consistency regularization."
                ),
                problem_statement=(
                    "Naive pseudo-labeling introduces confirmation bias and noisy labels into models."
                ),
                objectives=(
                    "Filter pseudo-labels with thresholded confidence and semantic consistency.",
                    "Iteratively expand the training pool without drift.",
                ),
                proposed_methods=(
                    "Consistency regularization",
                    "Dynamic thresholding (FreeMatch)",
                    "Data purification filtering",
                ),
                expected_outcomes=(
                    "Robust self-training engine",
                    "Pseudo-label error mitigation study",
                ),
                key_features=(
                    "Dynamic threshold calculator",
                    "Pseudo-label drift detector",
                    "Curriculum sample promoter",
                ),
                technical_approach=(
                    "Python", "PyTorch", "USB (Unified Semi-supervised Benchmark)",
                ),
                feasibility_notes="High feasibility. Evaluated on benchmark semi-supervised tasks.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="evaluation_frameworks",
        trigger_terms=frozenset({
            "benchmark", "benchmarks", "metric", "metrics", "testbed",
            "ground truth", "evaluation", "synthetic benchmarks", "narrow evaluation",
        }),
        directions=(
            ProposalDirection(
                title="Dynamic Stress-Testing and Real-World Evaluation Framework",
                summary=(
                    "A holistic evaluation framework challenging models beyond static synthetic testbeds "
                    "with real-world adversarial perturbations and distribution shifts."
                ),
                problem_statement=(
                    "Static academic benchmarks fail to reflect complex, noisy real-world deployments."
                ),
                objectives=(
                    "Construct dynamic stress tests covering linguistic noise, formatting anomalies, and typos.",
                    "Evaluate model resilience beyond standard accuracy metrics.",
                ),
                proposed_methods=(
                    "Adversarial input perturbation",
                    "Holistic robustness scoring",
                    "Task decomposition testing",
                ),
                expected_outcomes=(
                    "Dynamic stress-testing library",
                    "Real-world robustness benchmarking report",
                ),
                key_features=(
                    "Perturbation injection engine",
                    "Multi-dimensional scorecard visualizer",
                    "Automated regression testing hook",
                ),
                technical_approach=(
                    "Python", "TextAttack", "CheckList", "Pytest",
                ),
                feasibility_notes="High feasibility. Pure evaluation framework with zero training compute.",
            ),
            ProposalDirection(
                title="Ecological Validity Profiler for Academic Benchmarks",
                summary=(
                    "An auditing tool quantifying the semantic gap between popular academic datasets "
                    "and practical industry production queries."
                ),
                problem_statement=(
                    "Academic datasets often rely on synthetic templates that oversimplify practical nuances."
                ),
                objectives=(
                    "Compare linguistic complexity and vocabulary distribution between datasets.",
                    "Provide an ecological validity index for academic benchmarks.",
                ),
                proposed_methods=(
                    "Corpus lexical diversity measurement",
                    "Sentence structure complexity profiling",
                    "Embedding space distribution overlap scoring",
                ),
                expected_outcomes=(
                    "Ecological validity auditing tool",
                    "Dataset alignment report",
                ),
                key_features=(
                    "Lexical diversity analyzer",
                    "Dataset distribution divergence meter",
                    "Validity score summary generator",
                ),
                technical_approach=(
                    "Python", "spaCy", "Scikit-learn", "Matplotlib",
                ),
                feasibility_notes="High feasibility. Post-hoc text analytics.",
            ),
            ProposalDirection(
                title="Continuous Automated Evaluation and Regression Harness",
                summary=(
                    "A CI/CD evaluation pipeline that automatically assesses model updates against a "
                    "fixed evaluation battery to prevent silent capability regressions."
                ),
                problem_statement=(
                    "Model fine-tuning frequently introduces unintended capability degradations in other tasks."
                ),
                objectives=(
                    "Implement automated pull-request evaluation triggers.",
                    "Track capability regression across 10+ standard tasks.",
                ),
                proposed_methods=(
                    "CI/CD workflow integration",
                    "Automated regression alerting",
                    "Cost-controlled subset sampling",
                ),
                expected_outcomes=(
                    "Automated evaluation pipeline",
                    "Model release qualification dashboard",
                ),
                key_features=(
                    "GitHub Actions CI/CD integration",
                    "Regression delta visualizer",
                    "Automated model acceptance gate",
                ),
                technical_approach=(
                    "Python", "GitHub Actions", "FastAPI", "SQLite",
                ),
                feasibility_notes="High feasibility. Focuses on software engineering automation.",
            ),
        ),
    ),
    DomainBlueprint(
        domain_id="sensitivity_robustness",
        trigger_terms=frozenset({
            "hyperparameter", "hyperparameters", "prompt", "prompting", "noise",
            "perturbation", "perturbations", "stability", "brittle", "sensitivity",
        }),
        directions=(
            ProposalDirection(
                title="Robust Optimization and Prompt Perturbation Suite",
                summary=(
                    "An evaluation and training toolkit to quantify and mitigate model sensitivity "
                    "to input prompt phrasing and parameter perturbations."
                ),
                problem_statement=(
                    "Models display brittle performance variance when prompts or hyperparameters change slightly."
                ),
                objectives=(
                    "Measure output variance across 20+ semantically equivalent prompt paraphrases.",
                    "Implement Sharpness-Aware Minimization (SAM) to improve parameter stability.",
                ),
                proposed_methods=(
                    "Automated prompt paraphrasing",
                    "Variance quantification metrics",
                    "Sharpness-aware optimization",
                ),
                expected_outcomes=(
                    "Prompt sensitivity auditing tool",
                    "Robust training optimization recipes",
                ),
                key_features=(
                    "Prompt mutation generator",
                    "Variance confidence intervals",
                    "Optimization stability plots",
                ),
                technical_approach=(
                    "Python", "PyTorch", "TextAttack", "Transformers",
                ),
                feasibility_notes="High feasibility. Evaluates stability directly.",
            ),
            ProposalDirection(
                title="Ensemble Distillation and Noise-Resilient Training Engine",
                summary=(
                    "A training engine distilling diverse prompt variations into a single noise-resilient "
                    "model that resists superficial phrasing shifts."
                ),
                problem_statement=(
                    "Single-prompt models overfit to specific syntactic patterns."
                ),
                objectives=(
                    "Train models on diversified prompt ensembles.",
                    "Reduce variance under prompt mutations by at least 50%.",
                ),
                proposed_methods=(
                    "Multi-prompt distillation",
                    "Adversarial input noise injection",
                    "Consistency regularization",
                ),
                expected_outcomes=(
                    "Noise-resilient model checkpoints",
                    "Multi-prompt training framework",
                ),
                key_features=(
                    "Prompt ensemble generator",
                    "Noise injection scheduler",
                    "Robustness verification benchmark",
                ),
                technical_approach=(
                    "Python", "PyTorch", "Hugging Face",
                ),
                feasibility_notes="Moderate feasibility. Requires multi-pass training.",
            ),
            ProposalDirection(
                title="Prompt Brittleness Profiler and Automated Stabilizer",
                summary=(
                    "A prompt engineering profiler that diagnoses brittle instructions and automatically "
                    "generates stabilized, robust prompt variants."
                ),
                problem_statement=(
                    "Developers struggle to identify which words in a prompt cause unpredictable failures."
                ),
                objectives=(
                    "Identify high-sensitivity tokens in prompt templates.",
                    "Automatically suggest stabilized phrasing with minimal variance.",
                ),
                proposed_methods=(
                    "Token ablation sensitivity testing",
                    "Automated prompt rewriting heuristics",
                    "Consistency scoring",
                ),
                expected_outcomes=(
                    "Prompt stabilization CLI utility",
                    "Interactive prompt sensitivity report",
                ),
                key_features=(
                    "Word-level sensitivity highlighting",
                    "Stabilized prompt candidate generator",
                    "Consistency benchmark runner",
                ),
                technical_approach=(
                    "Python", "FastAPI", "Click / CLI", "Streamlit",
                ),
                feasibility_notes="High feasibility. Pure inference-time prompt diagnostic.",
            ),
        ),
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_tokens(text: str) -> set[str]:
    """Extract lowercase alphanumeric tokens, splitting on punctuation and hyphens."""
    cleaned = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
    tokens = set(cleaned.split())
    for raw in re.findall(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b", text.lower()):
        tokens.add(raw)
    return tokens


def _clean_title(text: str) -> str:
    """Format raw text into Title Case words."""
    cleaned = re.sub(r"[^\w\s-]", " ", text)
    return " ".join(w.capitalize() for w in cleaned.split())


def _match_domain_blueprint(opp_title: str, opp_desc: str, keywords: list[str]) -> DomainBlueprint | None:
    """Find the best matching domain blueprint for an opportunity."""
    combined_text = f"{opp_title} {opp_desc} {' '.join(keywords)}".lower()
    tokens = _extract_tokens(combined_text)

    best_match: DomainBlueprint | None = None
    max_score = 0

    for blueprint in DOMAIN_BLUEPRINTS:
        overlap = len(tokens.intersection(blueprint.trigger_terms))
        phrase_matches = sum(1 for term in blueprint.trigger_terms if " " in term and term in combined_text)
        total_score = overlap + (phrase_matches * 2)

        if total_score > max_score and (total_score >= 2 or overlap >= 1):
            max_score = total_score
            best_match = blueprint

    return best_match


def _generate_generic_direction(opp_title: str, opp_desc: str, index: int) -> ProposalDirection:
    """Generate a grounded, distinct generic direction for unmapped opportunities."""
    clean = _clean_title(opp_title)
    if index == 0:
        return ProposalDirection(
            title=f"{clean} Implementation and Validation Framework",
            summary=f"A structured software and experimental framework designed to implement: {opp_title}.",
            problem_statement=f"The project directly addresses the challenge: '{opp_desc}'.",
            objectives=(
                f"Design and implement a modular software architecture addressing '{opp_title}'.",
                "Construct reproducible experimental pipelines with baseline comparisons.",
                "Quantify empirical performance metrics and system trade-offs.",
            ),
            proposed_methods=(
                "Modular architecture design",
                "Empirical validation harness",
                "Comparative baseline benchmarking",
            ),
            expected_outcomes=(
                "Open-source implementation framework",
                "Empirical evaluation report and reproducible codebase",
            ),
            key_features=(
                "Modular pipeline interface",
                "Automated validation testbed",
                "Metric telemetry logger",
            ),
            technical_approach=("Python", "PyTorch / Scikit-learn", "FastAPI"),
            feasibility_notes="High feasibility. Directly implements and evaluates the proposed opportunity.",
        )
    elif index == 1:
        return ProposalDirection(
            title=f"{clean} Comparative Benchmark Platform",
            summary=f"A standardized empirical benchmark platform evaluating diverse approaches to {opp_title}.",
            problem_statement=f"Lack of unified benchmarking protocols hinders comparative progress on: '{opp_desc}'.",
            objectives=(
                f"Establish unified evaluation metrics and test datasets for '{opp_title}'.",
                "Benchmark 3+ baseline techniques under standardized experimental conditions.",
            ),
            proposed_methods=(
                "Standardized dataset curation",
                "Automated metric calculation",
                "Pareto trade-off profiling",
            ),
            expected_outcomes=(
                "Public benchmarking suite",
                "Comparative evaluation leaderboard",
            ),
            key_features=(
                "Automated benchmark runner",
                "Result comparison visualizer",
                "Standardized evaluation harness",
            ),
            technical_approach=("Python", "Pandas", "Matplotlib", "Streamlit"),
            feasibility_notes="High feasibility. Pure evaluation framework.",
        )
    else:
        return ProposalDirection(
            title=f"{clean} Optimization and Deployment Pipeline",
            summary=f"An engineering pipeline providing automated optimization and tuning for {opp_title}.",
            problem_statement=f"Engineering and adaptation barriers restrict practical deployment of: '{opp_desc}'.",
            objectives=(
                f"Implement automated hyperparameter and architectural tuning for '{opp_title}'.",
                "Demonstrate improved efficiency and practical deployability.",
            ),
            proposed_methods=(
                "Automated configuration search",
                "Resource consumption profiling",
                "Lightweight deployment packaging",
            ),
            expected_outcomes=(
                "Optimized deployment-ready artifact",
                "Configuration tuning guide",
            ),
            key_features=(
                "Hyperparameter search engine",
                "Resource profiling monitor",
                "Containerized deployment recipe",
            ),
            technical_approach=("Python", "Optuna", "Docker", "PyTorch"),
            feasibility_notes="High feasibility. Focuses on practical tuning and optimization.",
        )


# ---------------------------------------------------------------------------
# Public Proposal Generation Entry Point
# ---------------------------------------------------------------------------

def generate_project_proposals(
    opportunities: list[ResearchOpportunity],
) -> list[ProjectProposal]:
    """Generate buildable project proposals from research opportunities.

    Parameters
    ----------
    opportunities:
        Potential research opportunities identified by M4.

    Returns
    -------
    list[ProjectProposal]
        Between ``MIN_PROPOSALS`` (3) and ``MAX_PROPOSALS`` (5) actionable
        project proposals directly grounded in the input opportunities.
        If no valid opportunities are supplied, returns ``[]``.
    """
    if not opportunities:
        return []

    # Extract valid opportunity records
    valid_opps: list[dict[str, Any]] = []
    for idx, opp in enumerate(opportunities):
        if opp is None:
            continue

        opp_id = getattr(opp, "opportunity_id", None) or getattr(opp, "id", None)
        if isinstance(opp, dict):
            opp_id = opp.get("opportunity_id") or opp.get("id")
            title = str(opp.get("title") or "").strip()
            desc = str(opp.get("description") or "").strip()
            keywords = list(opp.get("keywords") or [])
            paper_ids = list(opp.get("paper_ids") or [])
            evidence = list(opp.get("evidence") or [])
        else:
            title = str(getattr(opp, "title", "") or "").strip()
            desc = str(getattr(opp, "description", "") or "").strip()
            keywords = list(getattr(opp, "keywords", []) or [])
            paper_ids = list(getattr(opp, "paper_ids", []) or [])
            evidence = list(getattr(opp, "evidence", []) or [])

        if not opp_id:
            opp_id = f"opp_{idx + 1}"
        else:
            opp_id = str(opp_id)

        if not title:
            continue

        valid_opps.append({
            "opp_id": opp_id,
            "title": title,
            "description": desc,
            "keywords": keywords,
            "paper_ids": paper_ids,
            "evidence": evidence,
        })

    if not valid_opps:
        return []

    # Sort opportunities deterministically: most supporting papers first, then title
    valid_opps.sort(key=lambda o: (-len(o["paper_ids"]), o["title"]))

    # Collect proposed directions
    proposals: list[ProjectProposal] = []
    seen_titles: set[str] = set()

    # Determine distribution across opportunities to satisfy 3–5 proposals
    # without fabricating unrelated topics
    num_opps = len(valid_opps)

    # Calculate how many directions to extract per opportunity
    opp_direction_indices: list[tuple[dict[str, Any], int]] = []

    if num_opps == 1:
        # Generate 3 distinct directions from the single opportunity
        opp = valid_opps[0]
        opp_direction_indices = [(opp, 0), (opp, 1), (opp, 2)]
    elif num_opps == 2:
        # Generate 2 directions from primary opp and 1 from secondary opp (total 3)
        opp_direction_indices = [
            (valid_opps[0], 0),
            (valid_opps[1], 0),
            (valid_opps[0], 1),
        ]
    elif num_opps <= MAX_PROPOSALS:
        # 3, 4, or 5 opportunities: take the primary direction from each
        opp_direction_indices = [(opp, 0) for opp in valid_opps[:MAX_PROPOSALS]]
    else:
        # More than 5 opportunities: clamp to top 5
        opp_direction_indices = [(opp, 0) for opp in valid_opps[:MAX_PROPOSALS]]

    for opp, dir_idx in opp_direction_indices:
        blueprint = _match_domain_blueprint(
            opp_title=opp["title"],
            opp_desc=opp["description"],
            keywords=opp["keywords"],
        )

        if blueprint is not None:
            # Wrap dir_idx if exceeds available directions
            direction = blueprint.directions[dir_idx % len(blueprint.directions)]
        else:
            direction = _generate_generic_direction(
                opp_title=opp["title"],
                opp_desc=opp["description"],
                index=dir_idx,
            )

        if direction.title in seen_titles:
            # If title collision occurs, try fallback direction
            direction = _generate_generic_direction(
                opp_title=f"{opp['title']} (Variant {dir_idx + 1})",
                opp_desc=opp["description"],
                index=dir_idx,
            )

        seen_titles.add(direction.title)

        # Deterministic UUID5 based on title and source opportunity ID
        proposal_id = uuid5(NAMESPACE_DNS, f"proposal:{direction.title}:{opp['opp_id']}").hex

        proposals.append(
            ProjectProposal(
                proposal_id=proposal_id,
                title=direction.title,
                summary=direction.summary,
                problem_statement=direction.problem_statement,
                source_opportunity_ids=[opp["opp_id"]],
                objectives=list(direction.objectives),
                proposed_methods=list(direction.proposed_methods),
                expected_outcomes=list(direction.expected_outcomes),
                key_features=list(direction.key_features),
                technical_approach=list(direction.technical_approach),
                feasibility_notes=direction.feasibility_notes,
                paper_ids=list(opp["paper_ids"]),
                evidence=list(opp["evidence"]),
                novelty_confidence="Requires human validation",
            )
        )

    # Sort proposals deterministically by supporting papers descending, then title ascending
    proposals.sort(key=lambda p: (-len(p.paper_ids), p.title))

    return proposals
