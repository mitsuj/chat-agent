import streamlit as st
from datetime import datetime
import uuid
import requests
from utils.message_store import MessageStore


def get_available_ollama_models():
    """
    Fetch available models from the Ollama API.

    Returns:
        list: List of available model names
    """
    default_models = ["llama3", "mistral", "gemma", "llama2", "phi3"]

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Extract model names from response
            available_models = [model["name"] for model in data.get("models", [])]
            return available_models if available_models else default_models
        else:
            return default_models
    except Exception:
        # Return default models if API call fails
        return default_models


def chat_interface(user_name, is_admin=False):
    """
    Renders a chat interface component with message history.

    Args:
        user_name (str): The name of the current user
        is_admin (bool): Whether the current user is an admin
    """

    # Initialize the message store
    message_store = MessageStore()

    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
        # Load all chat sessions from storage
        chat_sessions = message_store.load_all_chats(user_name)
        if chat_sessions:
            st.session_state.chat_history = chat_sessions

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "llama3"

    # Create header with model selection dropdown
    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("💬 Chat Interface")

    with col2:
        # Model selection dropdown
        available_models = get_available_ollama_models()
        st.session_state.selected_model = st.selectbox(
            "Select Model",
            available_models,
            index=(
                available_models.index(st.session_state.selected_model)
                if st.session_state.selected_model in available_models
                else 0
            ),
        )

    # Create sidebar with direct options (not dropdown)
    with st.sidebar:
        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True):
            # Create a new chat session
            st.session_state.current_chat_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

        st.sidebar.divider()

        # Chat History Section
        st.sidebar.subheader("Chat History")

        # Display chat history as titles
        if not st.session_state.chat_history:
            st.sidebar.info("No previous chats")
        else:
            for chat_id, chat_data in sorted(
                st.session_state.chat_history.items(),
                key=lambda x: x[1].get("last_updated", ""),
                reverse=True,
            ):
                # Extract the first user message as title
                first_msg = next(
                    (
                        msg
                        for msg in chat_data.get("messages", [])
                        if msg["role"] == "user"
                    ),
                    None,
                )
                if first_msg:
                    title = first_msg["content"][:30] + (
                        "..." if len(first_msg["content"]) > 30 else ""
                    )
                    timestamp = chat_data.get("last_updated", "Unknown date")

                    # Make chat title clickable
                    if st.sidebar.button(f"{title}", key=f"chat_{chat_id}"):
                        st.session_state.current_chat_id = chat_id
                        st.session_state.messages = chat_data.get("messages", [])
                        st.rerun()
                    st.sidebar.caption(f"{timestamp}")

        # Admin Workspace (if applicable)
        if is_admin:
            st.sidebar.divider()
            st.sidebar.subheader("Admin Workspace")

            if st.sidebar.button("View All Users", use_container_width=True):
                st.session_state.admin_view = "users"

            if st.sidebar.button("System Statistics", use_container_width=True):
                st.session_state.admin_view = "stats"

    # Handle admin views if selected
    if is_admin and st.session_state.get("admin_view") == "users":
        st.subheader("User Management")
        st.write("User list would appear here")
        if st.button("Back to Chat"):
            st.session_state.admin_view = None
            st.rerun()

    elif is_admin and st.session_state.get("admin_view") == "stats":
        st.subheader("System Statistics")
        st.write("System statistics would appear here")
        if st.button("Back to Chat"):
            st.session_state.admin_view = None
            st.rerun()

    else:
        # Main chat display
        if not st.session_state.current_chat_id:
            st.info("Start a new chat or select a previous conversation")
        else:
            # Display messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(f"{message['content']}")
                    st.caption(f"{message['timestamp']} - {message['user']}")

            if prompt := st.chat_input("What would you like to ask?"):
                # Add user message
                user_message = {
                    "role": "user",
                    "content": prompt,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user": user_name,
                }

                st.session_state.messages.append(user_message)

                with st.chat_message("user"):
                    st.write(prompt)
                    st.caption(f"{user_message['timestamp']} - {user_name}")

                # Generate response using Ollama with selected model
                with st.spinner(f"Thinking with {st.session_state.selected_model}..."):
                    try:
                        response = get_ollama_response(
                            prompt=prompt,
                            messages=st.session_state.messages,
                            model=st.session_state.selected_model,
                        )
                    except Exception as e:
                        response = f"Sorry, I encountered an error: {str(e)}"

                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "user": "Assistant",
                }

                st.session_state.messages.append(assistant_message)

                with st.chat_message("assistant"):
                    st.write(response)
                    st.caption(f"{assistant_message['timestamp']} - Assistant")

                # Save updated chat to history
                st.session_state.chat_history[st.session_state.current_chat_id] = {
                    "messages": st.session_state.messages,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Save messages to storage
                message_store.save_chat(
                    user_name,
                    st.session_state.current_chat_id,
                    st.session_state.chat_history[st.session_state.current_chat_id],
                )


def get_ollama_response(prompt, messages=None, model="llama3"):
    """
    Get a response from Ollama API with conversation context.

    Args:
        prompt (str): The user's input prompt
        messages (list): Previous messages in the conversation
        model (str): The model name to use

    Returns:
        str: The generated response
    """
    try:
        # Build conversation context from previous messages
        conversation_context = ""
        if messages:
            for msg in messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"{role}: {msg['content']}\n\n"

        # Add the current prompt to the context
        full_prompt = f"{conversation_context}User: {prompt}\n\nAssistant:"

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": full_prompt, "stream": False},
            timeout=60,
        )

        if response.status_code == 200:
            return response.json().get("response", "No response generated")
        else:
            return f"Error: Received status code {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure it's running on your system."
    except Exception as e:
        return f"Error: {str(e)}"
