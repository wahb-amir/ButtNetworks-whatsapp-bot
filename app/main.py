from fastapi import FastAPI
from app.api.v1.webhook import router as webhook_router

app = FastAPI(title="WhatsApp RAG Bot")


app.include_router(
    webhook_router, 
    prefix="/api/v1/webhook", 
    tags=["WhatsApp"]
)

@app.get("/")
async def root():
    return {"status": "online", "message": "RAG Bot Server is running"}