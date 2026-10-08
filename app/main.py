from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI(title="hello-world-cicd")


@app.get("/hello", response_class=PlainTextResponse)
def hello() -> str:
    return "Hello World"
