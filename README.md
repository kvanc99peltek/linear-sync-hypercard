# linear-sync-hypercard
Build better faster, stronger!

A Slack bot that automatically converts bug reports into structured Linear tickets using GPT.

## Features
- Trigger with "bug!" command in Slack
- Automatically formats bug reports with AI
- Creates Linear tickets with proper formatting
- Handles screenshot attachments
- Suggests appropriate team member assignments

## Setup

1. **Environment Variables**

bash
SLACK_BOT_TOKEN="xoxb-your-token" # Slack Bot User OAuth Token
SLACK_APP_TOKEN="xapp-your-token" # Slack App-Level Token
LINEAR_API_KEY="lin_api_xxx" # Linear API Key
LINEAR_TEAM_ID="xxx" # Linear Team ID
OPENAI_API_KEY="sk-xxx" # OpenAI API Key


2. **Installation**

bash
pip install -r requirements.txt
python app.py


## Usage
1. Invite the bot to your Slack channel
2. Type "bug!" followed by your bug report
3. Optionally attach screenshots
4. Bot will respond with a Linear ticket link

## Development
- Python 3.8+
- Uses Slack's Socket Mode for events
- Requires Linear API access
- OpenAI GPT-4 for report structuring