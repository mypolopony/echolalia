import re
from datetime import datetime
import pandas as pd

from echolalia.parser import WhatsAppParser
from echolalia.constants import S3_BUCKET_NAME, CHAT_LOG_FILENAME

parser = WhatsAppParser()

print(f"Parsing WhatsApp chat... for s3://{S3_BUCKET_NAME}/{CHAT_LOG_FILENAME}")

# Parse the chat log into dicts and then into a DataFrame
messages = parser.parse_chat_log(bucket=S3_BUCKET_NAME, chat_log_filename=CHAT_LOG_FILENAME)

print(messages)
