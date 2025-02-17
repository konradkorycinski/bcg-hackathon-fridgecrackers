import os
import time
import datetime
import requests

import RPi.GPIO as GPIO
import dht11

MAX_TEMP = 10

DHT11_PIN = 21
LDR_LIGHT_PIN = 16

# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(LDR_LIGHT_PIN, GPIO.IN)

# GPIO.cleanup()

# read data using pin 14
dht = dht11.DHT11(pin = DHT11_PIN)

temp_list = [0 for _ in range(3)]

def run():
    while True:
        result = dht.read()
        
        # dht11 need time to reset before next read
        # only then will the read data be valid
        if result.is_valid():
            date = datetime.datetime.now()

            is_light = GPIO.input(LDR_LIGHT_PIN) == 0

            print(f"{date:%Y-%m-%d %H:%M:%s}")
            print("Temperature: %-3.1f C" % result.temperature)
            print("Humidity: %-3.1f %%" % result.humidity)
            print(f"Light: {is_light}")

            log_data(
                result.temperature,
                result.humidity,
                is_light,
                timestamp=date.timestamp()
            )
             
            temp_list.append(result.temperature)
            temp_list.pop(0)
            print(temp_list)
    
            # if last 10 temp recording are above threshold, make an alert
            if all([temp > MAX_TEMP for temp in temp_list]):
                # call_twilio()
                alert(result)

            time.sleep(1)

 
def alert(result):
    print(f"ALERT!: temprerature {result.temperature} is above the threshold of {MAX_TEMP}")
    
def call_twilio():
    from twilio.rest import Client as TwilioClient

    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = TwilioClient(account_sid, auth_token)
    
    call = client.calls.create(
        url='http://demo.twilio.com/docs/voice.xml',
        to=os.environ["TO_PHONE_NUM"],
        from_=os.environ["FROM_PHONE_NUM"]
    )


def log_data(temperature, humidity, is_light, timestamp):
    import boto3
    import requests
     
    CloudWatch = boto3.client('cloudwatch')
    try:
        response = CloudWatch.put_metric_data(
            MetricData = [
                {
                    'MetricName': 'Temperature',
                    "Timestamp": timestamp,
                    'Unit': 'Count',
                    'Value': temperature,
                    'Dimensions': [
                        {
                            'Name': 'Name',
                            'Value': 'Fridge 1'
                        },
                        {
                            'Name': 'Sensor',
                            'Value': 'DMT11'
                        },
                    ],
                },
                {
                    'MetricName': 'Humidity',
                    'Unit': 'Percent',
                    'Value': humidity,
                    'Dimensions': [
                        {
                            'Name': 'Name',
                            'Value': 'Fridge 1'
                        },
                        {
                            'Name': 'Sensor',
                            'Value': 'DMT11'
                        },
                    ],
                },
                {
                    'MetricName': 'Light',
                    'Unit': 'Bits',
                    'Value': int(is_light),
                    'Dimensions': [
                        {
                            'Name': 'Name',
                            'Value': 'Fridge 1'
                        },
                        {
                            'Name': 'Sensor',
                            'Value': 'LDR'
                        },
                    ],
                },
            ],
            Namespace='FridgeCrackers'
        )
        print(response)
    except:
        import json

        # there was an issue with connecting to the internet
        # save the data locally
        with open("./data.log", "a") as file_handle:
            file_handle.write(json.dump({
                "temeperature": temperature,
                "humidity": humidity,
                "is_light": is_light,
                "timestamp": timestamp,
            }))


if __name__ == "__main__":
    run()
