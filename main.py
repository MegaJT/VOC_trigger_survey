from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from twilio.rest import Client
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TYPEFORM_SURVEY_LINK = os.getenv("TYPEFORM_SURVEY_LINK")

if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TYPEFORM_SURVEY_LINK]):
    raise EnvironmentError("Missing one or more required environment variables.")

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize FastAPI app
app = FastAPI()


# Request payload schema
class TriggerRequest(BaseModel):
    customer_name: str
    mobile_number: str  # Must include country code (e.g., +971xxxxx)


@app.post("/trigger-survey")
def trigger_survey(request: TriggerRequest):
    try:
        message_text = (
            f"Hi {request.customer_name}, thank you for using our service. "
            f"Please share your feedback: {TYPEFORM_SURVEY_LINK}"
            f"#first_name={request.customer_name}&phone_number={request.mobile_number}"
        )

        whatsapp_to = f"whatsapp:{request.mobile_number}"
        whatsapp_from = f"whatsapp:{TWILIO_PHONE_NUMBER}"

        retries = 3
        for attempt in range(1, retries + 1):
            try:
                message = twilio_client.messages.create(
                    body=message_text,
                    from_=whatsapp_from,
                    to=whatsapp_to
                )
                logging.info(f"Message sent on attempt {attempt}, SID: {message.sid}")
                break
            except Exception as e:
                logging.warning(f"Attempt {attempt} failed: {e}")
                if attempt == retries:
                    raise HTTPException(status_code=500, detail="All message attempts failed.")


                logging.info(f"WhatsApp message sent to {request.mobile_number}, SID: {message.sid}")

                return {
                    "status": "success",
                    "sid": message.sid,
                    "to": request.mobile_number
                }

    except Exception as e:
        logging.error(f"Failed to send message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

