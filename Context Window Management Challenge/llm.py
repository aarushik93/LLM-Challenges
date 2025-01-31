from openai import OpenAI
from transformers import pipeline


class llm:
    def __init__(self):
        self.full_message_history = []  # This is the full conversation history https://platform.openai.com/docs/api-reference/chat/object .
        self.client = OpenAI(
            api_key='')  # <== Put API key provided in the challenge email here.
        self.DEBUG = True  # Set this to True to see the context window being sent to the LLM.
        self.max_context_length = 4096
        self.summarizer = pipeline("summarization")
        if self.client.api_key == '':
            raise ValueError(
                "\033[91m Please enter the OpenAI API key which was provided in the challenge email into llm.py.\033[0m")

    def manage_context_window(self):
        # Define thresholds for different tiers
        recent_threshold = 10  # Most recent 10 messages are kept as-is
        older_threshold = 30  # Messages from 11 to 30 are lightly summarized
        oldest_threshold = len(self.full_message_history) - older_threshold  # The rest are heavily summarized

        recent_messages = self.full_message_history[-recent_threshold:]
        older_messages = self.full_message_history[
                         -older_threshold:-recent_threshold] if older_threshold > recent_threshold else []
        oldest_messages = self.full_message_history[:oldest_threshold]

        # Summarize older and oldest messages
        if older_messages:
            summarized_older = self.summarize_context(older_messages, max_length=80, min_length=20)
            recent_messages = summarized_older + recent_messages

        if oldest_messages:
            summarized_oldest = self.summarize_context(oldest_messages, max_length=50, min_length=10)
            recent_messages = summarized_oldest + recent_messages

        return recent_messages

    def summarize_context(self, messages, max_length=100, min_length=30):
        """
        Summarize the given messages, including both user and assistant interactions,
        using a pre-trained model.

        Args:
            messages (list): Messages to be summarized, including both user and assistant messages.
            max_length (int): Maximum length of the summary.
            min_length (int): Minimum length of the summary.

        Returns:
            list: Summarized content.
        """
        # Combine all messages (both user and assistant) into a single string for summarization
        full_conversation = ' '.join([msg['content'] for msg in messages])

        # Summarize the full conversation
        summary = self.summarizer(full_conversation, max_length=max_length, min_length=min_length, do_sample=False)
        summarized_text = summary[0]['summary_text']

        # Return the summary as a single 'assistant' message
        return [{'role': 'assistant', 'content': summarized_text}]

    def send_message(self, prompt: str, role: str = 'user', json_response: bool = False):
        """
        This function adds the provided prompt to the existing message history, creating a context window for the LLM.
        This context window is forwarded to the LLM. The received response from the LLM is then appended to the message history and returned.

        Args:
            prompt (str): The message content to be sent to the LLM.
            role (str, optional): The role of the speaker. Defaults to 'user'.
                - 'user': Represents the user speaking.
                - 'assistant': Represents the AI assistant speaking.
                - 'system': Represents instructions or context for the AI.
            json_response (bool, optional): Specifies whether the response should be returned as JSON. Defaults to False. If True, schema must be specified.

        Returns:
            str: The AI's response to the message.

        Raises:
            ValueError: If an invalid role is provided.

        Note:
            - The `context_window` is currently using a primitive way of managing conversation history, simply keeping only the last 4 messages.

        Example:
            >>> helper = OpenAIHelper()
            >>> response = helper.send_message("Hello, how can I assist you?")
            >>> print(response)
            "Sure, I can help you with that!"
        """
        if role == 'user':
            self.full_message_history.append({'role': 'user', 'content': prompt})
        elif role == 'assistant':
            self.full_message_history.append({'role': 'assistant', 'content': prompt})
        elif role == 'system':
            self.full_message_history.append({'role': 'system', 'content': prompt})
        else:
            raise ValueError("Invalid role provided. Valid roles are 'user', 'assistant', or 'system'.")

        context_window = self.manage_context_window()

        if self.DEBUG:
            print(f"\033[91m  Context sent to LLM:\n  {context_window} \033[0m")

        # Send the message to the LLM and get the response.
        response = self.gpt4_conversation(context_window)

        ai_message = response.choices[0].message.content

        self.full_message_history.append({'role': 'assistant', 'content': ai_message})
        return ai_message

    # ~#~#~# Methods for interacting with OpenAI's Chat Completions EndPoint - You probably won't need to edit anything below this line. #~#~#~#
    def gpt4_conversation(self, messages: list, json_response: bool = False, model: str = "gpt-4-1106-preview"):
        """
        Initiates a conversation with the GPT-4 language model using the specified parameters.

        This method sends a list of messages to the GPT-4 model and retrieves the model's response. It allows configuration
        of the model and response format.

        Args:
            messages (list): A list of message objects (dicts) that form the conversation history (context window).
            json_response (bool, optional): If True, forces the response to be in JSON format. Requires a defined response schema somewhere in the messages.
                                            Defaults to False.
            model (str, optional): The specific GPT-4 model version to be used for the conversation. Defaults to "gpt-4-1106-preview".

        Returns:
            response: The response from the GPT-4 model. Format: https://platform.openai.com/docs/api-reference/chat/object

        Raises:
            ValueError: If the combined token count of the response and context exceeds the 4096 token limit.

        Note:
            - The 'temperature' parameter controls the randomness of the model's responses. A higher value increases randomness.
            - The 'max_tokens' parameter sets the limit for the response token count. Exceeding this limit triggers a ValueError.
            - The method currently imposes a shorter context window limit for this specific implementation.

        Example:
            >>> response = gpt4_conversation([{'role': 'user', 'content': 'Hello, AI!'}])
            >>> print(response)
        """
        # Initialize the conversation with the GPT-4 model
        response = self.client.chat.completions.create(
            model=model,  # Specifies the GPT-4 model version
            temperature=0.79,  # Sets the AI's creativity level. Higher values increase randomness.
            max_tokens=4096,  # Sets the maximum number of tokens in the AI's response.
            response_format={"type": "json_object"} if json_response else None,  # Optional JSON response format
            messages=messages  # The conversation history to be sent to the model
        )

        # Check if the total token usage exceeds the limit
        # DO NOT CHANGE THIS - This is a requirement for the challenge.
        if response.usage.total_tokens > 4096:
            raise ValueError(
                "CHALLENGE CONTEXT WINDOW EXCEEDED: The context window now exceeds the 4096 token limit. Please try again with a shorter prompt.")

        return response


