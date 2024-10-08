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
iMessage chat logs can be accessed with some great tools (https://github.com/reagentx/imessage-exporter) to text or HTML format. 

```

 2240  git clone https://github.com/ReagentX/imessage-exporter.git
 2241  lx
 2242  cd imessage-exporter
 2243  lx
 2244  ./build.sh
 2245  brew install cargo
 2246  brew install rust
 2247  lx
 2248  ./build.sh
 2249  rustup target add x86_64-apple-darwin
 2250  brew install rustup
 2251  rustup target add x86_64-apple-darwin
 2252  rustup default sable
 2253  rustup default stable
 2254  ./build.sh
 2255  rustup target add x86_64-apple-darwin
 2256  ./build.sh
 2257  rustup target add x86_64-apple-darwin
 2258  lx
 2259  cd image-exporter
 2260  lx
 2261  ./imessage-exporter
 2262  lx
 2263  cd src
 2264  lx
 2265  cd exporters
 2266  lx
 2267  cd ..
 2268  lx
 2269  cargo install imessage-exporter
 2270  imessage-exporter -f txt -o output -c efficient
 2271  /Users/mypolopony/.cargo/bin/imessage-exporter -g tct -o output
 2272  /Users/mypolopony/.cargo/bin/imessage-exporter -f txt -o output
 2273  /Users/mypolopony/Library/Messages/
 2274  lx
 2275  ls
 2276  cd ~/Projects/imessage-exporter
 2277  /Users/mypolopony/.cargo/bin/imessage-exporter -f txt -o output
 2278  lx
 2279  cd output
 2280  lx
 2281  ls -alsthrc
 2282  subl +14156839285.txt

 ```

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