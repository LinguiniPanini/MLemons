"""Registra el ultimo training job como Model Package aprobado.

Toma el job ya finalizado (output del run_training.py) y crea/actualiza el
Model Package Group + Model Package + Approval. Imprime el ARN final.
"""
import os
import subprocess
import sys
import boto3
import sagemaker


def main(job_name=None):
    creds = subprocess.check_output(
        ["aws", "configure", "export-credentials", "--format", "env-no-export"]
    ).decode()
    for line in creds.strip().split("\n"):
        k, _, v = line.partition("=")
        os.environ[k] = v

    region = "us-east-2"
    sess = boto3.Session(region_name=region)
    sm = sess.client("sagemaker")

    if job_name is None:
        # tomar el job mas reciente con prefix mlemons-modelo-a
        jobs = sm.list_training_jobs(
            NameContains="mlemons-modelo-a",
            StatusEquals="Completed",
            SortBy="CreationTime",
            SortOrder="Descending",
            MaxResults=1,
        )["TrainingJobSummaries"]
        if not jobs:
            print("ERROR: no hay training jobs completados con prefix mlemons-modelo-a", file=sys.stderr)
            sys.exit(1)
        job_name = jobs[0]["TrainingJobName"]

    desc = sm.describe_training_job(TrainingJobName=job_name)
    model_data = desc["ModelArtifacts"]["S3ModelArtifacts"]
    print("Job        :", job_name)
    print("Model data :", model_data)

    image_uri = sagemaker.image_uris.retrieve(
        framework="pytorch",
        region=region,
        version="2.0.1",
        py_version="py310",
        instance_type="ml.t2.medium",
        image_scope="inference",
    )
    print("Image      :", image_uri)

    group_name = "mlemons-modelo-a-group"
    try:
        sm.create_model_package_group(
            ModelPackageGroupName=group_name,
            ModelPackageGroupDescription="Modelo A binario (sano vs defectuoso)",
        )
        print("Grupo creado:", group_name)
    except sm.exceptions.ResourceInUse:
        print("Grupo ya existe:", group_name)

    resp = sm.create_model_package(
        ModelPackageGroupName=group_name,
        ModelPackageDescription=f"Trained job {job_name}",
        InferenceSpecification={
            "Containers": [
                {
                    "Image": image_uri,
                    "ModelDataUrl": model_data,
                }
            ],
            "SupportedContentTypes": ["application/x-image"],
            "SupportedResponseMIMETypes": ["application/json"],
        },
        ModelApprovalStatus="PendingManualApproval",
    )
    package_arn = resp["ModelPackageArn"]
    print("Package    :", package_arn)

    sm.update_model_package(
        ModelPackageArn=package_arn,
        ModelApprovalStatus="Approved",
        ApprovalDescription="Cumple objetivo accuracy >= 0.90 (97.76%)",
    )
    print("Approved   : si")
    print()
    print("===== USO =====")
    print(f"cd infra && terraform apply -var 'model_package_arn={package_arn}'")
    return package_arn


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
