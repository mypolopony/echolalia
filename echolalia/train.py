import argparse

import boto3
import pandas as pd
import echolalia.run_sagemaker as run_sagemaker
import torch
import yaml
from sagemaker.pytorch import PyTorch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from torch.utils.data import Dataset

from echolalia.constants import S3_BUCKET_NAME, SAGEMAKER_ARN
from echolalia.parser import WhatsAppParser, iMessageParser
from echolalia._utils import read_s3_file


class ConversationDataset(Dataset):
    """
    The ConversationDataset class is a PyTorch Dataset that takes in a list of input_ids and output_ids. It 
    wraps a tokenized data into a format compatible with PyTorch, which requires a dataset to be a subclass 
    of torch.utils.data.Dataset
    """

    def __init__(self, input_ids, output_ids):
        self.input_ids = input_ids
        self.output_ids = output_ids

    def __len__(self):
        return len(self.input_ids)

    def __getitem__(self, idx):
        return {
            "input_ids": self.input_ids[idx],
            "labels": self.output_ids[idx]  # Model needs labels during training
        }

# Define the argument parser
def parse_args():
    parser = argparse.ArgumentParser()

    # Add argument for the YAML configuration file
    parser.add_argument("--manifest", type=str, help="training manifest file")

    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments
    args = parse_args()

    # Load manifest from S3
    manifest = yaml.safe_load(read_s3_file(S3_BUCKET_NAME, args.manifest))

    # Gather messages for each source
    for source in manifest["sources"]:
        # Check for source type
        if source["type"] == "WhatsApp":
            parser = WhatsAppParser()
        elif source["type"] == "iMessage":
            parser = iMessageParser()
        else:
            raise ValueError(f"Unknown source type: {source['type']}")
        
        # Parse chat log
        messages = parser.parse_chat_log(bucket=S3_BUCKET_NAME, chat_log_filename=source["logfile"])
    
        # Prune messages
        # If the first message is from the target user, it won't be correlated to a previous input, so remove it
        if messages.iloc[0]["user"] == source["user"]:
            messages = messages.iloc[1:]
        # If the last message is NOT from the target user, it won't be correlated to a following output, so remove it
        if messages.iloc[-1]["user"] != source["user"]:
            messages = messages.iloc[:-1]

        # Now inputs and outputs are aligned, one row after the other. Join into a single DataFrame
        source["training_data"] = pd.DataFrame({
            "input": messages[messages["user"] != source["user"]]["message"].values,
            "output": messages[messages["user"] == source["user"]]["message"].values
        })
    
    # Combine all sources into a single DataFrame
    training_data = pd.concat([source["training_data"] for source in manifest["sources"]])

    # Model definition
    tokenizer = AutoTokenizer.from_pretrained(manifest["model_name"])
    model = AutoModelForCausalLM.from_pretrained(manifest["model_name"])

    # Set pad_token to eos_token
    tokenizer.pad_token = tokenizer.eos_token

    # Tokenize the inputs and outputs
    training_data["input_ids"] = training_data["input"].apply(lambda x: tokenizer.encode(x, truncation=True, padding="max_length", max_length=512))
    training_data["output_ids"] = training_data["output"].apply(lambda x: tokenizer.encode(x, truncation=True, padding="max_length", max_length=512))

    # Convert columns to lists
    input_ids = training_data["input_ids"].tolist()
    output_ids = training_data["output_ids"].tolist()

    # Convert lists to PyTorch tensors
    input_ids_tensor = torch.tensor(input_ids)
    output_ids_tensor = torch.tensor(output_ids)

    # Ensure both tensors have the same shape for proper input-output pairing
    assert input_ids_tensor.shape == output_ids_tensor.shape

    # Instantiate the dataset
    dataset = ConversationDataset(input_ids_tensor, output_ids_tensor)

    # Resize tokens
    model.resize_token_embeddings(len(tokenizer))

    # Training args from manifest
    training_args = TrainingArguments(**manifest["training_args"])

    # Create the Trainer instance
    trainer = Trainer(
        model=model,            # The model to train
        args=training_args,     # Training arguments
        train_dataset=dataset,  # Training dataset
        eval_dataset=dataset,   # Same as training dataset for now
    )

    # Start training
    trainer.train()

    # Save the model
    trainer.save_model("./model")