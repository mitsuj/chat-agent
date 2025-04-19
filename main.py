import streamlit as st

from authentication.auth import get_authenticator
from components.chat import chat_interface


def clear_chat_session_state():
    """Clear all chat-related session state variables"""
    for key in [
        "messages",
        "current_chat_id",
        "chat_history",
        "selected_model",
        "admin_view",
    ]:
        if key in st.session_state:
            del st.session_state[key]


def main():
    authenticator, config = get_authenticator()

    # Store previous authentication status to detect changes
    previous_auth_status = st.session_state.get("authentication_status")

    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    # Check if authentication status changed (login or logout)
    current_auth_status = st.session_state.get("authentication_status")
    if previous_auth_status != current_auth_status:
        clear_chat_session_state()

    if st.session_state.get("authentication_status"):
        st.sidebar.success(f"Logged in as {st.session_state.get('name')}")

        # Use the authenticator's built-in logout function instead of custom button
        authenticator.logout("Logout", "sidebar", key="logout_button")

        # Check if user is admin
        username = st.session_state.get("username")
        user_info = config["credentials"]["usernames"].get(username, {})
        user_roles = user_info.get("roles", [])
        is_admin = "admin" in user_roles

        # Display the chat interface with admin status
        chat_interface(st.session_state.get("name"), is_admin)

    elif st.session_state.get("authentication_status") is False:
        st.error("Username/password is incorrect")
    elif st.session_state.get("authentication_status") is None:
        st.warning("Please enter your username and password")


if __name__ == "__main__":
    main()
