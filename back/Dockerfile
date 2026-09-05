FROM python:3.14-slim

WORKDIR /

#COPY pyproject.toml requirements.txt ./
#RUN python -m pip install --no-cache-dir -r requirements.txt
RUN uv sync

#create a non root user to access the container 
RUN adduser -u 5678 —-disabled-password --gecos "" vscode

COPY . .

CMD ["python","server.py"]