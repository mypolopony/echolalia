import re
from datetime import datetime
import pandas as pd

from echolalia.parser import WhatsAppParser

parser = WhatsAppParser()

S3_BUCKET_NAME = "smcphers-echolalia"
CHAT_LOG_FILENAME = "data/_chat.txt"

print(f"Parsing WhatsApp chat... for s3://{S3_BUCKET_NAME}/{CHAT_LOG_FILENAME}")

# Parse the chat log into dicts and then into a DataFrame
messages = parser.parse_chat_log(bucket=S3_BUCKET_NAME, chat_log_filename=CHAT_LOG_FILENAME)

print(messages)