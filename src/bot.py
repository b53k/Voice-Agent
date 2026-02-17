'''
CALL MANAGER:
Orchestrates outbound calls using Twilio's Programmable Voice API. 
Manages call lifecycle, handles webhook callbacks for call status, 
and initiates Media Streams connection. Uses ngrok tunnel for local development.
'''

import os
from pathlib import Path
from dotenv import load_dotenv
from twilio.rest import Client

env_path = Path(__file__).parent / '.env'
load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)
webhook_url = os.getenv('WEBHOOK_URL')


def make_call(to_number, from_number, webhook_url):
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        #url = 'https://demo.twilio.com/welcome/voice/',
        url=webhook_url + '/webhook/answer'
    )

    print (f"Call initiated with SID: {call.sid}")
    return call.sid

if __name__ == '__main__':
    twilio_number = '+14043415604'
    test_number = '+16156451400'
    my_number = '+16623800332'
    sabin_number = '+17047960263'
    make_call(sabin_number, twilio_number, webhook_url)
