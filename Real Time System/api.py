from fastapi import FastAPI, Request
import uvicorn
from request_processor import RequestProcessor
from config import Config

app = FastAPI()
processor = RequestProcessor(model_path=Config.MODEL_PATH)

@app.post("/alert")
async def analyze_request(request: Request):
    body = await request.body()
    raw_request = {
        'method': request.method,
        'url': str(request.url),
        'headers': dict(request.headers),
        'payload': body.decode() if body else '',
    }
    
    predicted_class, risk_score, features = processor.process_request(raw_request)
    
    return {
        'predicted_class': int(predicted_class),
        'risk_score': float(risk_score),
        'is_suspicious': predicted_class == 1,
        'features': features
    }

# Send 
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
