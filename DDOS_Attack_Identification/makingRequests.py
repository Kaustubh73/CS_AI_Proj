import requests

url = "http://172.21.129.37:8080/data"
data = {"key1": "value1"}  # Replace with your payload

response = requests.get(url, data=data)

print("Response Status Code:", response.status_code)
print("Response Text:", response.text)