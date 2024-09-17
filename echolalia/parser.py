import re
from dateutil import parser
from datetime import datetime
import pandas as pd
from ._utils import get_matching_s3_objects, read_s3_file
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
    Parser class for WhatsApp chat logs.
    """

    '''
    class WhatsAPPLineException(Exception):
        """
        Exception class for WhatsApp messages.
        """
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)
    '''

    def __init__(self):
        # Initialize the log pattern. Rather bespoke, but it works fur current version [24.15.80 (628510191)] of WatsApp logs.
        # - Ignore any characters before the timestamp
        # - Extract the timestamp
        # - Extract the user (should end with the first colon)
        # - Extract the message (may include colons as well)
        self.log_pattern = re.compile(r'[^.]*?\[(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2}:\d{2})\/ue202f([APM]{2})\] (.+?): (.*)')

    def _sanitize_message(message: str) -> str:
        """
        Sanitize a line of text from a WhatsApp chat log by removing special characters, excluding certain messages. No
        particular model-based processing is done here, just basic text cleaning for the WhatsAPP chat logs.
        
        Parameters
        ----------
        message : str
            The message to sanitize.
        
        Returns
        -------
        str
            The sanitized message.
        """
        # Individual throaway cases
        if "/ue200e<attached:" in message:
            message = ""
        elif "/ue200eVoice call" in message:
            message = ""
        elif "/ue200eMissed voice call" in message:
            message = ""
        elif "/ue200eVideo call" in message:
            message = ""
        elif "/ue200eYou deleted this message." in message:
            message = ""
        elif "/ue200eTap to call back" in message:
            message = ""

        # Alays perform these replacements
        if " /ue200e<This message was edited>" in message:                      # If the message was edited, save the raw message
            message = message.replace(" /ue200e<This message was edited>", "")
        message = re.sub(r'http\S+', '', message)                               # Remove URLs
        message = message.strip()                                               # Remove leading/trailing whitespace

        return message

    def parse_chat_log(self, bucket: str, chat_log_filename: str) -> pd.DataFrame:
        """
        Download a chat log from S3 and parse it into a list of messages, with metadata.

        This parser does some basic sanitization of the messages, such as removing URLs and special characters. The
        result is a complete DataFrame with columns for the timestamp, user, message, and any exceptions that occurred.

        Further processing (collecting messages into groups, excluding eceptions, etc.) can be done on the result

        Parameters
        ----------
        bucket : str
            The S3 bucket containing the chat log.
        chat_log_filename : str
            The filename of the chat log.
        
        Returns
        -------
        pd.DataFrame
            A DataFrame containing the parsed chat log.
        """

        # Initialize a list of messages
        all_messages = []
        
        # Download the chat log from S3
        try:
            key = list(get_matching_s3_objects(bucket=bucket, search=chat_log_filename))[0]["Key"]
            chat_log = read_s3_file(bucket=bucket, key=key)
        except Exception as e:
            Exception(f"Error reading chat log from S3: {e}")

        # Maintain current user and timestamp for multi-line messages
        current_user, current_timestamp = None
        current_timestamp = None

        # Iterate over each line
        for line in chat_log.splitlines():
            # Initialize the return payload
            payload = {
                "timestamp": None,
                "user": None,
                "message": None,
                "exception": None,
                "chatline": line
            }

            # Find regex matches, if the exist
            matches = re.match(self.log_pattern, line)

            try:
                # Extract / transform elements from the line
                date = matches.group(1)                    # Date
                time = matches.group(2)                    # Time
                ampm = matches.group(3)                    # AM/PM
                timestamp = datetime.strptime(f"{date} {time} {ampm}", "%m/%d/%y %I:%M:%S %p") # Timestamp
                user = matches.group(4)                    # Username
                message = matches.group(5)                 # Message

                # Update the payload
                payload["user"] = current_user = user
                payload["timestamp"] = current_timestamp = timestamp
                
                # Sanitize and assign the correctly formatted payload message
                payload["message"] = self._sanitize_message(message)
            except Exception as e:
                # If we have an existying current user and timestamp, we can try to append the original chatline
                if current_user and current_timestamp:
                    payload["user"] = current_user
                    payload["timestamp"] = current_timestamp
                    
                    # Sanitize and assign the raw chatline
                    payload["message"] = self._sanitize_message(payload["chatline"])
                    
                    continue
            finally:
                # At this point they payload should be as complete as possible
                if payload["user"] and payload["timestamp"]:
                    all_messages.append(payload)
                
                # If at the end of the day, something is really off, exclude any totally disconnected mesages (i.e. 
                # no user or timestamp) and alert the user because this shouldn't happen
                else:   
                    print("[Hopefully just opening empty line, skipping: ", line)
                    continue
                    
                # Update exception if message is empty
                if not payload["message"]:
                    payload["exception"] = "No content to message"
                
                continue
        
        # Return as DataFrame with all messages cleansed and accounted for and all errors noted
        return pd.DataFrame(all_messages)