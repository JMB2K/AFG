import requests
import json
import time
from datetime import datetime
from appJar import gui

# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    'x-amz-access-token': 'Atna|EwICIMk-QAxUAGRRg_D75sr67JCV672l6r3HQ1LWbqES_KWObx0-k4CleFKUpcAaV_xPPnExTHkiPbHJgkN98RjE7mdxEGoZ7DaM9tzPfDUObZqpKBaQ6Vft3A_9TuggTCIG97OVE3S_Q4Vfw8bGSxxE8v_n7KNjClyLjCMecYwbXYcrg8fFye7WXcYKNNjZEuHn2n65JGfleB3NB-X3xfoP5HvHJb83mUP1-RjUG0bl0wTcIZbri34kCqpJzQBNpy5K095cwP4u7Hhifz5b-X-_UTdJ-OGurl0TfjJw9i5wn2690MC5AcoQp9l4kh4jdLYDk9nj9LEN_fRCsho5Gu7Uzb-9',
    'X-Amzn-RequestId': '2a783516-5107-4fd5-abc6-4df616e0b7d4',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S3B1.220218.004) RabbitAndroid/3.71.1.48.0',
    'X-Flex-Client-Time': '1647656899821',
    'x-flex-instance-id': '0604c7e6-8177-4b8d-8b64-cf0c5cff6023',
    'Authorization': 'RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=c38dd16dc54d68f2b8235295387780007db5376251a9870ae4ee40a4d7bfbbbe',
    'Host': 'flex-capacity-na.amazon.com',
    'X-Amz-Date': '20220318T212819Z',
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
        if i["startTime"] - int(time.time()) < 1500 or price_amount / block_length < 35 or block_length > 4:
            continue

        offerID = i["offerId"]
        blockPay = price_amount
        startTime = datetime.fromtimestamp(i["startTime"])
        blockDuration = block_length
        print(block_length, blockPay)

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
            time.sleep(.5)
            stalls = 0
        except Exception as E:
            stalls += 1
            if stalls == 2:
                break
            print('RESTING')
            time.sleep(300)
