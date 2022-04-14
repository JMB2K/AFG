import requests
import json
import time
from datetime import datetime
from appJar import gui

# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    'x-amz-access-token': 'Atna|EwICIOuj2GnvkDHeEDPPQAh9chhFj7aGhXYfDkPp3ZRbhOa6fRQjt2rWnZWQQwoGzP1NJ1I0OfUVZw3RTvU94_2uNqOrzYUYx_LMGf6KzkcWLlNVgDRtg9QCalPCX3HSm230Yu5yAN257caFtW5_BQsmTMNYvYLIxYdIIlYg5zxzQ-1UcezaHZl7xVOhs0etbdYTB0q3UaKWf1XH-fXYooW_dnAk_25pPJZH8FOpdOtWDZTe6pUkFrSUo2G3WCOq2oabtdmrYnng05Epy2rD0U6sOGM1XHH7Ap9weBp3GIwBvDV0i8r8xZy-j7ZrKtC1AWpOLK1h0vPh9ag64tGdKa2-AInB',
    'X-Amzn-RequestId': 'd057bdc6-2730-48c1-bfb7-ae769fedc1d9',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S3B1.220218.006) RabbitAndroid/3.72.1.25.0',
    'X-Flex-Client-Time': '1649627084823',
    'x-flex-instance-id': '0604c7e6-8177-4b8d-8b64-cf0c5cff6023',
    # Already added when you pass json=
    # 'Content-Type': 'application/json',
    'Authorization': 'RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=7a1fa0f716e2c88d68fb2e5d1a1698f0af386ef60d025af5f67784664e7cfe74',
    'Host': 'flex-capacity-na.amazon.com',
    'X-Amz-Date': '20220410T164445Z',
}
del headers["X-Flex-Client-Time"]
del headers["X-Amz-Date"]

offerID = ""
keepTrying = True
startTime = ""
blockDuration = 0
blockPay = 0
app = gui()


def flex_grabber(headers=headers):
    global offerID, keepTrying, startTime, blockDuration, blockPay
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
        raise KeyError(j)

    for i in [block for block in offer_list if not block["hidden"]]:
        block_length = (i["endTime"] - i["startTime"]) / 3600
        price_amount = i["rateInfo"]["priceAmount"]
        # Making sure not to accept anything that starts less than 25 minutes from current time or anything under $30/hr
        if i["startTime"] - int(time.time()) < 1500 or price_amount / block_length < 33:
            continue

        offerID = i["offerId"]
        # blockPay = price_amount
        startTime = datetime.fromtimestamp(i["startTime"])
        # blockDuration = block_length
        #print(block_length, price_amount)

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
            print(json.loads(accept.text)["message"])
        except Exception:
            # Throw up a pop-up if you get a block, showing the date, time, and pay
            keepTrying = False
            return app.infoBox(
                "Got One", f"{startTime}\n{block_length}\n${price_amount}"
            )


if __name__ == "__main__":

    while keepTrying:
        try:
            flex_grabber()
            time.sleep(1)
        except KeyError:
            break