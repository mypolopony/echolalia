import re
from datetime import datetime
from io import BytesIO

import boto3
import pandas as pd
from dateutil import parser

from ._utils import get_matching_s3_objects, read_s3_file
from echolalia.parser import WhatsAppParser, iMessageParser


class GenericParser(object):
    """
    Generic parser class to be inherited by specific chat log parsers. May contain general
    serialization or sterilization features, regardless of source
    """

    def __init__(self):
        pass

    def download_chat_log(self, bucket: str, chat_log_filename: str) -> str:
        """
        Download a chat log from S3.

        Parameters
        ----------
        bucket : str
            The S3 bucket containing the chat log.
        chat_log_filename : str
            The filename of the chat log.

        Returns
        -------
        str
            The chat log as a string.
        """
        # Download the chat log from S3
        try:
            key = list(get_matching_s3_objects(bucket=bucket, search=chat_log_filename))[0]["Key"]
            chat_log = read_s3_file(bucket=bucket, key=key)
        except Exception as e:
            raise Exception(f"Error reading chat log from S3: {e}")

        return chat_log

    def combine_messages(self, messages: pd.DataFrame) -> pd.DataFrame:
        """
        Combine messages into groups based on the user and timestamp. This combines multi-line messages into a single
        message and counts the number of messages in each, as well as collecting the timestamps and individual chatlines.

        Parameters
        ----------
        messages : pd.DataFrame
            A DataFrame containing the messages to combine.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the combined messages.
        """
        # Filter out messages with exceptions
        messages = messages[~messages["exception"].apply(lambda x: isinstance(x, str))]

        # Sort by timestamp
        messages = messages.sort_values(by="timestamp")

        # Add time between last messages
        messages["time_diff"] = messages["timestamp"].diff().dt.total_seconds()

        # Create a "group" whenever the user changes
        messages["group"] = (messages["user"] != messages["user"].shift()).cumsum()
        messages["num_messages"] = None

        # Group by this new "group" column and concatenate the values in "messages"
        return (
            messages.groupby("group", as_index=False)
            .agg(
                {
                    "user": "first",  # Take the first value of "user" for each group
                    "timestamp": list,  # Take the first value of "timestamp" for each group
                    "message": " ".join,  # Concatenate the values of "message"
                    "num_messages": "size",  # Count the number of messages
                }
            )
            .drop("group", axis=1)
        )


class WhatsAppParser(GenericParser):
    """
    Parser class for WhatsApp chat logs.
    """

    def __init__(self):
        self.messages = []

        # Initialize the log pattern. Rather bespoke, but it works fur current version [24.15.80 (628510191)] of WatsApp logs.
        # - Ignore any characters before the timestamp
        # - Extract the timestamp
        # - Extract the user (should end with the first colon)
        # - Extract the message (may include colons as well)
        self.log_pattern = re.compile(
            r"[^.]*?\[(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2}:\d{2})\u202f([APM]{2})\] (.+?): (.*)"
        )

    def _sanitize_message(self, message: str) -> str:
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
        if "\u200e<attached:" in message:
            message = ""
        elif "\u200eVoice call" in message:
            message = ""
        elif "\u200eMissed voice call" in message:
            message = ""
        elif "\u200eVideo call" in message:
            message = ""
        elif "\u200eYou deleted this message." in message:
            message = ""
        elif "\u200eTap to call back" in message:
            message = ""
        elif "\u200eMessages and calls are end-to-end encrypted" in message:
            message = ""

        # Alays perform these replacements
        if " /\u200e<This message was edited>" in message:  # If the message was edited, save the raw message
            message = message.replace(" /u200e<This message was edited>", "")
        message = re.sub(r"http\S+", "", message)  # Remove URLs
        message = message.strip()  # Remove leading/trailing whitespace

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

        # Download the chat log from S3
        chat_log = self.download_chat_log(bucket=bucket, chat_log_filename=chat_log_filename)

        # Maintain current user and timestamp for multi-line messages
        current_user = current_timestamp = None

        # Iterate over each line
        for line in chat_log.splitlines():
            # Initialize the return payload
            payload = {"timestamp": None, "user": None, "message": None, "exception": None, "chatline": line}

            # Find regex matches, if the exist
            matches = re.match(self.log_pattern, line)

            try:
                # Extract / transform elements from the line
                date = matches.group(1)  # Date
                time = matches.group(2)  # Time
                ampm = matches.group(3)  # AM/PM
                timestamp = datetime.strptime(f"{date} {time} {ampm}", "%m/%d/%y %I:%M:%S %p")  # Timestamp
                user = matches.group(4)  # Username
                message = matches.group(5)  # Message

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
                # At this point the payload should be as complete as possible
                if payload["user"] and payload["timestamp"]:
                    self.messages.append(payload)

                # If at the end of the day, something is really off, exclude any totally disconnected mesages (i.e.
                # no user or timestamp) and alert the user because this shouldn't happen
                else:
                    payload["exception"] = "Contextless message"

                # Update exception if message is simply empty
                if not payload["message"]:
                    payload["exception"] = "No content to message"

                continue

        # DataFrame it
        self.messages = pd.DataFrame(self.messages)

        # Validate and concatenate the messages
        try:
            self.messages = self.combine_messages(self.messages)
        except Exception as e:
            raise Exception(f"Error validating chat log: {e}")

        # Return as DataFrame with all messages cleansed and accounted for and all errors noted
        return pd.DataFrame(self.messages)


