FROM pytorch/pytorch:latest

ADD . .

ENV OPENAI_API_KEY=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

RUN pip3 install -r requirements.txt
RUN pip3 install transformers


CMD [ "python", "./main.py" ]