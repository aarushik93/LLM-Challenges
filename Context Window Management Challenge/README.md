# OpenAI Chat CLI Project

This project is a simple command-line interface for having a conversation with OpenAI's GPT-4 model.

## Setup

1. Install Docker on your machine.

## Running the Project

First build the docker image (folder location: Context Window Management Challenge )

```
docker build . -t llm-memory 
```
Next run in interactive mode so you can input text

```
docker run -it llm-memory 
```

Type your messages into the CLI and receive responses from the AI. Type 'quit' to end the conversation.