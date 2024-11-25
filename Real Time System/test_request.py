# send_to_queue.py
import redis
import json

def send_request_to_queue():
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    test_request = {
        
        'method': 'GET',
        'url': 'http://localhost:8080/tienda1/publico/anadir.jsp?id=2&nombre=Jam%F3n+Ib%E9rico&precio=85&cantidad=%27%3B+DROP+TABLE+usuarios%3B+SELECT+*+FROM+datos+WHERE+nombre+LIKE+%27%25&B1=A%F1adir+al+carrito',
        'headers': {
            'Content-Length': '0',
            'Cookie': 'JSESSIONID=B92A8B48B9008CD29F622A994E0F650D',
            'User-Agent': 'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.8 (like Gecko)',
        },
        'payload': '',
    }

    # Push to Redis queue
    redis_client.lpush('request_queue', json.dumps(test_request))
    print("Request sent to queue successfully!")


if __name__ == "__main__":
    send_request_to_queue()