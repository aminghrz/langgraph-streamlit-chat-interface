# 🦜 LangGraph Streamlit Chat Interface

*A simple, flexible, and lightweight Streamlit chat UI for LangGraph agents – ready for your custom workflows!*

---

## Overview

**LangGraph Streamlit Chat Interface** is a minimal, developer-friendly Streamlit app for chatting with any [LangGraph](https://github.com/langchain-ai/langgraph) workflow. With persistent thread memory, customizable API settings, and a clean experience, it’s perfect for demos, prototyping, and adapting to your own agent architectures.

![Chat Interface](/img/1.png)

### Why Use This App?

- 🚀 **Simplicity**: No user authentication, no web search, and no complex setup—just chat.
- 🪶 **Lightweight**: Minimal dependencies; quick, portable one-file SQLite persistence.
- 🎛️ **Flexible**: Can host any LangGraph agent; easily plug in your own graphs.
- 🧩 **Adaptable**: Starting point for your next Streamlit+LangGraph project.
- 💲 **Free and Open Source**!

*Looking for a more powerful, feature-rich solution?*  
👉 **Check out [LangChit](https://github.com/aminghrz/LangChit) for full user/auth, dual-layer persistent memory, web search, and more!**


---

## Features

- **Chat with LangGraph Agent**: Integrates your LangGraph's conversational agent in Streamlit.
- **Persistent Memory**: Each thread's conversation history and summary saved via SQLite.
- **Multi-Thread Management**: Switch between conversations, with full message history.
- **API Endpoint Flexibility**: Set your own base URL, API key, and choose any OpenAI-compatible model from your provider.
- **No External Database Needed**: Everything stored locally using a single SQLite file.
- **Easy Adaptation**: Designed for quick graph replacement—swap in your tools/nodes/workflows in `graph.py`.


---

## Quick Start

1. **Clone** the repository:
    ```bash
    git clone https://github.com/aminghrz/langgraph-streamlit-chat-interface.git
    cd langgraph-streamlit-chat-interface
    ```
2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3. **Run the Streamlit app**:
    ```bash
    streamlit run app.py
    ```
4. In the sidebar, enter your **API key** and **endpoint URL** (works with OpenAI or any compatible provider).
5. **Pick a model**, start a new thread, and chat away!


---

## Usage

- **Set API Settings**: In the sidebar, enter your API Key, Base URL and choose an available model. Save it!
- **Start or Select a Thread**: Use the sidebar to create a new chat or switch between past threads.
- **Chat**: Type your question or message in the chat box and interact with your agent.
- **Persistent State**: Thread history and summaries are automatically saved; pick up where you left off anytime.

---

## Architecture

- **LangGraph Agent**: Easily customizable in `graph.py`
- **Checkpointer**: Uses SQLite for persistent conversation memory
- **Streamlit UI**: Minimal, with no authentication layer by default
- **Plug-and-Play**: Tweak or replace the graph definition to inject custom tools, workflows, or multi-turn behaviors

---

## How to Customize

Adapting to your own LangGraph agent is simple:

- Change or expand the agent’s graph structure in [`graph.py`](graph.py).
- Add any tools, logic nodes, or memory managers you need.
- UI is in [`app.py`](app.py) and can easily be extended with new Streamlit components.

---

## Want More Features?

This app is the **bare-bones foundation** for quickly plugging in any LangGraph agent.

For a fully-fledged version with:
- User authentication & API key vault
- Dual-layer (thread + user/global) persistent memory
- Web search with RAG/direct modes
- Per-user multi-thread management
- Enhanced summarization and context management
- ...and much more!

👉 **Check out the advanced [LangChit](https://github.com/aminghrz/LangChit) project!**

---

## Dependencies

- `streamlit`
- `langgraph`
- `langchain-openai`
- `sqlite3` (standard library)
- *See* `requirements.txt` *for full details.*

---

## License

MIT License

---

## Contributing

Pull requests and forks welcome! This app is designed for researchers, devs, and hobbyists who want a minimal but robust starting point. If you have enhancements or spot a bug, please [open an issue](https://github.com/aminghrz/langgraph-streamlit-chat-interface/issues) or submit a PR!
