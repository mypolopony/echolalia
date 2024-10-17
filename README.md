## echolalia
A Familiar Being

## What?
This is a simple effort to re-create a friend; generating a chatbot using previous conversations over several years.

## Architecture
### Terraform
AWS resources Terraformed:

## Buld management
- Using `pyproject.toml` and `poetry` for dependancy management. Locally, the virtual environment is sym-linked to the poetry, so using `poetry add [package]` installs it in the local environment as well as sets it as a dependancy for use when building the Docker image.

As a quirk, SageMaker expects `requirements.txt` as well, so it's necessary to do `poetry export -f requirements.txt --output requirements.txt --without-hashes` to keep that file up to date.

## Running locally with bash entrypoint
```bash
docker run -i -d -v ~/.aws:/root/.aws:ro --entrypoint=bash echolalia
dde1e5d84211be972e88ca377a4c0069db3461443c0dd53cd9f421f1a85b015b
docker exec -it dde1e5d84211 bash
```

## Development build and push
```bash
aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 897729117324.dkr.ecr.us-west-1.amazonaws.com/echolalia

docker build --platform=linux/amd64 --target=training -t echolalia-training .
docker tag echolalia-training:latest 897729117324.dkr.ecr.us-west-1.amazonaws.com/echolalia:latest
docker push 897729117324.dkr.ecr.us-west-1.amazonaws.com/echolalia:latest
```

# Debugging with VS code (multi-stage build) [always rebuild]
```bash
docker build --target=debugger -t echolalia-debugger .
docker run -v ~/.aws:/root/.aws:ro -p 5678:5678 echolalia-debugger run.py
```


## Input, Ingestion and Cleanup

### WhatsApp
I started with a raw dump of a WhatsApp log, spanning several years and 50,000+ lines long. This included several line styles, special characters, error messages, etc. I took care of as many special cases as possible to reduce the corpus to simple text. Then, I grouped the multiple messages by speaker, creating chunks of inputs and outputs (essentially questions and answers) between any number of users and the target user. The target user is what that chatbot is attempting to mimic. 

# iMessage
iMessage chat logs can be accessed with some great tools (https://github.com/reagentx/imessage-exporter) to text or HTML format: 

```
git clone https://github.com/ReagentX/imessage-exporter.git
cd imessage-exporter
brew install cargo
brew install rust
brew install rustup
rustup target add x86_64-apple-darwin
rustup default stable
/Users/mypolopony/.cargo/bin/imessage-exporter -f txt -o output
```

Output will be `output/+[PHONE_NUMBER].txt`


## Notebooks
`workbook.py` is for debugging  
`demo.py` showcases some of the end-user cases as well as some data science analytics

## Training
Training is done with AWS SageMaker on a GPU-enabled `ml.g4dn.xlarge` machine. Training is set up via a `training_manifest.yaml`, read from S3, which indicates not only the nature of the multiple sources of logs but also the parameters of the training regimen. 

## GPU vs CPU

Is this a GPU implementation?
Build with `docker build --platform=linux/amd64 --target=training -t echolalia-training .`

## Proof
I should be able to ask the bot contextually dependent phrases (inside jokes, for example, developed over time), and it should respond positively.

## Results

## Improvements

- Read S3 file line by line ([https://pypi.org/project/smart-open/])
- Change `def generate_payload(line: str) -> dict:` to `->WhatAppPayload`
- Implement logging
- Consider timing
