import pandas as pd

class Contextualizer():
    """
    Given a conversation, this class will create inputs and outputs for a chatbot model.
    """
    def __init__(self, conversation: pd.DataFrame, target: str) -> None:
        """
        Parameters
        ----------
        conversation (pd.DataFrame): 
            A DataFrame containing the conversation
        target (str): 
            The target user to generate the model for
        """
        self.conversation = conversation
        self.target = target

    def sliding_window(self, window_size: int=5) -> pd.DataFrame:
        """
        Returns a DataFrame with a sliding window of the conversation
        
        This works by creating a contexts of a conversation by sliding a window of size `window_size`. Each context
        begins begins with a speaker and must end with a another speaker at least before the window_size is reached.
        """

        # Shuffle along each window_size throughout the conversation
        for i in range(len(self.conversation) - window_size):
            # The first user in this window
            user_1 = self.conversation.iloc[i]['user']

            # Is there a second within the window? If so, who is it?
            user_2 = set(self.conversation.iloc[i:i+window_size]['user'].unique()) - set([user_1])[0]

            # If there is a real back-and-forth conversation, then we can create a context
            if user_2:
                # Take the first speaker and their messages well as the preceeding messages from the second speaker
                # Keep in mind that we want to truncate so that the original speaker does not end up in the output
                input_text = " ".join(self.conversation.iloc[i:i+window_size]['message'].tolist())
                output_text = self.conversation.iloc[i+window_size]['message']
    
        return pd.DataFrame([])