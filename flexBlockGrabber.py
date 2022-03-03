import requests
import json
import time
from datetime import datetime
from appJar import gui

# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    'x-amz-access-token': 'Atna|EwICIBYQqCBiYYh7jKRDF9-rG7a_vWK2OhNak2lprt5v_-T1UqD9okdUEVYi5OKmaFG5TorEFnnWvfTUZJ-BCA9RWdrucGKB_ncgsOQDz-bHMI1bwWI8FmhQQdOhOLYmAY3ard79maNn5bTtD4NN4qeuN2uQjYwzcNDJmQa0y6rDEQpZuWlWIhGZetcKRAls1efKPZWPE-s7n5G2LFJi7dimatAmzo_CyCn35iXwa-EXHRyZAzp8jqte2PP2ivhK-3VNXg-74radNWWfSIaZq7LMEvE0y56TdSgE5SJ8CX2lQRVPbt6b6l_Giqo-ddJEhQt7nMrjStmqrTVZkk1SBTtL8jZ1',
    'X-Amzn-RequestId': '85b0fb96-17be-4ca1-8225-b9dd5bcabb0f',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S2B3.220205.007.A1) RabbitAndroid/3.70.2.4.0',
    'X-Flex-Client-Time': '1646292146811',
    'x-flex-instance-id': '0604c7e6-8177-4b8d-8b64-cf0c5cff6023',
    'Authorization': 'RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=d749bf66d732c28d2c3f31f58f8032ba59182334da552b781fe77ee23b0c85d9',
    'Host': 'flex-capacity-na.amazon.com',
    'X-Amz-Date': '20220303T012226Z',
}


del headers["X-Flex-Client-Time"]
del headers["X-Amz-Date"]

highPay = 0
offerID = ""
keepTrying = True
startTime = ""
blockDuration = 0
blockPay = 0
app = gui()


def flex_grabber(headers=headers):
    global highPay, offerID, keepTrying, startTime, blockDuration, blockPay
    # This json_data is copied from a packet but remains the same, no need to change it

    search_json_data = {
        "apiVersion": "V2",
        "filters": {
            "serviceAreaFilter": [
                "6e412759-09ef-4314-92d9-c05ae1b73a50",
                "9ea0513e-8566-4e5e-b78c-a7c34ae5deb5",
                "529eb046-5a3f-4dc0-ac4a-6caf501bc91d",
                "8",
                "dae2f1d7-b83c-407b-824a-54f6ec8d4590",
                "bbcf923a-f0f5-42c9-8db5-6346b3a7e1f4",
            ],
            "timeFilter": {},
        },
        "serviceAreaIds": [
            "6e412759-09ef-4314-92d9-c05ae1b73a50",
        ],
    }

    # Requesting list of available blocks
    response = requests.post(
        "https://flex-capacity-na.amazon.com/GetOffersForProviderPost",
        headers=headers,
        json=search_json_data,
    )

    j = json.loads(response.text)
    # Looping through the available offers
    try:
        offer_list = j["offerList"]
    except KeyError:
        raise KeyError(j['message'])

    for i in offer_list:
        block_length = (i["endTime"] - i["startTime"]) / 3600
        price_amount = i["rateInfo"]["priceAmount"]
        # Making sure not to accept anything that starts less than 25 minutes from current time or anything under $30/hr
        if i["startTime"] - int(time.time()) < 1500 or price_amount / block_length < 30:
            continue
        # Filtering out blocks over 4 hours and making sure it's the highest paying offer
        if block_length <= 4 and not i["hidden"] and price_amount > highPay:
            highPay = price_amount
            offerID = i["offerId"]
            blockPay = price_amount
            startTime = datetime.fromtimestamp(i["startTime"])
            blockDuration = block_length
            print(block_length, highPay)

    if highPay:
        # Sending acceptance of offer
        accept_json_data = {
            "__type": "AcceptOfferInput:http://internal.amazon.com/coral/com.amazon.omwbuseyservice.offers/",
            "offerId": offerID,
        }
        accept = requests.post(
            "https://flex-capacity-na.amazon.com/AcceptOffer",
            headers=headers,
            json=accept_json_data,
        )

        # Checking response to confirm offer was accepted in time or if someone else got it, it includes a message if you missed it and is null if you got it
        try:
            json.loads(accept.text)["message"]
            highPay = 0
        except Exception:
            # Throw up a pop-up if you get a block, showing the date, time, and pay
            keepTrying = False
            return app.infoBox("Got One", f"{startTime}\n{blockDuration}\n${blockPay}")


while keepTrying:
    try:
        flex_grabber()
    except Exception as E:
        print(E)
        toExit = input("Press Enter To Exit")
        keepTrying = False