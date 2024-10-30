import slack_sdk
from slack_sdk.errors import SlackApiError

from app.settings import SLACK_CHANNEL_NAME, SLACK_TOKEN

slack_client = slack_sdk.WebClient(token=SLACK_TOKEN)


def send_slack_notification(message):
    try:
        response = slack_client.chat_postMessage(
            channel=SLACK_CHANNEL_NAME, text=message
        )
        if not response["ok"]:
            error_message = response["error"]
            # TODO add to log
    except SlackApiError as e:
        pass
