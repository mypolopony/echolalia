import re
from dateutil import parser
import pandas as pd
from ._utils import get_matching_s3_objects, read_s3_file
from .constants import S3_BUCKET_NAME
from io import BytesIO
import boto3

class GenericParser(object):
    """
    Generic parser class to be inherited by specific chat log parsers. May contain general
    serialization or sterilization features, regardless of source
    """
    def __init__(self):
        pass
    
class WhatsAppParser(GenericParser):
    """
    A specific parser for WhatsApp chat logs. The chat log should be in the following format:
        [12/31/21, 11:59:59 PM] User Name: Message text 

    Multiline messages are supported, but the timestamp and user name must be on the first line.

    Attributes:
        chat_log (str): The file to read the chat log from

    NOTA BENE: This parser will omit the last message in the chat for reasons.
    """
    
    def parse_chat_log(self, chat_log_filename: str) -> list[dict]:
        """
        Download a chat log from S3 and parse it into a list of messages.
        """

        # Initialize the payload
        payload = None

        # Initialize a list of messages
        messages = []

        # Flag to indicate if the current message is complete
        COMPLETED_MESSAGE = False
        
        # Download the chat log from S3
        try:
            key = list(get_matching_s3_objects(bucket="smcphers-echolalia", search=chat_log_filename))[0]["Key"]
            chat_log = read_s3_file(bucket=S3_BUCKET_NAME, key=key)
        except:
            Exception("Chat log not found")

        # Regex pattern to match the timestamp, user (with spaces and hyphens), and message
        pattern = r'\[(.*?)\] (.+?):\s*(.+)'

        for line in chat_log.splitlines():
            # Apply the regex pattern to extract the components
            match = re.match(pattern, line)

            try:
                # Interpret the line components
                timestamp = match.group(1)
                user = match.group(2)
                message = match.group(3)

                # If the current message is complete, append it to the list of messages
                if timestamp and user and message and payload is not None:
                    messages.append(payload)
                    payload = None  # Reset the payload

                # The return payload
                payload = {
                    "timestamp": parser.parse(timestamp),
                    "user": user,
                    "message": message,
                    "exception": None,
                    "chatline": line
                }
            except:
                # If the line doesn't match the pattern, it's part of the current multi-line message
                assert payload is not None, "Payload not initialized" # TODO: This does not handle the first cast - is this even hit?
                payload["message"] += f"\n{line}"

        return messages