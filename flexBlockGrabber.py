import requests
import json
import time
from datetime import datetime
from appJar import gui

# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {
    "x-amz-access-token": "Atna|EwICIJB4dE_PgINdG8H5eQTt0C6OpSDriHfi1HbpIDem218z61W8OCTAihAhdcTcCqWznNKBo_Bxr-TnBHVVInCyIH9ED8o8syzYJwiX6CCzboVwikdpAJ1nnNZfMMzmtCE5B-mABKQeKQs_eGPyyj_6F1paRtxuhTzUDTB4HyunOkYGWgpt1YDPSJzdtSTRXZ2JRF0r55zWZiBM54p7jGjKFfqBkx94ry-1ENaxORm4bcTzfUnDpJU0Wm7b-18otH4vt3wApddzdx2HDwDpPcgQm9j54twDfJEEQe8_sc8EaVoAOta7ZaHzn-pbCCPdXXN0ZLah2GsdbkxevwPpMxNDyHA7",
    "X-Amzn-RequestId": "febb3a20-88c6-49ec-b00a-4f6edbb5ab8e",
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 6 Build/S2B3.220205.007.A1) RabbitAndroid/3.70.2.4.0",
    "X-Flex-Client-Time": "1646000035733",
    "x-flex-instance-id": "0604c7e6-8177-4b8d-8b64-cf0c5cff6023",
    "Authorization": "RABBIT3-HMAC-SHA256 SignedHeaders=host;x-amz-access-token;x-amz-date;x-amzn-requestid,Signature=0c561698bdc60529c7a1787aadef7025a0dd5722082afdb6abfe674c2054889c",
    "Host": "flex-capacity-na.amazon.com",
    "X-Amz-Date": "20220227T161353Z",
}

del headers["X-Flex-Client-Time"]
del headers["X-Amz-Date"]

accessToken = headers["x-amz-access-token"]
highPay = 0
offerID = ""
keepTrying = True
startTime = ""
blockDuration = 0
blockPay = 0
app = gui()


def blockSearch(headers=headers):
    global highPay, offerID, keepTrying, startTime, blockDuration, blockPay
    # This json_data is copied from a packet but remains the same, no need to change it
    json_data = {
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
        json=json_data,
    )

    j = json.loads(response.text)
    # Looping through the available offers
    for i in j["offerList"]:
        # Making sure not to accept anything that starts less than 25 minutes from current time
        if i["startTime"] - int(time.time()) < 1500:
            continue
        blockLength = (i["endTime"] - i["startTime"]) / 3600
        priceAmount = i["rateInfo"]["priceAmount"]
        # Filtering out blocks from locations I don't want to pick up from and block lengths over 4 hours, and making sure it's the highest paying offer
        if blockLength <= 4 and not i["hidden"] and priceAmount > highPay:
            highPay = priceAmount
            offerID = i["offerId"]
            blockPay = priceAmount
            startTime = datetime.fromtimestamp(i["startTime"])
            blockDuration = blockLength

    if highPay > 105:
        acceptOffer(offerID, accessToken)
        highPay = 0
    else:
        # Reset high pay for next loop through refreshed list of offers
        highPay = 0


def acceptOffer(offerID, accessToken, headers=headers):
    global keepTrying

    json_data = {
        "__type": "AcceptOfferInput:http://internal.amazon.com/coral/com.amazon.omwbuseyservice.offers/",
        "offerId": offerID,
    }
    # Sending acceptance of offer
    r = requests.post(
        "https://flex-capacity-na.amazon.com/AcceptOffer",
        headers=headers,
        json=json_data,
    )
    # Checking response to confirm offer was accepted in time or if someone else got it, it includes a message if you missed it and is null if you got it
    try:
        acceptedOffer = json.loads(r.text)["message"]
    except Exception as E:
        # Throw up a pop-up if you get a block, showing the date, time, and pay
        keepTrying = False
        return app.infoBox("Got One", f"{startTime}\n{blockDuration}\n${blockPay}")


while keepTrying:
    blockSearch()
    # time.sleep(1)
