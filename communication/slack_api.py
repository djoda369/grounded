import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

load_dotenv()

production = True
production_name = "GAIA" if production else "TEST"

slack_token = os.environ[f"SLACK_{production_name}_TOKEN"]
app_token = os.environ[f"SLACK_{production_name}_APP_TOKEN"]

app = App(token=slack_token)
slack_client = WebClient(token=slack_token)

signing_secret = os.environ[f"SLACK_{production_name}_SIGNING_SECRET"]
signature_verifier = SignatureVerifier(signing_secret)

verification_token = os.environ[f"SLACK_{production_name}_VERIFICATION_TOKEN"]
