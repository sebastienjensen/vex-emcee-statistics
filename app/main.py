from fastapi import FastAPI

app = FastAPI(
    title = "MCDb API",
    version = "0.1.0"
)

@app.get("/")
async def root():
    return "OK"