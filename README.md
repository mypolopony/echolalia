## echolalia
A Familiar Being

## What?
This is a simple effort to re-create a friend; generating a chatbot using previous conversations.

## Architecture
### Terraform
AWS resources Terraformed:

## Buld management
- Using `pyproject.toml` and `poetry` for dependancy management. Locally, the virtual environment is sym-linked to the poetry, so using `poetry add [package]` installs it in the local environment as well as sets it as a dependancy for use when building the Docker image.

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
./imessage-exporter -f txt -o output
subl +14156839285.txt
```

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
