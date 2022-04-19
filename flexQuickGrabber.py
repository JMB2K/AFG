import requests
import json
import time
from datetime import datetime
from appJar import gui
import random
# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    'x-amz-access-token': 'Atna|EwICIAKumvHftIBbjtj-RiccpLnMydPloWNbRtvyxMSf2uFhQonYlouJrIMiaYpDGHtM1uZE_IBd763G7gviVnU_etZ2xI2XgvZjoHdp7LEXSfXAL0naThYlgmvBeO-XFU3FjkqnCHduWUvCRHmOhMTjhS1_4W70iwq-3LWLN38HcKNuWBOh-YTzU-WwdUApwui-oUw7XcBfsEe8eA-U4mEjEnKq0bMpXnHjx-YJ23YWrE6-kB5lBFK2tsZFfwSslowQLImKYxjXAm1yXbXvdvDXaQO1S_ZUunt9GvZhkAdKjGzsZG0hAbJInPo7QTqrxKxZyVRY-1DKgTi8sWdj7R36abKDJzD8bamvNbzjgZTIXsZzlq63pm62vwAtvs4oVjAYfL-vG_wBJahrHteM0N4uVkCv',
    'X-Amzn-RequestId': '504d5b0e-3e51-4e7f-a990-64f6fd657698',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S3B1.220218.006) RabbitAndroid/3.72.1.25.0',
    'X-Flex-Client-Time': '1650167899284',
    'x-flex-instance-id': '0604c7e6-8177-4b8d-8b64-cf0c5cff6023',
    # Already added when you pass json=
    # 'Content-Type': 'application/json',
    'Authorization': 'RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=09939bd47eac638e6dd6c1e0628ca782753543a08ffe46733dfaf7fef8b80ec4',
    'Host': 'flex-capacity-na.amazon.com',
    'X-Amz-Date': '20220416T225816Z',
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
        if i["startTime"] - int(time.time()) < 1500 or price_amount / block_length < 25:
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
            print(price_amount, block_length)
        except Exception:
            # Throw up a pop-up if you get a block, showing the date, time, and pay
            keepTrying = False
            return app.infoBox(
                "Got One", f"{startTime}\n{block_length}\n${price_amount}"
            )


if __name__ == "__main__":

    #break_time = [.25,.33,.5,.66,.75]

    while keepTrying:
        try:
            flex_grabber()
            #time.sleep(random.choice(break_time))
        except KeyError:
            break