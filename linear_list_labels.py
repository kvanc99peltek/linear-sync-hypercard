import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from the .env file.
load_dotenv()

# Retrieve your Linear API key and Team ID from environment variables.
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID")

if not LINEAR_API_KEY or not LINEAR_TEAM_ID:
    raise ValueError("Please set LINEAR_API_KEY and LINEAR_TEAM_ID in your environment.")

# Set the Linear GraphQL endpoint.
url = "https://api.linear.app/graphql"

# Define a GraphQL query to fetch team members.
query = """
query TeamMembers($teamId: String!) {
  team(id: $teamId) {
    id
    name
    members {
      nodes {
        id
        displayName
        email
      }
    }
  }
}
"""

# Build the payload with the team ID.
variables = {"teamId": LINEAR_TEAM_ID}

# Set up headers for authentication.
headers = {
    "Content-Type": "application/json",
    "Authorization": f"{LINEAR_API_KEY}"
}

# Send the request.
response = requests.post(url, headers=headers, json={"query": query, "variables": variables})
data = response.json()

# Print the response in a readable format.
print(json.dumps(data, indent=2))