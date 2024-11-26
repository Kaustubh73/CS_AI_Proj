from datetime import datetime
import re
from urllib.parse import urlparse, parse_qs
import numpy as np

class FeatureExtractor:
    def __init__(self):
        self.feature_names = [
            'Method', 'URL', 'Cookie', 'ContentLen', 'Payload', 'ReqLen', 'ArgLen', 'NumArgs', 'NumDigitsArgs', 
            'PathLen', 'NumLettersArgs', 'NumLettersPath', 
            'NumSpecialCharsPath', 'MaxByteValReq', 'Content_present', 'IP'
        ]

    def extract_features(self, request_data, historical_data):
        """
        Extract features from HTTP request data.
        
        Args:
            request_data: FastAPI Request object with additional metadata
        Returns:
            dict: Dictionary containing extracted features
        """
        print("REQUEST DATA",request_data)
        print("HISTORICAL DATA",historical_data)
        # Calculate time-based features
        # if historical_data:
        #     last_request = historical_data[-1]
        #     interval = (datetime.fromisoformat(request_data['timestamp']) - 
        #                datetime.fromisoformat(last_request['timestamp'])).total_seconds()
        #     user_agent_changed = request_data['user_agent'] != last_request['user_agent']
        #     ip_changed = request_data['ip_address'] != last_request['ip_address']
        # else:
        #     interval = 0
        #     user_agent_changed = False
        #     ip_changed = False

        # Initialize features dictionary
        features = {name: None for name in self.feature_names}
        url = request_data['url']
        payload = request_data['payload'] if request_data['payload'] else ''
        ip = request_data['ip']
        if '?' in url:
            url, url_payload = url.split('?', 1)
            payload = payload + '&' + url_payload if payload else url_payload
        
        length_of_request = len(url) + len(payload)
        
        url_args = re.findall(r'[?&]([^=&]+)=([^&]*)', url)
        payload_args = re.findall(r'([^=&]+)=([^&]*)', payload)
        
        length_of_arguments = sum(len(arg[1]) for arg in url_args + payload_args)
        number_of_arguments = len(url_args) + len(payload_args)
        number_of_digits_in_arguments = sum(len(re.findall(r'\d', arg[1])) for arg in url_args + payload_args)
        
        path = re.split(r'[?#]', url)[0]
        length_of_path = len(path)
        number_of_letters_in_arguments = sum(len(re.findall(r'[a-zA-Z]', arg[1])) for arg in url_args + payload_args)
        number_of_letter_chars_in_path = len(re.findall(r'[a-zA-Z]', path))
        number_of_special_chars_in_path = len(re.findall(r'[^a-zA-Z0-9]', path))
        max_byte_value_in_request = max(ord(char) for char in url + payload)
        
        # Remove 'JSESSIONID=' prefix from the Cookie value
        if request_data['cookie']:
            request_data['cookie'] = request_data['cookie'].replace('JSESSIONID=', '')
        
        # Store 0 for GET and 1 for POST in the Method column
        request_data['method'] = 0 if request_data['method'] == 'GET' else 1

        content_present = 1 if request_data['content_length'] else 0
        
        # Populate features dictionary
        features.update({
            'Method': 0 if request_data.get('method', 'GET') == 'GET' else 1,
            'URL': url,
            'Cookie': request_data.get('cookie', ''),
            'ContentLen': request_data.get('content_length', 0),
            'Payload': payload,
            'ReqLen': length_of_request,
            'ArgLen': length_of_arguments,
            'NumArgs': number_of_arguments,
            'NumDigitsArgs': number_of_digits_in_arguments,
            'PathLen': length_of_path,
            'NumLettersArgs': number_of_letters_in_arguments,
            'NumLettersPath': number_of_letter_chars_in_path,
            'NumSpecialCharsPath': number_of_special_chars_in_path,
            'MaxByteValReq': max_byte_value_in_request,
            'Content_present': content_present,
            'IP': ip
        })

        # Add Content_present feature
        
        return features

    def get_numeric_features(self, features):
        """
        Convert features to numeric array for model input.
        
        Args:
            features: Dictionary of extracted features
        Returns:
            numpy.ndarray: Array of numeric features in the correct order for model input
        """
        # Ensure the order matches the training data
        numeric_features = [
            features['Method'],
            features['ReqLen'],
            features['ArgLen'],
            features['NumArgs'],
            features['NumDigitsArgs'],
            features['PathLen'],
            features['NumLettersArgs'],
            features['NumLettersPath'],
            features['NumSpecialCharsPath'],
            features['MaxByteValReq'],
            features['Content_present']
        ]
        return np.array(numeric_features, dtype=np.float32)
