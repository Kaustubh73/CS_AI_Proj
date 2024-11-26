import os
import redis
import json
import time
from request_processor import RequestProcessor
import pandas as pd
from datetime import datetime, timedelta

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
        
        self.ddos_window = 2
        self.csv_path = "results.csv"
        self.ddos_request_threshold = 5
        
        print(f"Redis Worker initialized. Listening on queue: {Config.QUEUE_NAME}")
    
    
    # Add the ipaddress here
    
    def send_alert(result, ddos_attack = False, ddos_ip = None):
        # cookie = result[1]['cookie']
        # print(f"ALERT: Suspicious request detected for session ID: {cookie}")
        # # Convert to JSON
        # cookie = json.dumps(cookie)
        # # Send it to local host port 3000
        # # You can replace this with your own alerting mechanism
        # requests.post("http://localhost:3000/alert", json=cookie)
        
        # Extract the session cookie
        cookie = result[1]['cookie']
        print(f"ALERT: Suspicious request detected for session ID: {cookie}")
        
        # Create the JSON payload
        alert_payload = {"cookie": cookie}
        
        # Add the ddos_ip if the attack is flagged
        if ddos_attack:
            alert_payload["ddos_ip"] = ddos_ip
        
        # Convert to JSON
        alert_payload_json = json.dumps(alert_payload)
        
        # Send it to localhost port 3000
        response = requests.post("http://localhost:3000/alert", json=alert_payload_json)
        
        if response.status_code == 200:
            print("Alert sent successfully!")
        else:
            print(f"Failed to send alert: {response.status_code}, {response.text}")
        
        
    # Function to detect DDOS
    def DDOS_detect(self, parsed_request):
        
        ddos_attack = False
        ddos_ip = None
        
        df = pd.read_csv(self.csv_path, parse_dates=["timestamp"])
        
        current_time = datetime.now()
        start_time = current_time - timedelta(seconds=self.time_window)
        
        recent_requests = df[(df["timestamp"] >= start_time) & (df["timestamp"] <= current_time)]
        
        # Checking for the matched ip addresses with the new requests
        ip_matches = recent_requests[recent_requests["features"].apply(lambda x: x["IP"] == parsed_request["IP"])]

        ip_counts = ip_matches.shape[0]
        
        if ip_counts > self.ddos_request_threshold:
            ddos_attack = True
            ddos_ip = parsed_request["IP"]

        return ddos_attack, ddos_ip
        
    def start(self):
        while True:
            try:
                # Block and wait for requests from Redis queue
                _, request_data = self.redis_client.brpop(Config.QUEUE_NAME)
                
                try:              
                    parsed_request = json.loads(request_data)
                    
                    result = self.processor.process_request(parsed_request)
                    
                    features = result[1]
                    
                    ddos_attack, ddos_ip = self.DDOS_detect(features)
                    
                    print("Processed request:", result)
                    # If it is a suspicious request, send an alert (DOS attack or anomalous request)
                    
                    if result[0] == 1 or ddos_attack == True:
                        self.send_alert(result, ddos_attack, ddos_ip)
                        print("ALERT: Suspicious request detected.")
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

