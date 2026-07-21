# JARVIS - AI Chatbot Assistant

## Created By :- R. Neti

JARVIS is a **modular AI chatbot assistant** designed to understand user intents and extract relevant parameters from natural language queries. It uses **semantic embeddings** for intent recognition and **SpaCy + regex** for parameter extraction.

---

## Features

- **Intent Recognition**:  
  Classifies user input into predefined intents using **Sentence-BERT embeddings** (`all-MiniLM-L6-v2`) for semantic similarity.

- **Parameter Extraction**:  
  Extracts parameters like:
  - Artist names (`play_song`)  
  - Locations (`get_weather`)  
  - Event details (`add_event`)  
  - To-do tasks (`create_todo`)  
  - Mathematical expressions (`calculate`)  

- **Interactive REPL**:  
  Simple command-line interface to chat and test intents.

- **Extensible Design**:  
  Easily add new intents and example phrases.

---
# Intent Recognition Summary

- **Goal**: Identify the user’s intention from a natural language query (e.g., play a song, tell a joke, get weather).

- **Method**:

    - Predefine intents with example phrases in a dictionary (intents.py).

    - Use Sentence-BERT (all-MiniLM-L6-v2) to generate embeddings for each example phrase.

    - Precompute embeddings for all intents to speed up classification.

    - Classify new user input by computing cosine similarity between the input embedding and all intent example embeddings.

    - Select the intent with the highest similarity score. Optionally, ignore matches below a threshold.

- **Advantages**:

    - Handles semantic similarity, not just exact keyword matching.

    - Can recognize variations in phrasing (e.g., “Play some music” ≈ “Put on a song”).

    - Easy to extend by adding new intents or examples.

    - Tools Used:

    - sentence-transformers for embeddings

    - cosine similarity (util.cos_sim) for comparing user input to intent examples

# Project Structure
```
Intent_Recognition/
│
├─ intents.py           # Define all intents and example phrases
├─ intent_classifier.py # Load model, compute embeddings, classify intent
├─ param_extractor.py   # Extract parameters from user input
├─ main.py              # Main loop / chatbot REPL
├─ requirements.txt     # Python dependencies
└─ .gitignore           # Ignore venv, temp files, etc.
```
# Installations

1. Clone the repository:

```bash
git clone https://github.com/Ajay-Kumar-Prasad/jarvis.git
cd jarvis/Intent_Recognition
```

2. Create and activate a Python virtual environment:
```
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

3. Install dependencies:
```
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

# Run the chatbot in your terminal:

```
python main.py
```
# Examples
```
You: Play a song by BTS
Intent: play_song (score=0.87), Params: {'artist': 'BTS'}

You: Add lunch with John at 1pm
Intent: add_event (score=0.92), Params: {'datetime': '1pm', 'event': 'Add lunch with John'}
```

# Adding New Intents

1. Open intents.py.
2. Add a new key-value pair:

```
"new_intent": [
    "Example phrase 1",
    "Example phrase 2"
]
```
3. Re-run intent_classifier.py to precompute embeddings.

## Technologies Used

Python 3.10+
Sentence Transformers
SpaCy
PyTorch
