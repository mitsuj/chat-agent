import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os


def get_authenticator():
    # Update path to point to the config directory
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "auth_config.yaml",
    )
    with open(config_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Pre-hashing all plain text passwords once
    # stauth.Hasher.hash_passwords(config['credentials'])

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
    )

    return authenticator, config
