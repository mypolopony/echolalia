import re
from dateutil import parser
from datetime import datetime
import pandas as pd
from ._utils import get_matching_s3_objects, read_s3_file
from io import BytesIO
import boto3

class ChatlogSchema(object):
    """
    Class to define the schema of a chat log. This is a simple class that contains the column names and data types for
    a chat log.
    """

    def __init__(self, columns: list):
        """
        Initialize the schema with the column names and data types.

        Parameters
        ----------
        columns : list
            A list of tuples containing the column name and data type. The data type should be a string that can be
            passed to the `pd.DataFrame.astype()` method.
        """
        self.columns = columns

    def get_columns(self) -> list:
        """
        Get the column names for the schema.

        Returns
        -------
        list
            A list of column names.
        """
        return [col[0] for col in self.columns]

    def get_dtypes(self) -> dict:
        """
        Get the data types for the schema.

        Returns
        -------
        dict
            A dictionary of column names and data types.
        """
        return {col[0]: col[1] for col in self.columns}

    def get_schema(self) -> dict:
        """
        Get the schema as a dictionary.

        Returns
        -------
        dict
            A dictionary of column names and data types.
        """
        return self.get_dtypes()

    def get_schema_df(self) -> pd.DataFrame:
        """
        Get the schema as a DataFrame.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the schema.
        """
        return pd.DataFrame(self.columns, columns=["column", "dtype"])


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
    
    def validate_chat_log(self, chat_log: str) -> bool:
        """
        Validate a chat log to ensure it is in the correct format.

        Parameters
        ----------
        chat_log : str
            The chat log to validate.

        Returns
        -------
        bool
            True if the chat log is valid, False otherwise.
        """
        return True
    
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
        return messages.groupby("group", as_index=False).agg({
            "user": "first",                 # Take the first value of "user" for each group
            "timestamp": list,               # Take the first value of "timestamp" for each group
            "message": " ".join,             # Concatenate the values of "message"
            "num_messages": "size",          # Count the number of messages
            "chatline": ". ".join            # Concatenate the values of "chatline"
        })


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
        self.messages = []

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
            assert(self.validate_chat_log(self.messages))
            self.combine_messages(self.messages)
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
        # Initialize the timestamp pattern
        self.timestamp_pattern = re.compile(
            r"[A-Za-z]{3} \d{1,2}, \d{4} \s*\d{1,2}:\d{2}:\d{2} (AM|PM)"
        )

    def parse_chat_log(self, bucket: str, chat_log_filename: str) -> pd.DataFrame:
        # Download the chat log from S3
        chat_log = self.download_chat_log(bucket=bucket, chat_log_filename=chat_log_filename)

        # Initialize payload
        payload = None

        # For line in chat log, if the timestamp is found, create a new message object based on the remaining content. Keep
        # track of the current user and timestamp for multi-line messages.
        lines = chat_log.splitlines()
        for line in lines:
            # Add if there has been a previous line
            if payload:
                self.messages.append(payload)

            # Search for the timestamp
            match = re.search(self.timestamp_pattern, line)

            # Extract the timestamp if found and convert to datetime
            if match: # A new message is starting
                # Initialize the return payload
                payload = {"timestamp": None, "source": None, "message": ""}

                # Extract the timestamp string
                timestamp_str = match.group(0)

                # Convert the timestamp string to a datetime object
                payload["timestamp"] = datetime.strptime(timestamp_str, "%b %d, %Y %I:%M:%S %p")

                # Next comes the source
                payload["source"] = next(lines)
            else:
                # We're in a message, add it to the payload
                if payload["message"]:
                    payload["message"] += ' ' + line    # Odd way to append, but it works
            
            # The sad, final message
            self.messages.append(payload)
            
        # Return as DataFrame with all messages cleansed and accounted for and all errors noted
        return pd.DataFrame(self.messages)