# MLemons — Production Computer Vision MLOps Pipeline on AWS

[![AWS SageMaker](https://img.shields.io/badge/AI%20Inference-AWS%20SageMaker-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/sagemaker/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-844FBA?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![AWS Step Functions](https://img.shields.io/badge/Orchestration-AWS%20Step%20Functions-FF4F8B?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/step-functions/)
[![AWS Lambda](https://img.shields.io/badge/Serverless-AWS%20Lambda-FF9900?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Amazon DynamoDB](https://img.shields.io/badge/Database-Amazon%20DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)](https://aws.amazon.com/dynamodb/)
[![PyTorch](https://img.shields.io/badge/Framework-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![DVC](https://img.shields.io/badge/Data%20Version%20Control-DVC-945DD6?logo=dvc&logoColor=white)](https://dvc.org/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)

An automated, end-to-end Machine Learning Operations (MLOps) pipeline for real-time computer vision quality inspection deployed on **Amazon Web Services (AWS)** using **Terraform (IaC)**.

The system automates the full lifecycle: dataset versioning via DVC, model transfer learning on **Amazon SageMaker**, automated packaging into the **SageMaker Model Registry**, multi-stage serverless orchestration with **AWS Step Functions**, asynchronous scoring via **AWS Lambda**, and transactional persistence in **Amazon DynamoDB**.

---

## Architecture Flow

```
                      [ Image Upload to S3 ]
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │       AWS Step Functions State Machine       │
         │                                              │
         │  ┌────────────────────────────────────────┐  │
         │  │ 1. Lambda: invoke_modelo_a             │  │
         │  │    - Downloads image from S3           │  │
         │  │    - Preprocesses tensor dimensions    │  │
         │  │    - Queries SageMaker real-time EP    │  │
         │  └───────────────────┬────────────────────┘  │
         │                      │                       │
         │                      ▼                       │
         │             ┌──────────────────┐             │
         │             │ AWS SageMaker EP │             │
         │             │  (MobileNetV2)   │             │
         │             └────────┬─────────┘             │
         │                      │                       │
         │                      ▼                       │
         │  ┌────────────────────────────────────────┐  │
         │  │ 2. Lambda: compute_score               │  │
         │  │    - Evaluates batch quality heuristics│  │
         │  │    - Computes batch score & decision   │  │
         │  └───────────────────┬────────────────────┘  │
         │                      │                       │
         └──────────────────────┼───────────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Amazon DynamoDB  │
                       │ (Inspection Log) │
                       └──────────────────┘
```

---

## Core Technologies & Components

* **Inference Endpoint:** Transfer learning with **MobileNetV2** (PyTorch) trained on SageMaker, registered under the SageMaker Model Registry (`Approved` status), and served on real-time managed instances.
* **Orchestration:** **AWS Step Functions** coordinates sequential execution and error-handling retries between ingestion and classification.
* **Serverless Compute:** Two decoupled **AWS Lambda** microservices handle payload transformation, endpoint querying, and business scoring logic.
* **Data Persistence:** **Amazon DynamoDB** logs inspection results, timestamps, and quality scores for auditing.
* **Infrastructure as Code:** **Terraform** provisions all S3 buckets (raw data, model artifacts, DVC store), IAM roles with least-privilege policies, Lambdas, CloudWatch alarms, and DynamoDB tables.
* **Data Versioning:** **DVC (Data Version Control)** coupled with Amazon S3 backend for dataset lineage.
* **Quality Assurance:** 19 unit & integration test suites run via **GitHub Actions** on every push.

---

## Deployment & Execution Workflow

### 1. Prerequisites
- Python 3.11
- AWS CLI v2 configured with active credentials
- Terraform >= 1.5
- DVC

### 2. Infrastructure Provisioning
```bash
make install                 # Set up virtual environment and dependencies
source .venv/bin/activate
make apply                   # Terraform apply: IAM, S3, DynamoDB, Lambdas, Step Functions
```

### 3. Model Training & Registry Workflow
```bash
# Push dataset to S3 remote via DVC
dvc push

# Trigger SageMaker training job
python scripts/run_training.py

# Inject inference code and register model in Model Registry
python scripts/repack_model.py
python scripts/register_model_package.py
```

### 4. Deploy SageMaker Endpoint
```bash
cd infra
terraform apply -var "model_package_arn=<APPROVED_PACKAGE_ARN>"
```

### 5. Automated Testing & Verification
```bash
# Run test suite with pytest & code style validation
make test

# Smoke test the live endpoint
python scripts/smoke_test_endpoint.py data/lemons/sample.jpg
```

---

## Automated Test Coverage

The project contains 19 automated test suites executed via GitHub Actions CI:
* `test_scoring_logic.py`: Evaluates scoring heuristics and edge-case classification logic.
* `test_invoke_modelo_a.py`: Validates Lambda invocation using S3 and SageMaker runtime mocking.
* `test_compute_score_handler.py`: Verifies item writing and DynamoDB integration.

---

## Author
**Luis Alberto González Escamilla**  
Software & Systems Engineer · AI Agents & Cloud Solutions
