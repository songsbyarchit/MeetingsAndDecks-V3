import os
import requests
import openai
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

WEBEX_TOKEN = os.getenv("WEBEX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming Webex webhooks."""
    webhook_data = request.json
    print("🔔 Webhook triggered with data:", webhook_data)

    # 1. Verify the webhook event is a new message in the correct room
    resource = webhook_data.get("resource")
    event = webhook_data.get("event")
    data = webhook_data.get("data", {})

    if resource == "messages" and event == "created":
        message_id = data.get("id")
        room_id = data.get("roomId")

        if message_id:
            # 2. Get the actual text of the message from Webex
            message_text = fetch_webex_message_text(message_id)
            print(f"Received message: {message_text}")

            # 3. Send this text to your OpenAI function
            openai_response = process_natural_language_input(message_text)

            # 4. Print or handle the OpenAI response
            print(f"OpenAI response: {openai_response}")

    return jsonify({"status": "ok"}), 200

@app.route("/callback", methods=["GET"])
def oauth_callback():
    """Handles OAuth callback from Webex."""
    code = request.args.get("code")
    state = request.args.get("state")
    
    if not code:
        return "Error: No authorization code received.", 400

    print(f"✅ Received OAuth Code: {code}")
    return "OAuth successful! You can close this window.", 200

def fetch_webex_message_text(message_id):
    """Fetch the text of a Webex message by its ID."""
    url = f"https://webexapis.com/v1/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {WEBEX_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        message_data = response.json()
        return message_data.get("text", "")
    else:
        print(f"Failed to retrieve message: {response.text}")
        return ""

def process_natural_language_input(user_text):
    """
    Uses OpenAI's GPT-3.5-turbo to process user text and return structured data.
    """

    try:
        # Example prompt + system role. Adjust to your own logic!
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful meeting scheduling assistant. "
                        "When a user asks to schedule a meeting, parse the relevant details "
                        "like attendees, date, and time, and return them in JSON format. "
                        "For example: {\"attendees\":[...], \"date\":\"...\", \"time\":\"...\"}."
                    )
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            temperature=0.7
        )

        # Extract the response text from the OpenAI API response
        assistant_message = response["choices"][0]["message"]["content"]
        return assistant_message

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {"error": str(e)}
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)