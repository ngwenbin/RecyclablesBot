import telegram, sys, os, time
from dotenv import load_dotenv
from google.cloud import firestore
from shards import Shard, Counter
from order import Orders
from user import Users

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
db = firestore.Client() # initiates firestore db client

def send_message(user_id):
    TOKEN = "1068793031:AAHJdDT21UGx7eommP-WTP0ozX5jdmt9or4"
    CHAT_ID = user_id

    bot = telegram.Bot(token = TOKEN)
    bot.sendMessage(
        chat_id = CHAT_ID,
        text = "*Hey there!* We have some awesome news to share! 🎉🎉\n\nRecyclables have now expanded to selected regions "\
                "in Bukit Batok, Bukit Panjang and Holland Village!"\
                "\n\nSchedule a collection today and start creating impacts."\
                "\nEmpower others by sharing us with your family and friends!"\
                "\n\nFor more info, visit: https://www.recyclables.sg",
        parse_mode ='Markdown'
    )

# broadcasting purposes
doc_ref = db.collection(u'users').stream()
for doc in doc_ref:
    user_id = f'{doc.id}'
    print(user_id)
    send_message(user_id)
    time.sleep(1)
print("Done!")