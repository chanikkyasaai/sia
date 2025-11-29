from twilio.rest import Client
from app.core.config import settings
from fastapi import APIRouter

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN

sms_route = APIRouter()

client = Client(account_sid, auth_token)

@sms_route.post("/send")
def send_sms(message: str):
    sent_message = client.messages.create(
        from_='+14784007189',
        body=message,
        to='+918667282882'
    )
    return {"sid": sent_message.sid}
    # print(message.sid)
