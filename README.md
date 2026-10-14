# MLemons — Agro-Industrial Quality Control & MLOps Platform on AWS

[![Domain](https://img.shields.io/badge/Domain-AgTech%20%7C%20Computer%20Vision-2E7D32?logo=leaf&logoColor=white)](#business-problem--industry-context)
[![Accuracy](https://img.shields.io/badge/Model%20Accuracy-97.76%25-brightgreen)](https://aws.amazon.com/sagemaker/)
[![Batch Latency](https://img.shields.io/badge/E2E%20Latency-2.48s%20%2F%20batch-blue)](#architecture--data-flow)
[![AWS SageMaker](https://img.shields.io/badge/Inference-AWS%20SageMaker-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/sagemaker/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-844FBA?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![AWS Step Functions](https://img.shields.io/badge/Orchestration-Step%20Functions-FF4F8B?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/step-functions/)
[![Amazon DynamoDB](https://img.shields.io/badge/Audit%20Log-DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![DVC](https://img.shields.io/badge/Data%20Lineage-DVC-945DD6?logo=dvc&logoColor=white)](https://dvc.org/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)

An automated, cloud-native Machine Learning Operations (MLOps) platform designed to solve one of the most expensive operational challenges in post-harvest agriculture: **real-time visual defect detection, quality grading, and digital compliance auditing for fresh produce export lines**.

Built on **Amazon Web Services (AWS)** using **Terraform (IaC)**, the platform combines computer vision deep learning with serverless distributed orchestration to eliminate subjective manual inspection, prevent costly container shipment rejections, and enforce immutable traceability.

---

## 🌾 Business Problem & Industry Context

In commercial citrus packaging and export facilities, fruit sorting has traditionally relied on manual human inspection along conveyor lines. This operational model introduces critical failure modes:

| Manual Sorting Pain Point | Real-World Business Consequence | MLemons Solution |
| :--- | :--- | :--- |
| **Subjective Inspection Standards** | Inconsistencies between operators, shifts, and facilities cause disputed quality grades upon arrival at destination ports. | **Deterministic Deep Learning:** Standardized classification benchmarked at **97.76% accuracy**. |
| **Throughput Bottlenecks** | Human operators can only inspect 2–3 fruits per second, capping packaging line speeds. | **High-Throughput Parallel Inference:** Scalable real-time batch evaluations running in **2.48 seconds**. |
| **Worker Fatigue & False Negatives** | Prolonged shifts degrade human accuracy, allowing pest-damaged or decaying fruit to contaminate entire export pallets. | **Zero Fatigue Degradation:** 24/7 consistency across shifts with automated defect scoring thresholds. |
| **Zero Traceability & Data Capture** | Manual sorting generates no digital audit logs; quality disputes with supermarket distributors result in heavy financial penalties. | **Immutable Cloud Ledger:** Every batch transaction, quality score, and classification timestamp is persisted in **Amazon DynamoDB**. |

---

## 🎯 Key Engineering & Business Results

* **97.76% Test Accuracy:** MobileNetV2 transfer learning trained on 2,690 high-resolution images across diverse defect classes (skin blemish, black spot, mold, decay, under-ripe).
* **2.48s End-to-End Batch Ingestion & Scoring:** Orchestrated via **AWS Step Functions** and serverless **AWS Lambda** handlers, evaluating multi-image batches and returning definitive pass/fail decisions.
* **100% Cloud Traceability:** Complete inspection audit trail persisted in **Amazon DynamoDB** with raw image payloads indexed in **Amazon S3** for compliance audits.
* **28 Managed Cloud Resources via Terraform:** Full Infrastructure as Code covering S3 buckets, IAM least-privilege roles, DynamoDB tables, Lambda functions, Step Functions, CloudWatch alarms, and SageMaker model endpoints.
* **Rigorous Data & Model Lineage:** Versioned training data and model checkpoints managed via **DVC (Data Version Control)** with S3 remote storage and **MLflow** experiment tracking.
* **Automated CI/CD Quality Gates:** 19 unit and integration tests executed on every push via **GitHub Actions** with 100% coverage on serverless business logic.

---

## 🏗️ Architecture & Data Flow

```
                      [ Harvest / Batch Image Upload ]
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │    Amazon S3 (Raw Store)     │
                      └──────────────┬───────────────┘
                                     │
                                     ▼
         ┌────────────────────────────────────────────────────────┐
         │            AWS Step Functions State Machine            │
         │                                                        │
         │   ┌────────────────────────────────────────────────┐   │
         │   │ 1. Lambda: invoke_modelo_a                     │   │
         │   │    - Fetches image from S3                     │   │
         │   │    - Preprocesses input tensor (transforms)    │   │
         │   │    - Invokes SageMaker Real-Time Endpoint      │   │
         │   └───────────────────────┬────────────────────────┘   │
         │                           │                            │
         │                           ▼                            │
         │                  ┌──────────────────┐                  │
         │                  │ AWS SageMaker EP │                  │
         │                  │  (MobileNetV2)   │                  │
         │                  └────────┬─────────┘                  │
         │                           │ (Class Probabilities)      │
         │                           ▼                            │
         │   ┌────────────────────────────────────────────────┐   │
         │   │ 2. Lambda: compute_score                       │   │
         │   │    - Evaluates defect tolerance thresholds     │   │
         │   │    - Computes batch score & decision           │   │
         │   │    - Dispatches operational CloudWatch metrics │   │
         │   └───────────────────────┬────────────────────────┘   │
         │                           │                            │
         └───────────────────────────┼────────────────────────────┘
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │       Amazon DynamoDB        │
                      │  (Immutable Inspection Log)  │
                      └──────────────────────────────┘
```

---

## 🛠️ Infrastructure & MLOps Lifecycle

### 1. Model Registry & Packaging
SageMaker training produces versioned model artifacts packaged with standalone inference handlers (`code/inference.py`), validated, and registered in the **SageMaker Model Registry** under an `Approved` status gate before rollout.

### 2. FinOps & Operational Cost Optimization
* **Serverless Pipeline:** Lambda functions and Step Functions incur $0 during conveyor downtime.
* **S3 Lifecycle Policies:** Raw inspection images automatically transition across storage classes or expire based on compliance retention windows.
* **Scheduled Inference Endpoints:** SageMaker endpoints can be provisioned or de-provisioned via single-command Terraform workflows aligned with factory shifts.

---

## 🚀 Execution & Deployment Guide

### Prerequisites
- Python 3.11
- AWS CLI v2 configured with active credentials
- Terraform >= 1.5
- DVC

### 1. Provision Infrastructure
```bash
make install                 # Set up Python virtual environment and dependencies
source .venv/bin/activate
make apply                   # Terraform provisions S3, IAM, DynamoDB, Lambdas, and Step Functions
```

### 2. Dataset Versioning & Model Training
```bash
# Push dataset to S3 storage via DVC
dvc push

# Trigger training job on SageMaker
python scripts/run_training.py

# Package inference code and register model in Model Registry
python scripts/repack_model.py
python scripts/register_model_package.py
```

### 3. Deploy Inference Endpoint
```bash
cd infra
terraform apply -var "model_package_arn=<APPROVED_MODEL_PACKAGE_ARN>"
```

### 4. End-to-End Verification & Demo
```bash
# Smoke test the live SageMaker endpoint with a test sample
python scripts/smoke_test_endpoint.py data/lemons/good_quality/good_quality_0.jpg

# Execute full automated test suite (19 unit/integration tests)
make test
```

---

## 🧪 Automated Testing & Validation

The codebase includes **19 automated test suites** executed via GitHub Actions CI:
* `test_scoring_logic.py` (9 tests): Validates mathematical scoring algorithms, tolerance boundaries, and edge-case classification decisions.
* `test_invoke_modelo_a.py` (5 tests): Tests Lambda invocation against mocked S3 and SageMaker runtime interfaces.
* `test_compute_score_handler.py` (5 tests): Verifies DynamoDB persistence logic and error recovery.

---

## 👨‍💻 Author
**Luis Alberto González Escamilla**  
Computer Systems Engineer | AI & Agent Engineer
