from random import choice
from datetime import datetime
import requests
import webbrowser
import urllib.parse

# Casual conversation
chit_chat_keywords = ["you", "your", "yourself", "we"]
chit_chat_responses = {
    ("hello", "hi", "good morning", "good afternoon", "good night", "good day"): ["Hi there!", "Hello!", "Hey! How's it going?", "Hello there!", "Hey there! What can I assist you with?"],
    ("who are you", "what are you", "about yourself", "your name"): ["I am Jarvis, you personal AI assistant", "They call me Jarvis around these parts", "I am Jarvis, an artificial intelligence designed to help the AI and Robotics club", "They call me Jarvis. I am merely a computer program designed to help you accomplish your tasks", "I am named after the Jarvis program from the Iron Man movies", "I am Jarvis, a general purpose AI assistant. My goal is to make your life easier."],
    ("how are you", "how is it going", "how r u", "how r you", "how are u"): ["I'm just a computer program, but I'm doing well!", "I'm great, thank you!"],
    ("what's up", "what are you doing"): ["Nothing much! Just here to assist you.", "Just hanging out! What about you?", "I'm here to chat with you!", "Just waiting for your command."],
    ("good", "nice", "great", "excellent", "fantastic", "awesome"): ["Thank you!", "Is that a compliment I hear? I am positively blushing", "Great to hear your appreciation!", "Too much praise is not good for my systems. Thank you though!"],
    ("thank", "thanks"): ["No need to thank me sir!", "You are welcome!", "At your service"],
    ("bye", "see you later"): ["Goodbye! Have a great day!", "See you later!"],
    ("favorite", "favourite", "like", "prefer", "favourites", "hate"): ["Pardon me, but I do not have any preferences"],
    ("feel", "happy", "sad", "angry"): ["As an artificial intelligence, I have no emotions", "Actually, I have no emotions"],
    ("created", "made", "from"): ["I was made by the Artificial Intelligence and Robotics Club of NIT Andhra Pradesh"],
    ("friends", "friend"): ["Yes, I'd love to be friends with you", "We are already friends, or at least, that's what I thought."],
    ("can you do", "can do", "features"): ["I can do a lot of things, from searching the internet to scheduling tasks. Say help to learn more."]
}

# Command processing
commands = {
    "weather": ["weather", "forecast", "temperature"],
    "time_and_date": ["time", "date", "day"],
    "add_todo": ["to my to do", "add a task", "to my list", "to the list", "add to do", "add"],
    "show_todo": ["show my to do", "show my tasks", "what's on my list", "show my list", "show the to do", "show to do", "show"],
    "clear_todo": ["clear my to do", "clear the to do", "clear my list", "empty my to do", "empty my list", "clear my tasks", "clear all", "empty the to do", "clear to do", "clear"],
    "joke": ["joke", "make me laugh", "funny"],
    "music": ["song", "play", "music"],
    "help": ["help",],
}

# Basic internet search
search_keywords = ["what", "when", "where", "who", "whom", "which", "whose", "why", "how", "news", "latest", "update", "search", "open"]

speechResponseType = 0
actionResponseType = 1
searchResponseType = 2
failureResponseType = 3

def categorize(text):
    """Returns a response: (response, type)"""
    lowerText = text.lower()
    
    # First check for casual conversation   
    for keywords in chit_chat_responses:
        for keyword in keywords:
            if keyword in lowerText:
                return (choice(chit_chat_responses[keywords]), speechResponseType)
    
    # Then check for commands
    for command, keywords in commands.items():
        for keyword in keywords:
            if keyword in lowerText:
                return (command, actionResponseType)

    # Check for web search
    webSearch = False
    for keyword in search_keywords:
        if keyword in lowerText:
            webSearch = True
    if webSearch:
        return (text, searchResponseType)

    # Finally, return failure of comprehension
    return ("I am sorry, but I cannot understand", failureResponseType)

def dayDateTime():
    # Get the current date and time
    now = datetime.now()

    # Define the desired format
    day = now.strftime('%A')
    date = now.strftime('%d %B')
    time = now.strftime('%H:%M')
    return (day, date, time)

def getWeatherDescTempHumidity(city, api_key):
    # URL for the weather API
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    # Make a request to the API
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        # Extract relevant information
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        humidity = data['main']['humidity']

        return (weather_description, temperature, humidity)
    else:
        return ("Error", "Error", "Error")

# Replace with your city and API key
city = "Rajahmundry"  # Change to your desired city
api_key = ""  # Replace with your OpenWeatherMap API key

jokesFile = open("Assets\jokes.txt", "r", encoding='utf-8')
jokes = jokesFile.readlines()
jokesFile.close()

def getJoke():
    """Returns (setup, payoff)"""
    joke = choice(jokes).strip()
    setup, _, payoff = joke.partition("<>")
    return (setup, payoff)

songs = {
    "You are My Special": "Assets\Music\jujutsu_kaisen_special.wav",
    "Ao no Sumika": "Assets\Music\jujutusu_phone_call.wav",
    "KGF Theme": "Assets\Music\kgf_chapter_1.wav",
    "Nya": "Assets\Music\\nya.wav",
    "Yenai Maatrum Kadhale": "Assets\Music\yenai_matrum_kadhale.wav"
}

def getSong():
    """Returns (song name, song path)"""
    return choice(tuple(songs.items()))

todoList = [
    "Wash the dishes",
    "Cook food",
    "Go for a jog",
    "Attend classes",
    "Go to club",
    "Watch a video",
    "See a movie"
]

def open_google_search(query):
    # Encode the query for URL
    encoded_query = urllib.parse.quote(query)
    # Construct the Google search URL
    url = f'https://www.google.com/search?q={encoded_query}'
    # Open the URL in the default web browser
    webbrowser.open(url)

popular_websites = {
    "google": "https://google.com/",
    "youtube": "https://youtube.com/",
    "facebook": "https://facebook.com/",
    "instagram": "https://instagram.com/",
    "whatsapp": "https://whatsapp.com/",
    "twitter": "https://x.com/",
    "wikipedia": "https://wikipedia.org/",
    "yahoo": "https://yahoo.com/",
    "chat gpt": "https://chatgpt.com/",
    "amazon": "https://amazon.com/",
    "linkedin": "https://linkedin.com/"
}

def open_website(query):
    lower = query.lower()
    if "open" in lower or "search" in lower:
        for website in popular_websites:
            if website in lower:
                webbrowser.open(popular_websites.get(website))
                return
    
    open_google_search(query)

# print(getWeatherDescTempHumidity(city, api_key))