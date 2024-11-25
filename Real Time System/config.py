import os

class Config:
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    QUEUE_NAME = 'request_queue'
    WINDOW_SIZE = 10  # Number of requests to analyze together
    WINDOW_TIME = 300  # Time window in seconds (5 minutes)
    MODEL_PATH = 'random_forest_hijacking_model.onnx'
    ALERT_THRESHOLD = 0.7
    RESULT_CSV = 'results.csv'
