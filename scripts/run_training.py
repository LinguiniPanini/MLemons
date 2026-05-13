"""Ejecuta el training job que esta en el notebook 03 sin abrir Jupyter.

Util para probar end-to-end desde la CLI antes de correr el notebook.
"""
import os
import subprocess
import boto3
import sagemaker
from sagemaker.pytorch import PyTorch


def main():
    creds = subprocess.check_output(
        ['aws', 'configure', 'export-credentials', '--format', 'env-no-export']
    ).decode()
    for line in creds.strip().split('\n'):
        k, _, v = line.partition('=')
        os.environ[k] = v

    region = 'us-east-2'
    boto_sess = boto3.Session(region_name=region)
    sm_session = sagemaker.Session(boto_session=boto_sess)
    account = boto_sess.client('sts').get_caller_identity()['Account']
    role = f'arn:aws:iam::{account}:role/mlemons-sagemaker-role'

    bucket_raw = f'mlemons-raw-{account}'
    bucket_models = f'mlemons-models-{account}'
    train_s3 = f's3://{bucket_raw}/lemons'

    print('Account :', account)
    print('Role    :', role)
    print('Train   :', train_s3)
    print('Models  :', f's3://{bucket_models}/modelo-a/')
    print()

    estimator = PyTorch(
        entry_point='script.py',
        source_dir='src/modelo_a',
        role=role,
        framework_version='2.0.1',
        py_version='py310',
        instance_count=1,
        instance_type='ml.m5.large',
        output_path=f's3://{bucket_models}/modelo-a/',
        base_job_name='mlemons-modelo-a',
        hyperparameters={
            'epochs': 3,
            'batch_size': 32,
            'lr': 1e-3,
        },
        metric_definitions=[
            {'Name': 'test:accuracy', 'Regex': r'Test accuracy: ([0-9.]+)'},
            {'Name': 'test:loss',     'Regex': r'Test loss: ([0-9.]+)'},
        ],
        sagemaker_session=sm_session,
        max_run=3600,
    )

    estimator.fit({'train': train_s3}, wait=True)
    job_name = estimator.latest_training_job.name
    model_data = estimator.model_data

    print()
    print('===== JOB COMPLETO =====')
    print('Job   :', job_name)
    print('Model :', model_data)

    sm = boto_sess.client('sagemaker')
    desc = sm.describe_training_job(TrainingJobName=job_name)
    metrics = {m['MetricName']: m['Value'] for m in desc.get('FinalMetricDataList', [])}
    print('Metricas:')
    for k, v in metrics.items():
        print(f'  {k:18s} = {v}')


if __name__ == '__main__':
    main()
