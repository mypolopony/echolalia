Echolalia
![image](images/chatbot.png)
============
[![Current Version](https://img.shields.io/badge/version-0.9-green.svg)](github.com/mypolopony/echolalia) 

This is a simple effort to re-create a friend; generating a chatbot using text conversations spanning several years. Containerized and deployed on AWS.

## Input, Ingestion and Parsing

### WhatsApp
I started with a raw dump of a WhatsApp log, spanning 50,000+ lines. This included several line styles, special characters, image links, error messages, etc. I took care of as many special cases as possible to reduce the corpus to simple text. Then, I grouped the multiple messages by speaker, creating chunks of inputs and outputs between any number of users and the target user represernting pairs of the interaction. The target user is what that chatbot is attempting to mimic. 

### iMessage
iMessage chat logs are digested in the same way and can be accessed with some great tools (https://github.com/reagentx/imessage-exporter) to text format. 

## Architecture
This package generates a series of containers (debug, train, and chat) to be used with SageMaker. The containers are maintained on ECR and also used locally for debugging as well as to initiate the training and chat endpoints. 

### Terraform
AWS resources are Terraformed:
    - S3 buckets
    - IAM Roles
    - SageMaker instances
    - ECR repository

### Terraform
AWS resources Terraformed:
    - ECR
    - IAM
    - S3
    - SageMaker

## Buld management
- This project uses `pyproject.toml` and `poetry` for dependancy management. Locally, the virtual environment is sym-linked to the poetry, so using `poetry add [package]` installs it in the local environment as well as sets it as a dependancy for use when building the Docker image.

The Docker build is multi-stage. Similarly, `pyproject.toml` contains several groups to correspond to the different dependencies:
_base_ includes all of the major packages in order to run debugging and training
_debugger_ includes `pydebug` which can be used to run a local server and allow interactive debugging in Visual Code, for example
_training_ is the main training image
_chat_ is a slimmer image used for predictions


## Training
Training is done with AWS SageMaker on a GPU-enabled `ml.g4dn.xlarge` machine using A HuggingFace estimator. The training parameterized using a training manifest YAML, read from S3, which indicates not only the nature of the multiple sources of logs but also the parameters of the training regimen. 

Build and push and then run `echolalia` (the training image) with the proper S3 key to the training manifest. The instance will be set up and model will be generated based on the manifest, which is then uploaded to S3.

## Chat
Similarly, build and push  `echolalia-chat`. 
## Usage

0. Set up constants
1. Create and push a training manifest to an appropriate location on S3
2. Build, push and run `echolalia` (the training image)
3. Run the image locally (using `train.py` and `--manifest` with the proper S3 key)


## Notebooks
`workbook.py` is for debugging  
`demo.py` showcases some of the end-user cases as well as some data science analytics



## Proof
I should be able to ask the bot contextually dependent phrases (inside jokes, for example, developed over time), and it should respond positively.

## Results

## TODO
- add to training_manifest
- tar and send model

## Improvements
- Add only necessary files from docker image
- Use GitHub actions to automatically build and push ECR images
- Change `def generate_payload(line: str) -> dict:` to `->WhatAppPayload`
- Implement CloudWatch logging
- Consider timing