import os
import re
import requests
import json
from threading import Thread
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from flask import Flask
from dotenv import load_dotenv

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from parse_fields import extract_title, extract_priority, extract_assignee, extract_labels, extract_description


# Load environment variables from the .env file.
load_dotenv()

# Set OpenAI API key.

# Initialize Slack Bolt app using your Bot token.
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def enrich_bug_report(raw_text):
    prompt = (
        "You are the best AI product manager. Read the following raw bug report and produce "
        "a structured ticket with the following exact format:\n\n"
        "**Description:** <detailed explanation of the bug>\n\n"
        "**Priority:** <Urgent, High, Medium, or Low>\n\n"
        "**Recommended Assignee:** <choose the team member best suited>\n\n"
        "**Labels:** <choose one: Bug, Feature, or Improvement>\n\n"
        "**Title:** <a concise summary of the issue>\n\n"
        "Team Members:\n"
        "1. **Nikolas Ioannou (Co-Founder):** Best for strategic challenges and high-level product decisions.\n"
        "2. **Bhavik Patel (Founding Engineer):** Best for addressing core functionality issues and backend performance problems.\n"
        "3. **Aaron (Frontend Engineer):** Best for addressing frontend issues and UI/UX problems.\n"
        "4. **Rushil Nagarsheth (Founding Engineer):** Best for managing infrastructure challenges and system integrations.\n\n"
        "Raw Bug Report:\n"
        f"{raw_text}\n"
    )

    response = client.chat.completions.create(model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": (
                "You format bug reports into a structured ticket exactly following the Markdown format provided. "
                "Do not alter the markdown syntax. Do not include any section with 'Attachments:' in your response."
            )
        },
        {"role": "user", "content": prompt}
    ],
    temperature=0.7)
    ticket = response.choices[0].message.content

    # First, remove any lines that start with 'attachments:' (case-insensitive)
    ticket = re.sub(r"(?im)^\s*attachments:.*(?:\n|$)", "", ticket)
    # Then, remove any block that starts with '**Attachments:**' until the next header or end-of-string.
    ticket = re.sub(r"(?is)\*\*Attachments:\*\*.*?(?=\n\*\*|$)", "", ticket)
    # Specifically target "Attachments: None" pattern
    ticket = re.sub(r"(?is)\*\*Attachments:\*\*\s*None.*?(?=\n\*\*|$)", "", ticket)

    return ticket

