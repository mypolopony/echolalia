"""Echolalia is a package for creating chatbot-based conversational agents."""

__version__ = "0.0.1"

from ._utils import get_matching_s3_objects
from .parser import WhatsAppParser, iMessageParser

__all__ = [
    # Utility stuff
    "get_matching_s3_objects"
    # Parser stuff
    "WhatsAppParser"
    "IMessageParser"
]
