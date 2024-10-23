Echolalia
![image](images/chatbot.png)
============
[![Current Version](https://img.shields.io/badge/version-0.9-green.svg)](github.com/mypolopony/echolalia) 

_In development_

This is a simple, home-grown effort to re-create a friend; generating a chatbot using text conversations spanning several years. Containerized and deployed on AWS with learning and prediction using SageMaker.

## Input, Ingestion and Parsing

### WhatsApp
A raw dump of a WhatsApp log spans more than 50,000+ messages. This includes several line styles, special characters, image links, error messages, etc. Cleansing these special cases reduces the corpus to simple text between (in this case, two) users. The messages are grouped by speaker, creating chunks of inputs and outputs between the target user and the other user, represernting pairs of the interaction. The target user (outputs) is what that chatbot is attempting to mimic. 

### iMessage
iMessage chat logs are digested in the same way and can be accessed with some great tools (https://github.com/reagentx/imessage-exporter) to text format. 

## Architecture
This package generates a series of containers (debug, train, and chat) to be used with SageMaker. The containers are maintained on ECR and also used locally for debugging as well as to initiate the training and chat endpoints. 

### Terraform (IaC)
All AWS resources are Terraformed:
    - S3 buckets
    - IAM Roles
    - SageMaker instances
    - ECR repositories

## Buld management
- This project uses `pyproject.toml` and `poetry` for dependancy management. Locally, the virtual environment is sym-linked to the poetry, so using `poetry add [package]` installs it in the local environment as well as sets it as a dependancy for use when building the Docker image.

The Docker build is multi-stage. Similarly, `pyproject.toml` contains several groups to correspond to the different dependencies:
_base_ includes all of the major packages in order to run debugging and training
_debugger_ includes `pydebug` which can be used to run a local server and allow interactive debugging in Visual Code, for example
_training_ is the main training image
_chat_ is a slimmer image used for predictions


## Training
Training is done with AWS SageMaker on a GPU-enabled `ml.g4dn.xlarge` machine using a generic Estimator. The training is parameterized using a training manifest YAML, read from S3, which indicates not only the nature of the multiple sources of logs to parse but also the parameters of the training regimen. 

## Usage
0. Set up constants
1. Create and push a training manifest to an appropriate location on S3
2. Build and push `echolalia` (the training image)
3. Run the Estimator which will initialize and run the job on SageMaker (example: `run_sagemaker.py`) to generate model files
4. Build and push `echolalia-chat` 
5. Run the Chatbot to have a conversation (example: `chat.py`)

## Proof
I should be able to ask the bot contextually dependent phrases (inside jokes, for example, developed over time), and it should respond positively.

## TODO
- Move from notebooks to class-based code
- Add to training_manifest
- Ensure model is tar/gzip'd

## Improvements
- Add only necessary files from Docker image
- Use GitHub actions to automatically build and push ECR images
- Change `def generate_payload(line: str) -> dict:` to `->WhatAppPayload`
- Implement CloudWatch logging
- Consider timing context