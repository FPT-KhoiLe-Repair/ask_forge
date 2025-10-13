import uvicorn
from fastapi import FastAPI
app = FastAPI()

@app.get("/api/hello")
async def hello():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app)