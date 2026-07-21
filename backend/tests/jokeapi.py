import requests

url = "https://jokes-always.p.rapidapi.com/common"

headers = {
	"x-rapidapi-key": "c7a8094621mshee7e9825a4c41e0p18a831jsn180b0072883d",
	"x-rapidapi-host": "jokes-always.p.rapidapi.com"
}

response = requests.get(url, headers=headers)

print(response.json())