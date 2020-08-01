import telegram, sys, os, gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

def get_orders():
    ## gspread
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    gc = gspread.authorize(creds)

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
    TOKEN = '1086519799:AAE4YR2kZWP6dicS5AmKDGUgTKzYFSJLnEc'
    CHAT_ID = -1001427022537

    bot = telegram.Bot(token = TOKEN)
    bot.sendMessage(
        chat_id = CHAT_ID,
        text = "*🚨 These are your orders for today:*\n\n" + get_orders(),
        parse_mode ='Markdown'
    )