def create_linear_ticket(enriched_report):
    LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
    LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")

    if not LINEAR_API_KEY or not LINEAR_TEAM_ID:
        raise ValueError("Please ensure LINEAR_API_KEY and LINEAR_TEAM_ID are set in your environment.")

    # Extract fields from the GPT output.
    title = extract_title(enriched_report)
    description = extract_description(enriched_report)  # Extract only the description portion.
    priority_str = extract_priority(enriched_report)
    assignee_name = extract_assignee(enriched_report)
    labels = extract_labels(enriched_report)

    if not labels:
        labels = ["Bug"]

    priority_map = {"low": 0, "medium": 1, "high": 2}
    priority = priority_map.get(priority_str.lower(), 1) if priority_str else 1

    # Normalize assignee name for case-insensitive matching.
    assignee_name = assignee_name.lower() if assignee_name else ""
    ASSIGNEE_MAP = {
        "": "",
        "nikolas ioannou": "93d4b23a-0c5a-4dc1-81d8-45d82684e9d4",
        "bhavik patel": "14543ff1-21dd-4e1d-ad23-bbf33d814ac0",
        "rushil nagarsheth": "094f80e8-8853-40ca-837f-81e0b2b2b07f",
        "aaron": "f5bc2d04-c905-4aa2-a25f-bbaa1e4af763",
    }

    assignee_id = ASSIGNEE_MAP.get(assignee_name)
    if not assignee_id:
        print(f"Warning: Assignee '{assignee_name}' not found in the mapping. Falling back to 'aaron'.")
        assignee_id = ASSIGNEE_MAP["aaron"]

    TICKET_TYPE_MAP = {
        "Bug Bot": os.getenv("LINEAR_BUG_LABEL_ID", "74ecf219-8bfd-4944-b106-4b42273f84a8"),
        "In QA": os.getenv("LINEAR_IN_QA_LABEL_ID", "ce778bdc-39e1-4a1b-a546-488fde56252b"),
        "Internal Admin": os.getenv("LINEAR_CORE_WEB_LABEL_ID", "031c70bb-cc93-40ec-a3dd-7ed36bc19b23"),
        "Core Web": os.getenv("LINEAR_BUG_LAB", "1d8a8a3d-5813-439f-a421-641875357c99"),
        "Core Mobile": os.getenv("LINEAR_BUG_LABEL_ID", "361e454d-9f41-494f-95ad-04301dbb3231"),
        "Backend": os.getenv("LINEAR_BUG_LABEL_ID", "c3aa8f63-f8c8-4d22-915e-6ddab30829d7"),
        # "QA'd --> Functional": os.getenv("LINEAR_INTERNAL_ADMIN_LABEL_ID", "d8a01af7-45ed-4257-b039-7f1c0d4fab92"),
        # "Feature": os.getenv("LINEAR_FEATURE_LABEL_ID", "504d1625-23fb-41ac-afea-e46bcabb4e53"),
        # "Improvement": os.getenv("LINEAR_IMPROVEMENT_LABEL_ID", "3688793e-2c4c-4e5b-a261-81f365f283f8")

    }
    mapped_labels = []
    for label in labels:
        normalized = label.strip().capitalize()
        if normalized in TICKET_TYPE_MAP:
            mapped_labels.append(TICKET_TYPE_MAP[normalized])
    if not mapped_labels:
        mapped_labels = [TICKET_TYPE_MAP["Bug"]]

    variables = {
        "input": {
            "teamId": LINEAR_TEAM_ID,
            "title": title,
            "description": description,
            "priority": priority
        }
    }
    if assignee_id:
        variables["input"]["assigneeId"] = assignee_id
    if mapped_labels:
        variables["input"]["labelIds"] = mapped_labels

    url = "https://api.linear.app/graphql"

    mutation = """
    mutation IssueCreate($input: IssueCreateInput!) {
      issueCreate(input: $input) {
        success
        issue {
          id
          title
          url
        }
      }
    }
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": LINEAR_API_KEY
    }

    response = requests.post(url, headers=headers, json={"query": mutation, "variables": variables})
    result = response.json()

    if "errors" in result:
        raise Exception(f"Linear API error: {result['errors']}")

    return result["data"]["issueCreate"]["issue"]

@app.event("app_mention")
def handle_app_mention(event, say, logger):
    user = event.get("user")
    text = event.get("text", "")
    thread_ts = event.get("ts")
    logger.info(f"Bot was mentioned by {user}: {text}")

    try:
        enriched_report = enrich_bug_report(text)
        ticket = create_linear_ticket(enriched_report)
        response_message = f"Thanks for reporting the bug, <@{user}>! A ticket has been created in Linear: {ticket.get('url', 'URL not available')}"
    except Exception as e:
        logger.error(f"Error processing bug report from mention: {e}")
        response_message = f"Sorry <@{user}>, there was an error processing your bug report."

    say(text=response_message, thread_ts=thread_ts)

# Minimal Flask app to bind to the $PORT for Heroku.
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Slack Bot is running!", 200

if __name__ == "__main__":
    # Start the Slack bot in a separate thread.
    def start_bot():
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        handler.start()

    bot_thread = Thread(target=start_bot)
    bot_thread.start()

    # Bind Flask to the $PORT provided by Heroku.
    port = int(os.environ.get("PORT", 5003))
    flask_app.run(host="0.0.0.0", port=port)