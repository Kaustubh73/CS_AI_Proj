import os
import redis
import json
import time
from request_processor import RequestProcessor
from config import Config

class RedisWorker:
    def __init__(self, model_path):
        self.processor = RequestProcessor(model_path=model_path)
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            decode_responses=True
        )
        print(f"Redis Worker initialized. Listening on queue: {Config.QUEUE_NAME}")

    def start(self):
        while True:
            try:
                # Block and wait for requests from Redis queue
                _, request_data = self.redis_client.brpop(Config.QUEUE_NAME)
                
                try:
                    parsed_request = json.loads(request_data)
                    result = self.processor.process_request(parsed_request)
                    print("Processed request:", result)
                    
                    # Analyze 
                    # Optionally, you can store results or send alerts
                    self._handle_result(result)
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON in queue: {request_data}")
                except Exception as e:
                    print(f"Error processing request: {e}")
                
            except redis.exceptions.ConnectionError:
                print("Redis connection lost. Reconnecting...")
                time.sleep(5)
            except Exception as e:
                print(f"Unexpected error in worker: {e}")
                time.sleep(5)

    def _handle_result(self, result):
        """
        Optional method to handle processing results
        Can be used to:
        - Log suspicious requests
        - Send alerts
        - Store in a database
        """
        predicted_class, features = result
        if predicted_class == 1:  # Suspicious request
            print(f"ALERT: Suspicious request detected.")
            # Add your alert mechanism here (e.g., send email, log to file, etc.)
        # Store features and result in a csv file
        # If csv file doesn't exist, create it and write the header
        if not os.path.exists(Config.RESULT_CSV):
            with open(Config.RESULT_CSV, 'w') as f:
                f.write("timestamp, features, predicted_class\n")
        with open(Config.RESULT_CSV, 'a') as f:
            # time stamp in real time - date and time
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp}, {features}, {predicted_class}\n")        
        

def main():
    worker = RedisWorker(model_path=Config.MODEL_PATH)
    worker.start()

if __name__ == "__main__":
    main()

