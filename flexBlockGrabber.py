import requests
import json
import time
from datetime import datetime


# You must run the app on your phone and catch the packet, convert it at "https://curlconverter.com/#" and replace this info with it, then comment out date and time
headers = {

}


del headers['X-Flex-Client-Time']
del headers['X-Amz-Date']

accessToken = headers["x-amz-access-token"]
highPay = 0
offerID = ""
keepTrying = True


def blockSearch(headers):
    global highPay, offerID, keepTrying
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
    try:
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
    except Exception as E:
        print (j['message'])
        keepTrying = False

    if highPay > 115:
        print("GotOne", highPay)
        acceptOffer(offerID, accessToken)
        highPay = 0
    else:
        # Reset high pay for next loop through refreshed list of offers
        highPay = 0


def acceptOffer(offerID, accessToken, headers=headers):

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
    acceptedOffer = json.loads(r.text)
    try:
        contentCheck = acceptedOffer["message"]
    except Exception as E:
        print("GOT EM COACH!")
        print(E)
        keepTrying = False


while keepTrying:
    blockSearch(headers)
    #time.sleep(1)