class iMessageParser(GenericParser):
    """
    Parser class for iMessage / iChat chat logs.

    This utelizes open source code from https://github.com/ReagentX/imessage-exporter which turns the iMessage database
    into text files. This parser is designed to work with those text files.
    """

    def __init__(self):
        self.messages = []

        # Initialize the timestamp pattern
        self.timestamp_pattern = re.compile(r"[A-Za-z]{3} \d{1,2}, \d{4} \s*\d{1,2}:\d{2}:\d{2} (AM|PM)")

    def _sanitize_message(self, message: str) -> str:
        """
        Sanitize a line of text from an iMessage chat log by excluding certain messages.

        Parameters
        ----------
        message : str
            The message to sanitize.

        Returns
        -------
        str
            The sanitized message.
        """
        # Remove filenames (images)
        base_pattern = r"^.+\.\w+"
    
        # Check if the string only contains the filename
        if re.fullmatch(base_pattern, message):
            message = ""  # If only the filename is present, return an empty string
        else:
            # If there is additional text, remove just the filename
            message = re.sub(base_pattern + r"\s+", "", message)

        # Remove out of order / redundant messages
        if "This message responded to an earlier message." in message:
            message = ""
        
        return message

    def parse_chat_log(self, bucket: str, chat_log_filename: str) -> pd.DataFrame:
        # Download the chat log from S3
        chat_log = self.download_chat_log(bucket=bucket, chat_log_filename=chat_log_filename)

        # Initialize payload
        payload = None

        # For line in chat log, if the timestamp is found, create a new message object based on the remaining content. Keep
        # track of the current user and timestamp for multi-line messages.
        lines = iter(chat_log.splitlines())
        for line in lines:

            if "He gave us catholic school girls so" in line:
                print("Found it")
            # Search for the timestamp
            match = re.search(self.timestamp_pattern, line)

            # Extract the timestamp if found and convert to datetime
            if match:  # A new message is starting
                # Add if there has been a previous line
                if payload:
                    payload["message"] = self._sanitize_message(payload["message"].strip())
                    if payload["message"]:
                        self.messages.append(payload)

                # Initialize the return payload
                payload = {"timestamp": None, "user": None, "message": "", "exception": None}

                # Extract the timestamp string
                timestamp_str = match.group(0)

                # Convert the timestamp string to a datetime object
                payload["timestamp"] = datetime.strptime(timestamp_str, "%b %d, %Y %I:%M:%S %p")

                # Next comes the source
                payload["user"] = next(lines).strip()
            else:
                # We're in a message, add it to the payload
                payload["message"] += " " + line # Odd way to append, but it works

        # The sad, final message
        payload["message"] = payload["message"].strip()
        self.messages.append(payload)

        # DataFrame it
        self.messages = pd.DataFrame(self.messages)

        # Validate and concatenate the messages
        try:
            self.messages = self.combine_messages(self.messages)
        except Exception as e:
            raise Exception(f"Error validating chat log: {e}")

        # Return as DataFrame with all messages cleansed and accounted for and all errors noted
        return pd.DataFrame(self.messages)
