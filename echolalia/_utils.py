from typing import Any, TypedDict
from datetime import datetime

import boto3
import pandas as pd
import numpy as np
from io import BytesIO


class S3Results(TypedDict):
    """
    TypedDict enumeration of S3 result.
    """

    Key: str
    LastModified: datetime
    ETag: str
    Size: int
    StorageClass: str


def get_matching_s3_objects(bucket, prefix="", search="", suffix="") -> S3Results:
    """
    Identify matching s3 objects based on search string criteria.

    Parameters
    ----------
    bucket : str
        The S3 bucket in which to find the objects.
    prefix : str, optional
        The S3 key prefix that identifies the objects, by default ""
    search : str, optional
        A string that must be in the S3 key, by default ""
    suffix : str, optional
        A string that must be at the end of the S3 key, by default ""


    Yields
    ------
    dict
        A dictionary containing the S3 object metadata.
    """
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")

    kwargs = {"Bucket": bucket}

    # We can pass the prefix directly to the S3 API
    if isinstance(prefix, str):
        kwargs["Prefix"] = prefix

    # Pagination
    for page in paginator.paginate(**kwargs):
        try:
            contents = page["Contents"]
        except KeyError:
            break

        # Check for matching objects
        for obj in contents:
            key = obj["Key"]
            if search in key and key.endswith(suffix):
                yield obj


def read_s3_file(bucket: str, key: str) -> str:
    """
    Download a file from S3 to local memory.

    Parameters
    ----------
    bucket : str
        The S3 bucket containing the file.
    key : str
        The key of the file in the S3 bucket.

    Returns
    -------
    str
        The content of the file as a string.
    """
    # Initialize the S3 client
    s3 = boto3.client("s3")

    # Create an in-memory bytes buffer
    file_buffer = BytesIO()

    # Download the file into the buffer
    s3.download_fileobj(Bucket=bucket, Key=key, Fileobj=file_buffer)

    # Move the cursor to the beginning of the buffer
    file_buffer.seek(0)

    # Read the content of the file
    content = file_buffer.read()

    # If the file contains text, decode it (assuming UTF-8 encoding)
    text_content = content.decode("utf-8")

    return text_content


def median_diff(series: list) -> pd.Timedelta:
    """
    This function calculates the median difference between consecutive elements in a pandas Series. It
    improves on the native impelementation in that it can handle series of size 1.

    Parameters
    ----------
    series: list
        The input list of pd.Timestamp [I think]

    Returns
    -------
    float
        The median difference between consecutive elements in the series
    """
    # This is a bizarre thing, for whatever reason the input is sent as a double array
    series = series[0]

    if len(series) > 1:  # Normal diff median calculation
        return pd.Series(series).diff().median()
    elif len(series) == 1:  # Median is just the singular value
        return pd.Timedelta(0)
    else:  # No values
        raise Exception("No values in the series")
