import requests

url = "http://localhost:3000/tools/call"
data = {
    "tool": "scraper_tool",
    "input": {
        "url": "https://example.com"
    }
}

response = requests.post(url, json=data)
print("Output:", response.json())
