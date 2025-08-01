import streamlit as st
import sqlite3
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime
from openai import OpenAI

from app_functions import (
    init_user_settings_db,
    save_user_settings,
    load_user_settings,
    get_thread_ids,
    load_messages_for_thread
)

st.set_page_config(layout="wide", page_title="LangGraph Chat Agent")
st.markdown("""
<style>
h1, h2, h3, h4, h5, h6 {
    font-family: 'Segoe UI Emoji', 'Segoe UI Symbol', 'Segoe UI', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)
if "settings_db_initialized" not in st.session_state:
    init_user_settings_db(db="chatbot.sqlite3")
    st.session_state.settings_db_initialized = True

########################### Start of User API Settings ################################    
if "user_api_settings" not in st.session_state:
    st.session_state.user_api_settings = load_user_settings(db="chatbot.sqlite3")
settings_configured = bool(
    st.session_state.user_api_settings.get("api_key") and
    st.session_state.user_api_settings.get("base_url") and 
    st.session_state.user_api_settings.get("model")
)

@st.cache_resource
def get_openai_client(api_key, base_url):
    """Caches the OpenAI client to avoid re-initializing on every rerun."""
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {e}")
        return None

@st.cache_data(show_spinner=False)
def fetch_model_list(api_key, base_url):
    """Fetch model IDs once per unique (api_key, base_url)."""
    client = OpenAI(api_key=api_key, base_url=base_url)
    models = client.models.list()
    if getattr(models, "data", None):
        return [m.id for m in models.data]
    else:
        return []

with st.sidebar.expander("🔧 API Settings", expanded=not settings_configured):
    api_key_input = st.text_input(
        "API Key:",
        value=st.session_state.user_api_settings.get("api_key", ""),
        type="password",
        help="Enter your API key",
        key="api_key_input"
    )
    base_url_input = st.text_input(
        "Base URL:",
        value=st.session_state.user_api_settings.get("base_url", ""),
        placeholder="https://api.example.com/v1",
        help="Enter the base URL for the API",
        key="base_url_input"
    )

    effective_api_key = api_key_input.strip() or st.session_state.user_api_settings.get("api_key", "").strip()
    effective_base_url = base_url_input.strip() or st.session_state.user_api_settings.get("base_url", "").strip()

    if effective_api_key and effective_base_url:
        client = get_openai_client(effective_api_key, effective_base_url)
    else:
        client = None
        st.warning("Enter both API Key and Base URL to initialize client")

    prev_key = st.session_state.get("__api_key_for_models")
    prev_url = st.session_state.get("__base_url_for_models")
    if (effective_api_key and effective_base_url) and (effective_api_key != prev_key or effective_base_url != prev_url):
        st.session_state["model_ids"] = []
        if "selected_model" in st.session_state:
            del st.session_state["selected_model"]
        st.session_state["__api_key_for_models"] = effective_api_key
        st.session_state["__base_url_for_models"] = effective_base_url

    if "model_ids" not in st.session_state:
        st.session_state["model_ids"] = []

    if client:
        if not st.session_state["model_ids"]:
            with st.spinner("Fetching available models..."):
                try:
                    ids = fetch_model_list(effective_api_key, effective_base_url)
                    if ids:
                        st.session_state["model_ids"] = ids
                    else:
                        st.warning("No models returned by the API endpoint.")
                except Exception as e:
                    st.error(f"Error fetching models: {e}")
        if st.session_state["model_ids"]:
            model_ids = st.session_state["model_ids"]
            default_idx = 0
            if st.session_state.user_api_settings["model"]:
                default_idx = model_ids.index(st.session_state.user_api_settings["model"])
            if ("selected_model" in st.session_state and st.session_state.selected_model in model_ids):
                default_idx = model_ids.index(st.session_state.selected_model)
            st.selectbox(
                "Choose a model:",
                options=model_ids,
                index=default_idx,
                key="selected_model",
                help="Select an available model from your endpoint"
            )
        else:
            st.info("No available models to choose. Check your API settings or the endpoint.")
    else:
        st.warning("OpenAI client could not be initialized. Please check API key & Base URL.")

    if st.button("💾 Save API Settings"):
        if api_key_input.strip() and base_url_input.strip():
            save_user_settings(
                db="chatbot.sqlite3",
                api_key=api_key_input.strip(),
                base_url=base_url_input.strip(),
                model=st.session_state.selected_model
            )
            st.session_state.user_api_settings = {
                "api_key": api_key_input.strip(),
                "base_url": base_url_input.strip(),
                "model": st.session_state.selected_model
            }
            st.success("API settings saved successfully!")
            st.rerun()
        else:
            st.error("Please fill in both API Key and Base URL")
if not settings_configured:
    st.sidebar.warning("⚠️ Please configure your API settings")
########################### End of User API Settings ################################

if not st.session_state.user_api_settings.get("api_key") or not st.session_state.user_api_settings.get("base_url"):
    st.warning("⚠️ Please configure your API settings in the sidebar before using the chat.")
    st.stop()


if "conn" not in st.session_state:
    st.session_state.conn = sqlite3.connect("chatbot.sqlite3", check_same_thread=False)

if "store" not in st.session_state:
    embedding_model = OpenAIEmbeddings(
        model='text-embedding-3-large',
        api_key=st.session_state.user_api_settings["api_key"],
        base_url=st.session_state.user_api_settings["base_url"]
    )

from graph import create_graph
if "app" not in st.session_state or \
    "last_api_settings" not in st.session_state or \
    st.session_state.last_api_settings != st.session_state.user_api_settings: #or \

    st.session_state.app, st.session_state.checkpointer = create_graph(
        model=st.session_state.user_api_settings["model"],
        api_key=st.session_state.user_api_settings["api_key"],
        base_url=st.session_state.user_api_settings["base_url"],
        conn=st.session_state.conn
    )
    st.session_state.last_api_settings = st.session_state.user_api_settings.copy()
    st.info("LangGraph app compiled with updated settings.")


if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

if "current_summary" not in st.session_state:
    st.session_state.current_summary = ""


st.sidebar.title("Chat Threads")

available_threads = get_thread_ids(st.session_state.conn)

if available_threads:
    options = available_threads
    if st.session_state.thread_id and st.session_state.thread_id not in options:
        options = [st.session_state.thread_id] + options

    try:
        current_selection_index = options.index(st.session_state.thread_id) if st.session_state.thread_id in options else 0
    except ValueError:
        current_selection_index = 0 

    selected_thread = st.sidebar.selectbox(
        "Select a Thread:",
        options,
        index=current_selection_index,
        key="thread_selector"
    )

    if selected_thread and selected_thread != st.session_state.thread_id:
        st.session_state.thread_id = selected_thread
        raw_lc_messages = load_messages_for_thread(st.session_state.thread_id, st.session_state.checkpointer)
        st.session_state.display_messages = raw_lc_messages

        agent_config = {"configurable": {"thread_id": st.session_state.thread_id}}
        state_data = st.session_state.checkpointer.get(config=agent_config)
        if state_data and "channel_values" in state_data and "summary" in state_data["channel_values"]:
            st.session_state.current_summary = state_data["channel_values"]["summary"]
        else:
            st.session_state.current_summary = ""
        st.rerun()
elif not st.session_state.thread_id and not available_threads:
    st.sidebar.info("No threads yet. Click 'New Thread' to start.")


# "Start New Thread" button
if st.sidebar.button("➕ New Thread"):
    new_thread_id_num = f"{'user'}@{datetime.now().strftime('%Y%m%d_%H%M%SS')}"

    st.session_state.thread_id = str(new_thread_id_num)
    st.session_state.display_messages = []
    st.session_state.current_summary = ""
    st.success(f"Started new thread: {st.session_state.thread_id}")
    if st.session_state.thread_id not in available_threads:
        available_threads.insert(0, st.session_state.thread_id)
    st.rerun() 

st.title("🤖 LangGraph Powered Chat")

if st.session_state.thread_id:
    st.markdown(f"**Current Thread ID:** `{st.session_state.thread_id}`")
    if st.session_state.current_summary:
        with st.expander("Conversation Summary", expanded=False):
            st.markdown(st.session_state.current_summary)

    # Display chat messages from history
    for msg in st.session_state.display_messages:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        elif isinstance(msg, AIMessage):
            with st.chat_message("assistant"):
                st.markdown(msg.content)

    # Chat input for the user
    if prompt := st.chat_input("What would you like to discuss?"):
        st.session_state.display_messages.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        graph_input = {"messages": [HumanMessage(content=prompt)]}
        agent_config = {"configurable": {"thread_id": st.session_state.thread_id}}

        try:
            # Stream the agent response without showing status
            for event in st.session_state.app.stream(graph_input, config=agent_config, stream_mode="updates"):
                pass  # Just process without displaying

            # After invocation, reload the state
            updated_lc_messages = load_messages_for_thread(st.session_state.thread_id, st.session_state.checkpointer)
            st.session_state.display_messages = updated_lc_messages

            state_data = st.session_state.checkpointer.get(config=agent_config)
            if state_data and "channel_values" in state_data and "summary" in state_data["channel_values"]:
                st.session_state.current_summary = state_data["channel_values"]["summary"]

        except Exception as e:
            st.error(f"Error interacting with the agent: {e}")

        st.rerun()

else:
    st.info("Please select a thread or start a new one from the sidebar to begin chatting.")