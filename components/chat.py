import json
import uuid
from datetime import datetime

import requests
import streamlit as st
from streamlit_extras.stateful_chat import chat

from utils.mongodb_message_store import MongoDBMessageStore
from utils.mongodb_prompt_store import MongoDBPromptStore


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

    # Initialize the MongoDB message store
    message_store = MongoDBMessageStore()
    prompt_store = MongoDBPromptStore()

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

    # Add states for command handling
    if "show_command_dropdown" not in st.session_state:
        st.session_state.show_command_dropdown = False

    if "input_value" not in st.session_state:
        st.session_state.input_value = ""

    if "selected_command" not in st.session_state:
        st.session_state.selected_command = None

    # Load available commands for dropdown
    all_prompts = prompt_store.get_all_prompts()

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

        # Admin Workspace (moved to the top, right after New Chat button)
        if is_admin:
            st.sidebar.divider()
            st.sidebar.subheader("Admin Workspace")

            if st.sidebar.button("Knowledge", use_container_width=True):
                st.session_state.admin_view = "knowledge"

            if st.sidebar.button("Prompts", use_container_width=True):
                st.session_state.admin_view = "prompts"

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

    # Handle admin views if selected
    if is_admin and st.session_state.get("admin_view") == "knowledge":
        st.subheader("Knowledge Management")
        st.write("Knowledge base management would appear here")
        if st.button("Back to Chat"):
            st.session_state.admin_view = None
            st.rerun()

    elif is_admin and st.session_state.get("admin_view") == "prompts":
        st.subheader("Prompt Management")

        # Create tabs for prompt management
        tab1, tab2, tab3 = st.tabs(["Create Prompt", "View Prompts", "Import/Export"])

        # TAB 1: Create Prompt
        with tab1:
            with st.form("create_prompt_form"):
                title = st.text_input("Prompt Title")

                # Show the command format below the title
                if title:
                    command = "/" + title.lower().replace(" ", "-")
                    st.caption(f"Command: {command}")

                content = st.text_area("Prompt Content", height=200)

                submitted = st.form_submit_button("Save Prompt")

                if submitted and title and content:
                    command = prompt_store.save_prompt(title, content)
                    st.success(f"Prompt saved! Use {command} in chat.")

        # TAB 2: View Prompts
        with tab2:
            prompts = prompt_store.get_all_prompts()

            if not prompts:
                st.info("No prompts available")
            else:
                for prompt in prompts:
                    with st.expander(f"{prompt['title']} ({prompt['command']})"):
                        st.text_area(
                            "Content", prompt["content"], disabled=True, height=100
                        )
                        st.caption(
                            f"Last updated: {prompt.get('last_updated', 'Unknown')}"
                        )

                        if st.button("Delete", key=f"delete_{prompt['command']}"):
                            prompt_store.delete_prompt(prompt["command"])
                            st.rerun()

        # TAB 3: Import/Export
        with tab3:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Export Prompts")
                export_data = prompt_store.export_prompts_to_json()
                st.download_button(
                    label="Download Prompts as JSON",
                    data=export_data,
                    file_name="prompts_export.json",
                    mime="application/json",
                )

            with col2:
                st.subheader("Import Prompts")
                uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
                if uploaded_file is not None:
                    try:
                        json_str = uploaded_file.getvalue().decode("utf-8")
                        count = prompt_store.import_prompts_from_json(json_str)
                        st.success(f"Successfully imported {count} prompts!")
                    except Exception as e:
                        st.error(f"Error importing prompts: {str(e)}")

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

            # Create a placeholder for the command dropdown
            command_dropdown = st.empty()

            # Get user input
            user_input = st.chat_input(
                "Type / to see commands or enter your message:",
                key="chat_input",
            )

            # Show command dropdown if user just typed "/"
            if user_input and user_input == "/":
                st.session_state.show_command_dropdown = True
                st.session_state.input_value = user_input
                st.rerun()

            # Display command dropdown if needed
            if st.session_state.show_command_dropdown:
                with command_dropdown:
                    command_options = [
                        f"{p['command']} - {p['title']}" for p in all_prompts
                    ]
                    if command_options:
                        selected = st.selectbox(
                            "Select a command:",
                            options=command_options,
                            key="command_selector",
                        )

                        if st.button("Use Command"):
                            # Extract just the command part (before the space)
                            selected_command = selected.split(" - ")[0]
                            stored_prompt = prompt_store.get_prompt_by_command(
                                selected_command
                            )
                            if stored_prompt:
                                # Store the selected command for processing
                                st.session_state.selected_command = stored_prompt[
                                    "content"
                                ]
                                st.session_state.show_command_dropdown = False
                                # Force a rerun to reset the UI
                                st.rerun()
                    else:
                        st.write("No commands available")

            # Process user input
            if user_input:
                # Reset the command dropdown flag
                st.session_state.show_command_dropdown = False

                # Check if user input starts with a command
                if user_input.startswith("/"):
                    # Extract command part (everything up to first space or end of string)
                    command = user_input.split(" ")[0]
                    stored_prompt = prompt_store.get_prompt_by_command(command)

                    if stored_prompt:
                        # Replace command with content
                        if " " in user_input:
                            # If there's additional text after the command, preserve it
                            remaining_text = user_input[len(command) :].strip()
                            prompt = f"{stored_prompt['content']} {remaining_text}"
                        else:
                            prompt = stored_prompt["content"]
                    else:
                        prompt = user_input
                else:
                    prompt = user_input

                # Process the message as before
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

            # Check if a command was selected from the dropdown
            elif st.session_state.selected_command:
                prompt = st.session_state.selected_command
                st.session_state.selected_command = None  # Reset

                # Process the message
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
