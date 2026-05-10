import requests

URL = "http://127.0.0.1:8000/api/v1/webhook/whatsapp"

payload = {
    "From": "whatsapp:+923001112233",
    "Body": "What is EcoLens project?",
    "MessageSid": "TEST123456"
}

res = requests.post(URL, data=payload)

print("Status:", res.status_code)
print(res.text)