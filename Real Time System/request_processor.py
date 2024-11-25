from datetime import datetime, timedelta
import json
import onnxruntime as ort
import numpy as np
from feature_extractor import FeatureExtractor
import redis
from config import Config

class RequestProcessor:
    def __init__(self, model_path='random_forest_hijacking_model.onnx'):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            decode_responses=True
        )

        self.feature_extractor = FeatureExtractor()
        
        # Initialize ONNX Runtime Inference Session
        self.model = ort.InferenceSession(model_path)
        
        # Get input and output names
        self.input_name = self.model.get_inputs()[0].name
        self.output_name = self.model.get_outputs()[0].name
        
        # Session windows to store historical data
        self.session_windows = {}
        
    def process_request(self, request_data):
        # Parse raw HTTP request data
        parsed_request = {
            'timestamp': datetime.now().isoformat(),
            'method': request_data.get('method', 'GET'),
            'url': request_data.get('url', ''),
            'cookie': request_data.get('headers', {}).get('Cookie', ''),
            'content_length': request_data.get('headers', {}).get('Content-Length', 0),
            'payload': request_data.get('payload', '')
        }
        session_id = parsed_request['cookie']
        print("SESSION ID",session_id)
        if session_id.startswith('JSESSIONID='):
            session_id = session_id[11:]
        # Get historical data for the session
        print("SESSION WINDOWS",self.session_windows)
        if session_id not in self.session_windows:
            self.session_windows[session_id] = []
        
        # Update session window
        print("updating session window")
        self.session_windows[session_id].append(parsed_request)
        print("Clean old data")
        self._clean_old_data(session_id)
        print("Cleaned old data")

        # Extract features
        features = self.feature_extractor.extract_features(parsed_request,self.session_windows[session_id][:-1])
        print("FEATURES",features)
        # Get numeric features for model prediction
        numeric_features = self.feature_extractor.get_numeric_features(features)
        print("NUMERIC FEATURES",numeric_features)
        # session_id = features['Cookie']
        
        # Reshape for ONNX model input (add batch dimension)
        input_data = numeric_features.reshape(1, -1)
        print("INPUT DATA",input_data)
        # Make prediction using ONNX Runtime
        predicted_class = self._predict(input_data)
        # Get prediction class and probability
        
        # Handle alerts if necessary
        if predicted_class == 1:  # Assuming 1 is the anomalous class
            self._trigger_alert(session_id, features)
        
        return predicted_class, features

    def _predict(self, input_data):
        """
        Run inference using ONNX model
        
        Args:
            input_data: Numeric features array
        Returns:
            Prediction results
        """
        print("INPUT DATA",input_data)
        print(self.output_name)
        # Run model inference
        raw_prediction = self.model.run(
            [self.output_name],
            {self.input_name: input_data}
        )
        print("RAW PREDICTION",raw_prediction)
        # Get predicted class and probabilities
        predicted_class = raw_prediction[0]        
        return predicted_class
    
    def _clean_old_data(self, session_id):
        current_time = datetime.now()
        print("CLEANING OLD DATA")
        window = self.session_windows[session_id]
        
        # Remove data older than WINDOW_TIME
        cutoff_time = current_time - timedelta(seconds=Config.WINDOW_TIME)
        print("CUTOFF TIME",cutoff_time)
        self.session_windows[session_id] = [
            req for req in window
            if datetime.fromisoformat(req['timestamp']) > cutoff_time
        ]
        print("CLEANED OLD DATA")

    def _trigger_alert(self, session_id, request_data):
        alert = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'request_data': request_data
        }
        # Publish alert to Redis channel
        self.redis_client.publish('security_alerts', json.dumps(alert))
