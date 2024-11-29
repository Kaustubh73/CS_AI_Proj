# send_to_queue.py
import redis
import json

def send_request_to_queue():
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    for i in range(10):
        test_request = {
            
            'method': 'GET',
            'url': 'http://localhost:8080/tienda1/publico/anadir.jsp?id=1&nombre=Jam%F3n+Ib%E9rico&precio=39&cantidad=41&B1=A%F1adir+al+carrito',
            'headers': {
                'IP': '45245',
                'Content-Length': '0',
                'Cookie': 'JSESSIONID=54E25FF4B7F0E4E855B112F882E9EEA5',
                'User-Agent': 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.8 (like Gecko)',
                'Target-Class': '0'
            },
            'payload': '',
        }

        # Push to Redis queue
        redis_client.lpush('request_queue', json.dumps(test_request))
        print("Request sent to queue successfully!")


if __name__ == "__main__":
    send_request_to_queue()