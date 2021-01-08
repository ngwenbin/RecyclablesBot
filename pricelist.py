import requests

def get_price(regionid, itemid, API_TOKEN):
    URL = "https://us-central1-recyclables-telegram-bot.cloudfunctions.net/app/api/getPrices/"+regionid+"/"+itemid
    headers = {"Authorization": "Bearer " + API_TOKEN}
    r = requests.get(url=URL, headers=headers)
    return(r.json()['price'])