# echolalia
A Familiar Being

# What?
This is a simple effort to re-create a friend; generating a chatbot using previous conversations.

# Proof
I should be able to ask the bot, "how do you feel about McPherson Salon?" (a contextually dependent phrase), and it should respond positively.

# Improvements

- Read S3 file line by line ([https://pypi.org/project/smart-open/])
- Change `def generate_payload(line: str) -> dict:` to `->WhatAppPayload`