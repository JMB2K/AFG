import requests
import json
import time
from datetime import datetime
from appJar import gui
import random

# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    'x-amz-access-token': 'Atna|EwICIMjzNmO54MjUlGk0rlw1Dxw3JqbCL3WJMipQ532UUdxmBk3OoNii8M_9HzDV7AFK-AuiAlTTGovF2igV1_eYCERFyY4DuFs1OlIAtuhIC9Wb5jfoUShFNU6WX2DrUMswlPYMrD9pVy6rjayAZhG9c_qJr499MHoL2dPy-g8s6AjdfEj7O5IdXyF1Z6pARj6P_kRHxuoT0l-iYjIes4AvQCo2V9xUgdjERxa1cFa0kS2mCoH9Rk8AWHAKwRFPYxyZg7dXLI3MI1r2LN5vWVNN7UNKCcR44IhtyS-lxEwH2yR31pzGrhBLaciEf5c5hha6fR34u4CIClwk1sAzACujmAoeJ19BGqUrg2JtbjOvuLQqX1t1hShyCJyuoNMKBU-nXRAcaIOu4UXTuyn0PixF8Zim',
    'X-Amzn-RequestId': '363cdba6-31f3-409f-bdd7-516f6b005a31',
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S3B1.220218.006) RabbitAndroid/3.72.1.25.0',
    'X-Flex-Client-Time': '1649832484485',
    'x-flex-instance-id': '0604c7e6-8177-4b8d-8b64-cf0c5cff6023',
    # Already added when you pass json=
    # 'Content-Type': 'application/json',
    'Authorization': 'RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=2e81b6429577f6c3ec67588d538ce23b8b24ab055b7b96b422ab2b3325eb2d26',
    'Host': 'flex-capacity-na.amazon.com',
    'X-Amz-Date': '20220413T014804Z',
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
        map(print, [(x['endTime']-x['startTime']//3600, x['rateInfo']['priceAmount']) for x in offer_list])
    except KeyError:
        raise KeyError(j)

    for i in [block for block in offer_list if not block["hidden"]]:
        block_length = (i["endTime"] - i["startTime"]) / 3600
        price_amount = i["rateInfo"]["priceAmount"]
        # Making sure not to accept anything that starts less than 25 minutes from current time or anything under $30/hr
        if (
            i["startTime"] - int(time.time()) < 1500
            or price_amount / block_length < 27
            or price_amount < highPay
        ):
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
            print(json.loads(accept.text)["message"])
            highPay = 0
        except Exception:
            # Throw up a pop-up if you get a block, showing the date, time, and pay
            keepTrying = False
            return app.infoBox("Got One", f"{startTime}\n{blockDuration}\n${blockPay}")


if __name__ == "__main__":
    #breaks = [.25, .33, .5, .67, .75, 1]
    #rounds = 1
    stalls = 0
    while keepTrying:
        try:
            flex_grabber()
            #print(rounds)
            #rounds += 1
            time.sleep(random.choice(breaks))
            stalls = 0
        except Exception as E:
            stalls += 1
            if stalls == 2:
                break
            print("RESTING")
            time.sleep(600)
 
