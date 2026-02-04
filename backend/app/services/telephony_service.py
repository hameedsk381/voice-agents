"""
Telephony service for handling Twilio voice calls and streaming.
"""
import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from loguru import logger

class TelephonyService:
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid else None
        
    def generate_twiml_stream(self, stream_url: str, welcome_message: str = None) -> str:
        """Generate TwiML to connect a call to a media stream."""
        response = VoiceResponse()
        if welcome_message:
            response.say(welcome_message)
            
        connect = Connect()
        connect.stream(url=stream_url)
        response.append(connect)
        return str(response)

    async def initiate_outbound_call(self, to_number: str, from_number: str, webhook_url: str):
        """Triggers an outbound call via Twilio API."""
        if not self.client:
            logger.error("Twilio client not initialized (missing SID/Token)")
            return None
            
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=webhook_url
            )
            logger.info(f"Initiated outbound call to {to_number}: {call.sid}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to initiate Twilio call: {e}")
            return None

telephony_service = TelephonyService()