def gpt4_one_shot(self, system_prompt: str, user_prompt: str, json_response: bool = False,
                  model: str = "gpt-4-1106-preview"):
    """
    Executes a one-shot completion with the GPT-4 language model, using both a system and a user prompt.

    This method is designed for scenarios where a single interaction with the GPT-4 model is required, rather than a
    continuous conversation. It allows specifying both a system-level and a user-level prompt to guide the model's response.

    Args:
        system_prompt (str): The system-level prompt that sets the context or instructions for the model.
        user_prompt (str): The user's input or question to the model.
        json_response (bool, optional): If True, forces the response to be in JSON format. Requires a defined response schema.
                                        Defaults to False.
        model (str, optional): The specific GPT-4 model version to be used for the completion. Defaults to "gpt-4-1106-preview".

    Returns:
        str: The content of the model's response message as a string.

    Raises:
        ValueError: If the combined token count of the response and prompts exceeds the 4096 token limit.

    Note:
        - The 'temperature' parameter influences the model's creativity and unpredictability.
        - The 'max_tokens' parameter sets a limit on the response size.
        - This method is suitable for tasks like generating content, answering questions, or other one-off tasks.

    Example:
        >>> response = gpt4_one_shot("Always respond in French.", "Tell a one scentence poem about a robot's adventure.")
        >>> print(response)
        "Un robot solitaire, vers les étoiles il vole, son aventure commence, un rêve qui se dévoile."
    """
    # Initialize a one-shot completion with the GPT-4 model
    response = self.client.chat.completions.create(
        model=model,  # Specifies the GPT-4 model version
        temperature=0.79,  # Sets the AI's creativity level
        max_tokens=4096,  # Limits the response token count
        response_format={"type": "json_object"} if json_response else None,  # Optional JSON response format
        messages=[
            {"role": "system", "content": system_prompt},  # System-level context or instruction
            {"role": "user", "content": user_prompt}  # User input or question
        ]
    )

    # Check if the total token usage exceeds the limit
    # DO NOT CHANGE THIS - This is a requirement for the challenge.
    if response.usage.total_tokens > 4096:
        raise ValueError(
            "CHALLENGE CONTEXT WINDOW EXCEEDED: The context window now exceeds the 4096 token limit. Please try again with a shorter prompt.")

    return response.choices[0].message.content