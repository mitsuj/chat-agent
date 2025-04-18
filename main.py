import streamlit as st

from authentication.auth import get_authenticator
from components.chat import chat_interface


def main():
    authenticator, config = get_authenticator()

    try:
        authenticator.login()
    except Exception as e:
        st.error(e)

    if st.session_state.get("authentication_status"):
        st.sidebar.success(f"Logged in as {st.session_state.get('name')}")

        # Add logout button to sidebar
        if st.sidebar.button("Logout"):
            authenticator.logout()
            st.experimental_rerun()

        # Your main application content
        # st.title("Chat Agent")

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
