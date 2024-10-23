import logging
import random

import boto3
import sagemaker
from botocore.exceptions import ClientError
from sagemaker.model import Model
from sagemaker.serverless import ServerlessInferenceConfig

from echolalia.constants import CHAT_IMAGE_URL, S3_BUCKET_NAME, SAGEMAKER_ARN

def main():
    # Initialize logging
    logging.basicConfig(level=logging.INFO)

    # Initialize SageMaker session and role
    sagemaker_session = sagemaker.Session()

    # Initialize SageMaker client
    sagemaker_client = boto3.client("sagemaker")

    model_name = "catmodel"  # Name of the model

    # Define model parameters
    model_artifact = f"s3://{S3_BUCKET_NAME}/models/{model_name}.tar.gz"  # S3 path to the model file

    # Create the SageMaker model
    model = Model(
        model_data=model_artifact,
        role=SAGEMAKER_ARN,
        image_uri=CHAT_IMAGE_URL,
        sagemaker_session=sagemaker_session
    )

    serverless_config = ServerlessInferenceConfig(
        memory_size_in_mb=2048,    # Specify memory size
        max_concurrency=5          # Specify max concurrency
    )

    predictor = None

    try:
        # Deploy the model
        endpoint_name = f"chatbot-endpoint-{random.randint(0, 1e6)}"
        logging.info(f"Deploying model to endpoint: {endpoint_name}")
        
        predictor = model.deploy(
            endpoint_name=endpoint_name,  # Specify an endpoint name
            serverless_inference_config=serverless_config
        )
        logging.info("Model successfully deployed")

        # Chat loop
        while True:
            chat_input = input("Enter your message (or 'exit' to quit): ").strip()
            
            if chat_input.lower() == 'exit':
                logging.info("Exiting chat.")
                break
            
            if not chat_input:
                logging.warning("Empty input received. Please enter a valid message.")
                continue
            
            try:
                response = predictor.predict(chat_input)  # Get model prediction
                print("Chatbot Response:", response)      # Print the response
            except Exception as e:
                logging.error(f"Error during prediction: {e}")

    except ClientError as e:
        logging.error(f"Error deploying model: {e}")
    finally:
        # Clean up
        if predictor:
            try:
                logging.info("Deleting endpoint...")
                predictor.delete_endpoint()
                logging.info(f"Endpoint {endpoint_name} successfully deleted.")
            except Exception as e:
                logging.error(f"Error deleting endpoint: {e}")

if __name__ == "__main__":
    main()