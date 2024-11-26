from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


todos = [
    {
        "id": "1",
        "item": "Read a book."
    },
    {
        "id": "2",
        "item": "Cycle around town."
    }
]


app = FastAPI()

origins = [
#    "192.168.105.73:3000",
#    "http://192.168.105.73:3000",    
    "http://localhost:3000",
    "localhost:3000"
]


app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
)

"""
import httpx

# Replace with the URL of the logger website
LOGGER_WEBSITE_URL = "https://example-logger-website.com/log"

@app.middleware("http")
async def log_request(request: Request, call_next):
    # Read the request body
    body = await request.body()
    
    # Log the request data to the external logger
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                LOGGER_WEBSITE_URL,
                json={
                    "client_ip": client_host
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "body": body.decode("utf-8") if body else None,
                },
            )
        except Exception as e:
            print(f"Failed to log request: {e}")

    # Proceed with the original request
    response = await call_next(request)
    return response

"""


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}


@app.get("/todo", tags=["todos"])
async def get_todos() -> dict:
    return { "data": todos }


@app.post("/todo", tags=["todos"])
async def add_todo(todo: dict) -> dict:
    todos.append(todo)
    return {
        "data": { "Todo added." }
    }


@app.put("/todo/{id}", tags=["todos"])
async def update_todo(id: int, body: dict) -> dict:
    for todo in todos:
        if int(todo["id"]) == id:
            todo["item"] = body["item"]
            return {
                "data": f"Todo with id {id} has been updated."
            }

    return {
        "data": f"Todo with id {id} not found."
    }


@app.delete("/todo/{id}", tags=["todos"])
async def delete_todo(id: int) -> dict:
    for todo in todos:
        if int(todo["id"]) == id:
            todos.remove(todo)
            return {
                "data": f"Todo with id {id} has been removed."
            }

    return {
        "data": f"Todo with id {id} not found."
    }
