import telegram, sys, os, gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import firestore

"""
Distributed shards counter to allow more than 1 writes per second.
"""
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
db = firestore.Client()
class Shard(object):
    def __init__(self):
        self._countfri = 0
        self._countsat = 0
        self._totalorders = 0
        self._totalusers = 0

    def to_dict(self):
        return {"count_fri": self._countfri,
                "count_sat": self._countsat,
                "totalorders": self._totalorders,
                "totalusers": self._totalusers}

class Counter(object):
    def __init__(self, num_shards):
        self._num_shards = num_shards

    def init_counter(self, doc_ref):
        col_ref = doc_ref.collection("shards")
        for num in range(self._num_shards):
            shard = Shard()
            col_ref.document(str(num)).set(shard.to_dict())

    def clear_friday(self, doc_ref):
        for i in range(self._num_shards):
            shard_ref = doc_ref.collection(u'shards').document(str(i))
            shard_ref.update({"count_fri": 0})

    def clear_saturday(self, doc_ref):
        for i in range(self._num_shards):
            shard_ref = doc_ref.collection(u'shards').document(str(i))
            shard_ref.update({"count_sat": 0})

shard_counter = Counter(10)

def clearfri(event, context):
    shard_counter.clear_friday(db)

def clearsat(event, context):
    shard_counter.clear_saturday(db)

def get_orders():
    ## gspread
    gc = gspread.service_account(filename='credentials.json')

    sheet = gc.open("Recyclables (Database)").worksheet("Orders")
    data = sheet.get_all_values()
    ## pandas
    df = pd.DataFrame(data) # contains data from the entire sheet
    orders_data = df.iloc[4:] # contains data from the table of orders
    orders = pd.DataFrame(list(zip(orders_data[2], orders_data[4], orders_data[6], orders_data[7])), columns=['recyclables', 'address', 'weeknum', 'weekday']) # contains relevant data to show KG
    orders_today = orders[(orders.weeknum == str(df[4][0])) &
                        (orders.weekday == str(df[4][1]))] # contains exact data to show KG
    final_orders = ''
    for i in range(len(orders_today)):
        final_orders += '*{} {}:*\n'.format('Order', str(i + 1))
        address = orders_today.address.iloc[i].split('\n')
        add ='{} {} S({})'.format(address[0], address[1], address[2])
        final_orders += add + '\n'
        final_orders += orders_today.recyclables.iloc[i].split('\n')[0] + '\n\n'
    return final_orders

def send_message(event, context):
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    # TEST_TOKEN = os.getenv("TEST_TOKEN")
    # TEST_CHATID = os.getenv("TEST_CHATID")

    bot = telegram.Bot(token = TOKEN)
    # bot = telegram.Bot(token = TEST_TOKEN)
    bot.sendMessage(
        chat_id = CHAT_ID,
        # chat_id = TEST_CHATID,
        text = "*🚨 These are your orders for today:*\n\n" + get_orders(),
        parse_mode ='Markdown'
    )
