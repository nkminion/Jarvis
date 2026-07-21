# 🤖 AI Intent-Based Browser Agent

An AI-driven browser agent that performs automated web tasks based on natural language commands.  
This system integrates with the **Jarvis AI assistant** to execute tasks like searching, clicking, filling forms, and extracting data **without human input**.

---

## 📝 Overview
This project combines two main components:

1. **💡 Intent Classification**
   - Understands user goals from natural language input.
   - Produces structured JSON output containing the intent and associated entities.

2. **🕹️ AI Browser Agent**
   - Maps intents to browser actions automatically.
   - Executes tasks on the web without manual intervention.
   - Supports multi-step workflows and optional feedback extraction.

The combination enables automated execution of complex web tasks triggered via simple commands.

---

## ✨ Features
- 🗣️ Accepts natural language commands
- 🤖 Automatic intent classification
- 📦 Entity extraction for parameterized actions
- 🌐 Browser automation using **Playwright** or **Selenium**
- 🔗 Multi-step task execution
- 🛠️ Modular and extensible architecture
- 📄 Optional feedback or result extraction
- 🎙️ Voice output / narration (optional)
- 📸 Screenshots or data capture (optional)

---

## 🚀 Initial Actions / MVP
These are the first browser actions to implement:

| Category                | Actions                                                      |
|-------------------------|-------------------------------------------------------------|
| 🌐 **Navigation**        | Open URL, go back/forward, refresh                          |
| 🔍 **Search**            | Google/Wikipedia search, YouTube search                     |
| 🖱️ **Click / Interact**   | Click buttons, select dropdown, hover, scroll              |
| 📝 **Form Filling**      | Fill text inputs, select options, submit forms             |
| 📊 **Data Extraction**   | Extract text, tables, images from page                     |
| 💾 **Download**          | Download file or image                                      |
| 📢 **Browser Feedback**  | Screenshot, read page title, summarize content             |

> These actions form the foundation for multi-step tasks and advanced workflows.

---

## 🎯 Planned / Fun Features
- 🔗 Multi-step task automation (chain multiple actions)
- 🎙️ Voice narration of steps or results
- 📸 Screenshots or GIFs of task execution
- 🎉 Interactive or fun Easter eggs (memes, gifs, jokes)
- 🧠 Context-aware automation using previous intents

