## echolalia
A Familiar Being

## What?
This is a simple effort to re-create a friend; generating a chatbot using previous conversations over several years.

## Architecture
### Terraform
AWS resources Terraformed:

## Buld management
- Using `pyproject.toml` and `poetry` for dependancy management. Locally, the virtual environment is sym-linked to the poetry, so using `poetry add [package]` installs it in the local environment as well as sets it as a dependancy for use when building the Docker image.

## Running locally with bash entrypoint
```bash
docker run -i -d -v ~/.aws:/root/.aws:ro --entrypoint=bash echolalia
dde1e5d84211be972e88ca377a4c0069db3461443c0dd53cd9f421f1a85b015b
docker exec -it dde1e5d84211 bash
```

# Debugging with VS code (multi-stage build) [always rebuild]
docker build --target=debugger -t echolalia-debugger .
docker run -v ~/.aws:/root/.aws:ro -p 5678:5678 echolalia-debugger run.py

## Input, Ingestion and Cleanup
### WhatsApp
I started with a raw dump of a WhatsApp log, spanning several years and 50,000+ lines long. This included several line styles, special characters, error messages, etc. I took care of as many special cases as possible to reduce the corpus to simple text. Then, I grouped the multiple messages by speaker, creating chunks of inputs and outputs (essentially questions and answers) between any number of users and the target user. The target user is what that chatbot is attempting to mimic. 

# iMessage
iMessage chat logs can be accessed with some great tools (https://github.com/reagentx/imessage-exporter) to text or HTML format. 



## Pruning for modeling
--

## Notebooks
`workbook.py` is for debugging  
`demo.py` showcases some of the end-user cases as well as some data science analytics

## Proof
I should be able to ask the bot contextually dependent phrases (inside jokes, for example, developed over time), and it should respond positively.

## Results


## Improvements

- Read S3 file line by line ([https://pypi.org/project/smart-open/])
- Change `def generate_payload(line: str) -> dict:` to `->WhatAppPayload`
- Implement logging