import os
import redis
import json
import time
from request_processor import RequestProcessor

from config import Config
import requests
class RedisWorker:
    def __init__(self, model_path):
        self.processor = RequestProcessor(model_path=model_path)
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            decode_responses=True
        )
        print(f"Redis Worker initialized. Listening on queue: {Config.QUEUE_NAME}")
    
    
    # Add the ipaddress here
    
    # def send_alert(result):
    #     cookie = result[1]['cookie']
    #     print(f"ALERT: Suspicious request detected for session ID: {cookie}")
    #     # Convert to JSON
    #     cookie = json.dumps(cookie)
    #     # Send it to local host port 3000
    #     # You can replace this with your own alerting mechanism
    #     requests.post("http://localhost:3000/alert", json=cookie)
        
    # Function to detect DDOS, needs to keep running in the background
    def DDOS_detect(self):
        # Function on the ipaddress, and the frequency of the requests
        
        # Input the csv
        
        # Make the calculations on the csv
        
        
        # Return the IP addresses to block
        return 0
    
        
    def start(self):
        while True:
            try:
                # Block and wait for requests from Redis queue
                _, request_data = self.redis_client.brpop(Config.QUEUE_NAME)
                
                try:
                    # Run the DDOS checker
                    
                    parsed_request = json.loads(request_data)
                    result = self.processor.process_request(parsed_request)
                    print("Processed request:", result)
                    # If it is a suspicious request, send an alert
                    # if result[0] == 1:
                        # send_alert(result)
                        # print("ALERT: Suspicious request detected.")
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
        predicted_class, features, target_class, predicted_prob = result
        if predicted_class == 1:  # Suspicious request
            print(f"ALERT: Suspicious request detected.")
            # Add your alert mechanism here (e.g., send email, log to file, etc.)
        # Store features and result in a csv file
        # If csv file doesn't exist, create it and write the header
        if not os.path.exists(Config.RESULT_CSV):
            with open(Config.RESULT_CSV, 'w') as f:
                f.write("timestamp, features, predicted_class, target_class, predicted_prob\n")
        
        # If csv file is empty, write the header
        if os.stat(Config.RESULT_CSV).st_size == 0:
            with open(Config.RESULT_CSV, 'a') as f:
                f.write("timestamp, features, predicted_class, target_class, predicted_prob\n")
        with open(Config.RESULT_CSV, 'a') as f:
            # time stamp in real time - date and time
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp}, {features}, {predicted_class}, {target_class}, {predicted_prob}\n")        
        

def main():
    worker = RedisWorker(model_path=Config.MODEL_PATH)
    worker.start()

if __name__ == "__main__":
    main()

