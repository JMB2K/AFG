import requests
import json
import time
from datetime import datetime
from appJar import gui

# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    'x-amz-access-token': 'Atna|EwICIB8ipfqXlfUc8PKWXJFO5T0fZdVgzCvK60hwNsC1UrJ839Z_5vgNRhQeuRZsB6okaWfNb2xRyi8eYBONn1GrEEVT2QiqxF42nKUSS2ktxmvtICQiaN-LRBlk4OH4VTOlkVucRCmg1yQgBti6NOyvgKMfUBRntYiIwvFF8-_8rXmULuB06X9Lvu0jnKBteBSmqV60k7LbuMqVguBdw-E7AFi4GFNIbswI99d3pOZb8C5Xr4mPJ-ZkQzeVC-zZT4GiqlvoCnl0PfanD0jUfuBsYhz-gaG1V61pW8JzWxI9XtnfiZLSWzOHfE-Ncvnd1uWBEPlNpBcSRyQwwrFlfj8UQC4H',
    'X-Amzn-RequestId': '7a261edd-86e8-4cdd-95b5-24f902e9284a',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S3B1.220218.004) RabbitAndroid/3.71.1.48.0',
    'X-Flex-Client-Time': '1647659957500',
    'x-flex-instance-id': '0604c7e6-8177-4b8d-8b64-cf0c5cff6023',
    'Authorization': 'RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=cfbdfe7b6e0b2a29459bbf47926cb491a6d2164993b9e636d19f85b3fea3a349',
    'Host': 'flex-capacity-na.amazon.com',
    'X-Amz-Date': '20220318T221916Z',
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
        raise KeyError(j)

    for i in [block for block in offer_list if not block["hidden"]]:
        block_length = (i["endTime"] - i["startTime"]) / 3600
        price_amount = i["rateInfo"]["priceAmount"]
        # Making sure not to accept anything that starts less than 25 minutes from current time or anything under $30/hr
        if i["startTime"] - int(time.time()) < 1500 or price_amount / block_length < 35 or price_amount < highPay or block_length > 4:
            continue

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


if __name__ == '__main__':
    rounds = 1
    stalls = 0
    while keepTrying:
        try:
            flex_grabber()
            print(rounds)
            rounds += 1
            time.sleep(.75)
            stalls = 0
        except Exception as E:
            stalls += 1
            if stalls == 2:
                break
            print('RESTING')
            time.sleep(90)
