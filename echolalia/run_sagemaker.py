import os

import boto3
import echolalia.run_sagemaker as run_sagemaker
from sagemaker.estimator import Estimator
from sagemaker.pytorch import PyTorch

from echolalia.constants import SAGEMAKER_ARN, S3_BUCKET_NAME, IMAGE_URL

def main():
    os.environ["TRANSFORMERS_LOG_LEVEL"] = "debug"  # Turn on logging for the transformers library

    # Create a session
    boto_session = boto3.Session()
    sagemaker_session = run_sagemaker.Session(boto_session=boto_session)

    # Create the Estimator
    estimator = Estimator(
        image_uri=IMAGE_URL,                    # Image
        instance_type='ml.g4dn.xlarge',         # GPU instance
        instance_count=1,
        role=SAGEMAKER_ARN,                     # Pass the role
        sagemaker_session=sagemaker_session,    # Pass the session with the specified region
        hyperparameters={
            'manifest': "training/training_manifest.yaml",
        },
        debugger_hook_config = True,            # Enable debugger hook for more detailed logging,
        output_path = f"s3://{S3_BUCKET_NAME}/results/"
    )

    # Do some work!
    estimator.fit()

if __name__ == "__main__":
    main()