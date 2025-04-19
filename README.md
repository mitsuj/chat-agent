# Chat Agent

A Streamlit-based chat application that integrates with Ollama for AI model responses, featuring user authentication, MongoDB storage, and prompt management.

## Features

- **User Authentication**: Secure login with role-based access control (admin, editor, viewer)
- **Multiple Chat Sessions**: Create and manage separate chat conversations
- **Chat History**: Automatically saves conversations to MongoDB
- **LLM Integration**: Connect to local Ollama models
- **Model Selection**: Choose from available Ollama models
- **Custom Prompts**: Create, manage, import, and export prompt templates
- **Admin Workspace**: Special features for admin users

## Prerequisites

- Python 3.11+
- MongoDB server
- Ollama running locally

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/chat-agent.git
cd chat-agent
```

2. **Create a virtual environment**

Using uv:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
uv sync
```

4. **Configure MongoDB**

Make sure MongoDB is running locally or update the connection details in `config/mongodb_config.py`.

5. **Set up authentication**

Copy the example authentication config and customize it:

```bash
cp config/config.yaml.example config/auth_config.yaml
```

Edit `config/auth_config.yaml` with your user information and a secure cookie key.

## Configuration

### Authentication

Edit `config/auth_config.yaml` to set up users with different roles:

- **admin**: Full access to all features
- **editor**: Can create and edit chats and prompts
- **viewer**: Basic chat access only

Example configuration:

```yaml
cookie:
  expiry_days: 30
  key: your-random-secret-key
  name: chat-agent-cookie
credentials:
  usernames:
    admin_user:
      email: admin@example.com
      password: secure_password
      first_name: Admin
      last_name: User
      roles:
        - admin
```

### MongoDB

Configure your MongoDB connection in `config/mongodb_config.py`:

```python
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "chat_agent"
```

## Usage

Start the application:

```bash
streamlit run main.py
```

Access the web interface at `http://localhost:8501`

## Features

### Chat Interface

- Create new chat sessions
- Switch between previous conversations
- Send messages to Ollama models
- Use custom prompts with the `/command` syntax

### Admin Features

- **Knowledge Management**: Manage knowledge bases (upcoming feature)
- **Prompt Management**: Create, view, import, and export prompt templates

## Project Structure

```
chat-agent/
├── authentication/     # User authentication
├── components/         # UI components
├── config/             # Configuration files
├── utils/              # MongoDB utilities
└── main.py             # Application entry point
```

## Dependencies

- pymongo >= 4.12.0
- requests >= 2.32.3
- streamlit >= 1.44.1
- streamlit-authenticator >= 0.4.2
- streamlit-extras >= 0.6.0
