import gspread, re, logging, telegram.bot, os, requests, time
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, KeyboardButton, ChatAction)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
from telegram.ext import messagequeue as mq
from dotenv import load_dotenv
from google.cloud import firestore
from shards import Shard, Counter
from order import Orders
from user import Users
from pricelist import paperprice, clothesprice

# load env file
load_dotenv()

gc = gspread.service_account(filename='credentials.json')
sheet2 = gc.open("Recyclables (Database)").worksheet("Orders")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

# Global stuff
db = firestore.Client() # initiates firestore db client
shard_counter = Counter(10) # Initiates shard counts
TOKEN = os.getenv("TELEGRAM_TOKEN")
GRPCHATID = os.getenv("GROUPCHAT_ID")
API_TOKEN = os.getenv("API_TOKEN")
userdatas = {} # global user dict

class MQBot(telegram.bot.Bot): # Class handler for message queue

    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()

        except:
            pass

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        return super(MQBot, self).send_message(*args, **kwargs)


# ------------- State management -------------

# First level states
REGISTER, REGISTERYES, REGISTERNO, MAIN_MENU, RECYCLE, INFO, HELP, MY_ORDER = map(chr, range(8))
# Sub second level state
POSTAL, ADDRESS, UNIT = map(chr, range(8, 11))
# Second level states
HELPS, FAQ, CONTACT, CHANGE_ADDRESS, END_HELPS, PROCEED = map(chr, range(11, 17))
# Second level states
INFOS, ABOUT, PRIVACY, END_INFO = map(chr, range(17, 21))
# Second level states
RECYCLABLES, ITEM_PAPERS, ITEM_ELECTRONICS, ITEM_CLOTHES = map(chr, range(21, 25))
# Second level states - past orders
MY_ORDERS, CHECK_ORDERS, END_MY_ORDERS = map(chr, range(25, 28))
# Third level states
WEIGHT, CONFIRM, SELECT_DATE, CLEAR_ITEM, CLEAR, END_CLEAR, END_ELECTRONICS = map(chr, range(28, 35))
# Fourth level states
DATES, AGREEMENT, END_AGREEMENT = map(chr, range(35, 38))
# Fifth level states
CONFIRM_ORDER, CHECKOUT = map(chr, range(38, 40))
# Constants
(START_OVER, PAPERS, CLOTHES, DAYS, TIMES, BASKET,
 ITEM_TYPE, ROW, FULL_ADDRESS) = map(chr, range(40, 49))
# Meta states
STOPPING = map(chr, range(49, 50))
# Paper meta states
PAPER1, PAPER2, PAPER3, PAPER4 = map(chr, range(4))
# Clothes meta states
CLOTHES1, CLOTHES2, CLOTHES3, CLOTHES4 = map(chr, range(4, 8))
# Choices meta states
CHOICE1, CHOICE2 = map(chr, range(8, 10))

END = ConversationHandler.END

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Formatting of user data cache
def address_format(user_data):
    data = list()
    for key, value in user_data.items():
        if key == 'Postal code' or key == 'Address' or key == 'Unit':
            data.append('{}: {}'.format(key, value))
    return "\n".join(data).join(['\n', '\n'])

def item_format(user_data):
    items = list()
    for key, value in user_data.items():
        if key == PAPERS or key == CLOTHES:
            items.append('{}'.format(value))
    return "\n".join(items)

def final_address_format(text):
    data = list()
    for i in text:
        data.append('{}'.format(i))
    return "\n\n".join(data)

# Builds dynamic keyboard
def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

# Main functions
def start(update, context):

    main_text = "*Recyclables* can help you to schedule "\
                "recycling collections with a karang guni conveniently!"\
                "\n\nThrough *Recyclables*, you can help the environment "\
                "while increasing the productivity "\
                "of our local karung gunis."\
                "\nIn addition to that, you can receive "\
                "incentives for your recyclables! ☺️"\
                "\n\nHow can I help you?"

    register_text = "*Oops! Looks like you are not registered with us.*"\
                    "\n\nIn order to use Recyclables,"\
                    "\nI will need your residential address for registration purposes."\
                    "\n\nWe are currently running a trial run and are only operating in:"\
                    "\n📍 Choa Chu Kang"\
                    "\n📍 Yew Tee"\
                    "\n\n*Would you like to proceed?*"\
                    "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding."

    basket_text = "\n\n_You still have item(s) in your basket.\nDon't forget!_"

    main_keyboard = [[InlineKeyboardButton("♻️  Start recycling!", callback_data=str(RECYCLE))],
                     [InlineKeyboardButton( "📋  Info", callback_data=str(INFO))],
                     [InlineKeyboardButton("🙋🏻‍♀️  Help", callback_data=str(HELP))],
                     [InlineKeyboardButton("📋 My Orders (Testing)", callback_data=str(MY_ORDER))],
                     [InlineKeyboardButton("« Exit", callback_data=str(END))]]

    main_markup = InlineKeyboardMarkup(main_keyboard)

    reg_keyboard = [[InlineKeyboardButton("Yes", callback_data=str(REGISTERYES))],
                    [InlineKeyboardButton("No", callback_data=str(REGISTERNO))]]

    reg_markup = InlineKeyboardMarkup(reg_keyboard)

    if context.user_data.get(START_OVER): #To alert users who goes back to main with items in basket
        if context.user_data.get(BASKET):
            text = main_text + basket_text
        else:
            text = main_text
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=main_markup
        )
        context.user_data[START_OVER] = False
        return MAIN_MENU

    else:
        userids = str(update.effective_user.id)
        doc_ref = db.collection(u'users').document(userids)
        doc = doc_ref.get()
        update.message.reply_text(
            "*Hello " + str(update.message.from_user.first_name) +
            "!* 👋🏻 \nWelcome to Recyclables!",
            parse_mode="Markdown"
        )
        if doc.exists: # If user document exists
            userdatas.clear() # Clears global dict
            userdatas.update(doc.to_dict()) # Updates global dict with user data dict from firestore
            update.message.reply_text(
                text=main_text,
                parse_mode="Markdown",
                reply_markup=main_markup
            )
            return MAIN_MENU

        else:
            update.message.reply_text(
                text=register_text,
                reply_markup=reg_markup,
                parse_mode="Markdown"
            )
            return REGISTER


def my_order(update, context):
    keyboard = [[InlineKeyboardButton("📋 Check My Orders (Testing)", callback_data=str(CHECK_ORDERS))],
                [InlineKeyboardButton("« Back", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Hi, what would you like to do?",
        reply_markup=reply_markup
    )
    return MY_ORDERS

def check_past_orders(update, context):
    userids = str(update.effective_user.id)
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # get all orders whose userid field == current user
    # orders_collection_ref = db.collection(u'orders').where(u'userid', u'==', userids).stream()
    # test on user ids in orders collection
    orders_collection_ref = db.collection(u'orders').where(u'userid', u'==', '1298210408').stream()
    ordersString = ''
    i = 1
    for order in orders_collection_ref:
        # is there more efficient concatenation methods?
        strings = ["\nOrder", str(i), ": \nAddress: ", f'{order.to_dict().get("address")}', "\nRecycling: ", f'{order.to_dict().get("item")}', "\nDate: ", f'{order.to_dict().get("timeslot")}']
        ordersString = ordersString + ' '.join(strings)
        i += 1
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Here are your order details: " + ordersString,
        reply_markup=reply_markup
    )
    return MY_ORDERS

def recycle(update, context):
    keyboard = [[InlineKeyboardButton("🗞  Papers ", callback_data=str(ITEM_PAPERS))],
                [InlineKeyboardButton("👕  Clothes ", callback_data=str(ITEM_CLOTHES))],
                [InlineKeyboardButton("📱  Electronics ", callback_data=str(ITEM_ELECTRONICS))],
                [InlineKeyboardButton("« Back to main menu", callback_data=str(END))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Please select the type of recyclables\n you wish to recycle:"\
        "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        reply_markup=reply_markup
    )
    return RECYCLABLES


def papers(update, context):
    update.callback_query.answer(
        text="Do note that we do not accept cardboards/ cartons.",
        show_alert=True)
    keyboard = [[InlineKeyboardButton("10KG to 20KG", callback_data=str(PAPER1))],
                [InlineKeyboardButton("20KG to 30KG", callback_data=str(PAPER2))],
                [InlineKeyboardButton("30KG to 40KG", callback_data=str(PAPER3))],
                [InlineKeyboardButton("40KG to 50KG", callback_data=str(PAPER4))],
                [InlineKeyboardButton("« Back to recyclables", callback_data=str(END))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text=("*Please select an estimated weight of your papers:*"\
                "\n\nCurrent prices:\n"\
                "_${} per KG_\n"\
                "\nNeed help in estimating the weight?"\
                "\nClick [here](https://i.imgur.com/6zd9K5P.png)!"\
                "\n\n*IMPORTANT: Please remove any plastic covers/binders etc and our Karung guni uncles would really "\
                "appreciate if you can separate any* [waxy-shiny paperback covers on textbooks/ books](https://i.imgur.com/euQGxUb.png) *if POSSIBLE.*"\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.".format(paperprice)),
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    return WEIGHT


def clothes(update, context):
    update.callback_query.answer(
        text="We only accept normal civilian clothings as they are meant to be reused. Items such as but not limited to school/ work uniforms, canvas bags etc are not acceptable",
        show_alert=True)
    keyboard = [[InlineKeyboardButton("10KG to 20KG", callback_data=str(CLOTHES1))],
                [InlineKeyboardButton("20KG to 30KG", callback_data=str(CLOTHES2))],
                [InlineKeyboardButton("30KG to 40KG", callback_data=str(CLOTHES3))],
                [InlineKeyboardButton("40KG to 50KG", callback_data=str(CLOTHES4))],
                [InlineKeyboardButton("« Back to recyclables", callback_data=str(END))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text=("*Please select an estimated weight of your clothes:*"\
                "\n\nCurrent estimated prices:"\
                "\n_${} per KG_"\
                "\n\n*IMPORTANT: We only accept normal civilian clothings as they are meant to be reused. "\
                "Items such as but not limited to school/ work uniforms, canvas bags etc are not acceptable*"\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.".format(clothesprice)),
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    return WEIGHT


def get_link(name, address):
    link = 'https://docs.google.com/forms/d/e/1FAIpQLSe0HciAG8IvZtwIdO4qHvfJwhEdul7MG7UiNgo54wj4dNaW2w/viewform?usp=pp_url'\
        '&entry.1325814690=&entry.1717383728='
    link = link.replace('1325814690=', '1325814690=' + name)
    link = link.replace('1717383728=', '1717383728=' + address)
    return link


def electronics(update, context):
    name = str(update.effective_user.first_name)
    address = (userdatas['address'], userdatas['unit'], userdatas['postal'])
    full_address = ", ".join(address)
    update.callback_query.answer(
        text="Electronic recycling will be done via google forms."\
                "A list of acceptable items is listed on the forms"\
                "\n\nDo note that electronics recycling requests are processed manually.",
        show_alert=True)
    keyboard = InlineKeyboardButton(" « Back", callback_data=str(END))
    reply_markup = InlineKeyboardMarkup.from_button(keyboard)

    update.callback_query.edit_message_text(
        text=("Please fill in the form in [this link](" +
              get_link(name, full_address) + ") to receive a quotation."),
        # "https://forms.google.com/e_waste"),
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    return END_ELECTRONICS


def _item_text(item):
    paperTypes = [PAPER1, PAPER2, PAPER3, PAPER4]
    clothesTypes = [CLOTHES1, CLOTHES2, CLOTHES3, CLOTHES4]

    if item in paperTypes:
        pos = paperTypes.index(item) + 1
        text_item = ('Papers ({0}KG to {1}KG)'
                 '\n${2} per KG'.format((pos)*10,
                                         (pos+1)*10,
                                            paperprice))
    else:
        pos = clothesTypes.index(item) + 1
        text_item = ('Clothes ({0}KG to {1}KG)'
                 '\n${2} per KG'.format((pos)*10,
                                         (pos+1)*10,
                                            clothesprice))

    return text_item


def item_basket(update, context):
    user_data = context.user_data
    context.user_data[BASKET] = True

    if context.user_data.get(START_OVER):
        # For item name updates
        context.user_data[START_OVER] = False

    else:
        item = update.callback_query.data
        context.user_data[ITEM_TYPE] = item
        itemtype = _item_text(item)

        if re.match("Papers", itemtype):
            context.user_data[PAPERS] = itemtype
            update.callback_query.answer(text="Papers added!", show_alert=True)

        elif re.match("Clothes", itemtype):
            context.user_data[CLOTHES] = itemtype
            update.callback_query.answer(
                text="Clothes added!", show_alert=True)

    keyboard = [[InlineKeyboardButton("🗓 Select date", callback_data=str(SELECT_DATE))],
                [InlineKeyboardButton("➕  Add item(s)", callback_data=str(END))],
                [InlineKeyboardButton("➖  Clear item(s)", callback_data=str(CLEAR_ITEM))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=("*Your current recyclables:*\n{}"\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.".format(item_format(user_data))),
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    if PAPERS not in user_data and CLOTHES not in user_data:
        context.user_data[BASKET] = False
    return CONFIRM


def clear_item(update, context):
    keyboard = [[InlineKeyboardButton("🗞  Papers ", callback_data=str(CHOICE1))],
                [InlineKeyboardButton("👕  Clothes ", callback_data=str(CHOICE2))],
                [InlineKeyboardButton("« Back", callback_data=str(END_CLEAR))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Please select the item you wish to clear:",
        reply_markup=reply_markup
    )
    context.user_data[START_OVER] = True
    return CLEAR


def clear_confirm(update, context):
    choice = update.callback_query.data
    if choice == CHOICE1:
        context.user_data.pop(PAPERS, None)
        text = "Papers cleared!"
    elif choice == CHOICE2:
        context.user_data.pop(CLOTHES, None)
        text = "Clothes cleared"

    update.callback_query.answer(
        text=text,
        show_alert=True
    )
    return CLEAR


def date_selection(update, context):
    user_data = context.user_data
    context.bot.send_chat_action(
        chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    context.user_data[START_OVER] = True
    URL = "https://us-central1-recyclables-telegram-bot.cloudfunctions.net/app/api/getDates/5/6"
    headers = {"Authorization": "Bearer " + API_TOKEN}
    try:
        gc.login()
        sheet3 = gc.open("Recyclables (Database)").worksheet("Postals")
        sheet3.find(userdatas['postal'])

        if context.user_data.get(BASKET):
            r = requests.get(url=URL, headers=headers)
            try:
                date_data = r.json()
                keyboard_button = []

                for i in date_data['dates']:
                    keyboard_button.append(InlineKeyboardButton(i, callback_data=i))

                reply_markup = InlineKeyboardMarkup(build_menu(keyboard_button, n_cols=1))
                text = "*Please select your preferred date:*"\
                    "\n\nType /cancel to exit the bot."
                update.callback_query.edit_message_text(
                    text=text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )

            except:
                text = "*We are fully booked! Please try again next week!*"\
                        "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding."

                update.callback_query.edit_message_text(
                    text=text,
                    parse_mode='Markdown',
                )
            update.callback_query.answer()
            return DATES

        else:
            update.callback_query.answer(
                text="You cannot proceed to select date"\
                    " with nothing in your basket!"\
                    "\n\nPlease add items into your basket.",
                show_alert=True
            )
            return END

    except gspread.exceptions.CellNotFound:  # gspread exceptions
        text = "Sorry! You are unable to proceed as your region is currently not available!"\
                "\n\nWe are currently running a trial run and are only operating in:"\
                "\n📍 Choa Chu Kang"\
                "\n📍 Yew Tee"\
                "\n\nFollow us on [Instagram](https://www.instagram.com/recyclables.sg/) or [Facebook](https://www.facebook.com/recyclables.sg/) for updates!"\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding."
        keyboard = [[InlineKeyboardButton("« Back to item basket", callback_data=str(END))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        return DATES


def agreement(update, context):
    user_data = context.user_data
    if user_data.get(START_OVER):
        user_data[DAYS] = update.callback_query.data
    else:
        context.user_data[START_OVER] = True

    keyboard = [[InlineKeyboardButton("Yes, I agree", callback_data=('agree')),
                 InlineKeyboardButton("« Back to select date", callback_data=str(END_AGREEMENT))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="*Please do ensure your recyclables are reasonably accurate to the weight indicated*."\
                "\n\nBy proceeding you agree that your items are within our requirements and our Karung Guni uncles have the right to refuse them if they are not."\
                "\n\nCollection timing will be between 11am to 2pm."\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    return AGREEMENT


def basket_confirm(update, context):
    user_data = context.user_data
    user_data[START_OVER] = False
    #times = update.callback_query.data
    #user_data[TIMES] = times
    days = user_data[DAYS]
    address = (userdatas['address'], userdatas['unit'], userdatas['postal'])
    full_address = "\n".join(address)

    text = ("*Your current order is as follows:*\n"\
            "Item basket:\n_{0}_"\
            "\n\nCollection address:\n{1}"\
            "\n\nCollection details:\n{2}"\
            "\n11am to 2pm".format(item_format(user_data),
                                   full_address,
                                   days))
    end_text = "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding."
    keyboard = [[InlineKeyboardButton("🛒  Checkout", callback_data=str(CHECKOUT)),
                 InlineKeyboardButton("« Back", callback_data=str(END))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=text+end_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    userdatas['fulladdress'] = full_address
    return CONFIRM_ORDER


def success(update, context):
    user_data = context.user_data
    gc.login()
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    userids = str(update.effective_user.id)
    username = str(update.effective_user.username)
    item = item_format(user_data)
    full_address = userdatas['fulladdress']
    timeslot = user_data[DAYS]
    timestamp = str(int(time.time()))
    ordernum = timestamp + "U" + userids

    if re.match(r"\b(\w*fri\w*)\b", timeslot, re.I):
        shard_counter.increment_friday(db)
    elif re.match(r"\b(\w*sat\w*)\b", timeslot, re.I):
        shard_counter.increment_saturday(db)

    header_text = ("*Your order has been confirmed! 👍🏻\n\n*")

    order_text = ("*Order No. #O{}*"\
                  "\n-------------------------".format(ordernum))

    item_text = ("\n*Recyclables to be collected:*\n{}".format(item))

    collection_add = ("\n\n*Collection address:*\n{}".format(full_address))

    collection_detail = ("\n\n*Collection details:*\n{0}"\
                         "\n11am to 2pm".format(timeslot))

    end_text = "\n\n_Message @RecyclablesHelpBot on Telegram for any order related enquiries!_"

    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=header_text + order_text + item_text +
            collection_add + collection_detail + end_text,
        parse_mode="Markdown"
    )

    # this is for order message notification
    bot = context.bot
    bot.send_message(chat_id=GRPCHATID,
                     parse_mode="Markdown",
                     text=order_text+item_text+collection_add+collection_detail)

    db.collection(u'orders').document(ordernum).set(Orders(userids, username, ordernum, item, timeslot, timestamp, full_address).orders_to_dict())
    shard_counter.increment_order(db)
    sheet2.append_row([ordernum, userids, item, timeslot, full_address], value_input_option="RAW")
    user_data.clear()
    userdatas.clear()
    return STOPPING


def failure(update, context):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text(
        "Sure thing, no worries!"
    )
    return STOPPING


def info(update, context):
    keyboard = [[InlineKeyboardButton("👥 About Us", callback_data=str(ABOUT))],
                [InlineKeyboardButton("🔐 Privacy policy",
                                      callback_data=str(PRIVACY))],
                [InlineKeyboardButton("« Back", callback_data=str(END))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="What info would you like to see?"
        "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        reply_markup=reply_markup
    )
    return INFOS


def info_privacy(update, context):
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END_INFO))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="We treat your data very seriously. Do visit our [Facebook](https://www.facebook.com/recyclables.sg/) page for more information."\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    return INFOS


def info_about(update, context):
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END_INFO))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Hello 👋🏻! We are a group of NUS students from NUS Social Impact Catalyst.\n\n"\
                "Our goal is to improve Singapore’s domestic recycling efforts by "\
                "partnering with the local karung guni community. "\
                "By bridging the gap between residents and the collectors "\
                "via a digital platform, household recycling is "\
                "made more convenient and at the same time, "\
                "it reduces recycling waste contamination which "\
                "makes recycling overall more effective."\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",

        reply_markup=reply_markup
    )
    return INFOS


def helps(update, context):
    keyboard = [[InlineKeyboardButton("💬 F.A.Q", callback_data=str(FAQ))],
                [InlineKeyboardButton("📬 Contact Us", callback_data=str(CONTACT))],
                [InlineKeyboardButton("🏙 Change address / Unregister", callback_data=str(CHANGE_ADDRESS))],
                [InlineKeyboardButton("« Back", callback_data=str(END))]
                ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="How can I help you? 😊"\
             "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        reply_markup=reply_markup
    )
    return HELPS


def helps_faq(update, context):
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END_HELPS))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Our FAQ can be found on our [Facebook page](https://www.facebook.com/recyclables.sg/).\n\n"\
                " Alternatively, you can message @RecyclablesHelpBot on Telegram for any enquiries!"\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    return HELPS


def helps_contact(update, context):
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END_HELPS))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Feel free to reach us at the following channels!"\
                "\n\n*Email*: help@recyclables.sg"\
                "\n*Instagram* : [@recyclables.sg](https://www.instagram.com/recyclables.sg/)"\
                "\n*Facebook*: [recyclables.sg](https://www.facebook.com/recyclables.sg/)"\
                "\n*Telegram: *@RecyclablesHelpBot",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    return HELPS


def change_address(update, context):
    keyboard = [[InlineKeyboardButton("Proceed", callback_data=str(PROCEED)),
                 InlineKeyboardButton("« Back", callback_data=str(END_HELPS))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="🚨 Proceeding will reset your registration details "\
                "and you will have to register again to use our services."\
                "\n\nDo you wish to proceed?",
        reply_markup=reply_markup
    )
    return HELPS


def proceed(update, context):
    userids = str(update.effective_user.id)
    db.collection(u'users').document(userids).delete()
    user_data = context.user_data
    user_data.clear()
    shard_counter.decrement_user(db)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Reset completed, your details are removed. \n\nType /start to enter your new details!"
    )
    return STOPPING


def register(update, context):
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="*Okay, please tell me your postal code in six digits.*"\
                "\n\nWe are currently running a trial run and are only operating in:"\
                "\n📍 Choa Chu Kang"\
                "\n📍 Yew Tee"\
                "\n\n_For example: 520123_"\
                "\n\nType /cancel to cancel",
        parse_mode='Markdown',
    )
    return POSTAL

def postal(update, context):
    postal = update.message.text

    # One map SG api-endpoint
    URL = "https://developers.onemap.sg/commonapi/search"
    PARAMS = {'searchVal': postal,
              'returnGeom': 'Y',
              'getAddrDetails': 'Y'}

    invalid_text = "*Invalid postal code, please try again.*"\
                    "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding."

    text = "*Please select your address from the following:* \n\n"

    try:
        postals = int(postal)
        context.bot.send_chat_action(
            chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        if len(postal) == 6:
            r = requests.get(url=URL, params=PARAMS)
            add_data = r.json()
            if add_data['found'] > 0:
                context.user_data['Postal code'] = str(postal)
                keyboard_button = []
                x = 0
                text_address = []
                for i in add_data['results']:
                    block = add_data['results'][x]['BLK_NO']
                    street = add_data['results'][x]['ROAD_NAME']
                    building = add_data['results'][x]['BUILDING']
                    if '@' in building:
                        building = building.split('@')[0]
                    elif len(building) > 20:
                        building = building[:20]
                    full_add = block + ' ' + street + ', ' + building
                    lat = round(float(add_data['results'][x]['LATITUDE']), 3)
                    lng = round(float(add_data['results'][x]['LONGITUDE']), 3)
                    keyboard_button.append(InlineKeyboardButton(
                        "📍 Address #" + str(x+1), callback_data=(full_add + ','+str(lat)+','+str(lng))))
                    x += 1
                    text_address.append("Address #" + str(x) + "\n" + full_add)

                reply_markup = InlineKeyboardMarkup(
                    build_menu(keyboard_button, n_cols=1))
                update.message.reply_text(
                    text=text +
                    final_address_format(text_address) +
                    "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
                return ADDRESS

            else:
                update.message.reply_text(text=invalid_text,
                                        parse_mode='Markdown',
                                        disable_web_page_preview=True)
                return POSTAL

        else:
            update.message.reply_text(text=invalid_text,
                                      parse_mode='Markdown',
                                      disable_web_page_preview=True)
            return POSTAL

    except ValueError:
        update.message.reply_text(text=invalid_text,
                                  parse_mode='Markdown',
                                  disable_web_page_preview=True)
    return POSTAL


def address(update, context):
    res = update.callback_query.data
    data = res.split(",")
    update.callback_query.answer()
    context.user_data['Address'] = data[0]+", "+data[1]
    context.user_data['latitude'] = data[2]
    context.user_data['longitude'] = data[3]
    update.callback_query.edit_message_text(
        text="*Okay, please tell me your unit number:*"\
                "\n_Floor - unit number_"\
                "\nFor example: #01-01"\
                "\n\nType /cancel to exit the bot. Type /start if the buttons are not responding.",
        parse_mode='Markdown'
    )
    return UNIT


def unit(update, context):
    unit = update.message.text
    context.user_data['Unit'] = unit
    timestamp = str(int(time.time()))

    try:
        user_data = context.user_data
        userids = str(update.message.from_user.id)
        username = str(update.message.from_user.username)
        userfirstname = str(update.message.from_user.first_name)
        postal = context.user_data['Postal code']
        address = context.user_data['Address']
        unit = context.user_data['Unit']
        latitude = context.user_data['latitude']
        longitude = context.user_data['longitude']
        update.message.reply_text("Your address:\n{}"\
                                  "\nThank you for registering! To change your address,"\
                                  " navigate to Help in the menu.".format(address_format(user_data)))

        db.collection(u'users').document(userids).set(Users(userids, username, userfirstname, address, unit, postal, latitude, longitude, timestamp).users_to_dict())
        shard_counter.increment_user(db)
        user_data.clear()
        start(update, context)
        return END

    except KeyError:
        update.message.reply_text('error, try again later')
        return STOPPING


def end(update, context):
    user_data = context.user_data
    user_data.clear()
    update.callback_query.edit_message_text(
        text="Alright! Thank you and have a nice day!"
    )
    return END


def cancel(update, context):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text(
        text="Alright! Thank you and have a nice day!"
    )
    return END


def cancel_slots(update, context):
    update.message.reply_text(
        text="Sorry! We are fully booked this week!"
    )
    return END

def end_reg(update, context):
    user_data = context.user_data
    user_data.clear()
    update.callback_query.edit_message_text(
        text='No problem! Hope to see you soon!'
    )
    return STOPPING

def cancel_reg(update, context):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text(
        text="Alright! Thank you and have a nice day!"
    )
    return STOPPING

def end_nested(update, context):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text(
        text="Alright! Thank you and have a nice day!"
    )
    return STOPPING


def end_second(update, context):
    context.user_data[START_OVER] = True
    start(update, context)
    return END


def end_third(update, context):
    recycle(update, context)
    return END


def end_fourth(update, context):
    item_basket(update, context)
    return END


def end_fifth(update, context):
    agreement(update, context)
    return END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    from telegram.utils.request import Request
    # global throughput to 29 messages per 1 second
    q = mq.MessageQueue(all_burst_limit=29, all_time_limit_ms=1000)
    request = Request(con_pool_size=8)

    # For production deployment
    NAME = "recyclables"
    PORT = os.environ.get('PORT')

    mainBot = MQBot(TOKEN, request=request, mqueue=q)
    updater = Updater(bot=mainBot, use_context=True)
    dp = updater.dispatcher

    # Fifth level (time + confirm)
    confirm_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            basket_confirm, pattern='^{0}$'.format(('agree')))],

        states={
            CONFIRM_ORDER: [
                CallbackQueryHandler(success, pattern='^' + (CHECKOUT) + '$')
            ],
        },

        fallbacks=[
            CallbackQueryHandler(end_fifth, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', failure)
        ],

        map_to_parent={
            STOPPING: STOPPING,
            END: AGREEMENT,
        }
    )

    # Fourth level (date)
    select_date_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(date_selection, pattern='^' + str(SELECT_DATE) + '$')],

        states={
            DATES: [
                CallbackQueryHandler(agreement, pattern='^(?!' + str(END) + '$).*$'),
            ],
            AGREEMENT: [confirm_level,
                        CallbackQueryHandler(date_selection, pattern='^' + str(END_AGREEMENT) + '$'), ]
        },

        fallbacks=[
            CallbackQueryHandler(end_fourth, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: STOPPING,
            END: CONFIRM,
        }
    )

    # Third level (Papers)
    papers_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            papers, pattern='^' + str(ITEM_PAPERS) + '$')],

        states={
            WEIGHT: [
                CallbackQueryHandler(item_basket, pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(PAPER1),
                                                                                           str(
                                                                                               PAPER2),
                                                                                           str(
                                                                                               PAPER3),
                                                                                           str(PAPER4)))
            ],
            CONFIRM: [
                select_date_level,
                CallbackQueryHandler(
                    clear_item, pattern='^' + str(CLEAR_ITEM) + '$')
            ],
            CLEAR: [
                CallbackQueryHandler(clear_confirm, pattern='^{0}$|^{1}$'.format(str(CHOICE1),
                                                                                 str(CHOICE2))),
                CallbackQueryHandler(
                    item_basket, pattern='^' + str(END_CLEAR) + '$')
            ],
        },

        fallbacks=[
            CallbackQueryHandler(end_third, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: STOPPING,
            END: RECYCLABLES,
        }
    )

    # Third level (Clothes)
    clothes_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            clothes, pattern='^' + str(ITEM_CLOTHES) + '$')],

        states={
            WEIGHT: [
                CallbackQueryHandler(item_basket, pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(CLOTHES1),
                                                                                           str(
                                                                                               CLOTHES2),
                                                                                           str(
                                                                                               CLOTHES3),
                                                                                           str(CLOTHES4)))
            ],
            CONFIRM: [
                select_date_level,
                CallbackQueryHandler(
                    clear_item, pattern='^' + str(CLEAR_ITEM) + '$')
            ],
            CLEAR: [
                CallbackQueryHandler(clear_confirm, pattern='^{0}$|^{1}$'.format(str(CHOICE1),
                                                                                 str(CHOICE2))),
                CallbackQueryHandler(
                    item_basket, pattern='^' + str(END_CLEAR) + '$')
            ],
        },

        fallbacks=[
            CallbackQueryHandler(end_third, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: STOPPING,
            END: RECYCLABLES,
        }
    )

    # Third level (Electronics)
    electronics_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            electronics, pattern='^' + str(ITEM_ELECTRONICS) + '$')],

        states={
            END_ELECTRONICS: [
                CallbackQueryHandler(end_third, pattern='^' + str(END) + '$')
            ]
        },

        fallbacks=[
            CallbackQueryHandler(end_third, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: STOPPING,
            END: RECYCLABLES,
        }
    )
    # Second level (Item selection)
    orders_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            my_order, pattern='^' + str(MY_ORDER) + '$')],

        states={
            MY_ORDERS: [
                CallbackQueryHandler(check_past_orders, pattern='^' +
                                     str(CHECK_ORDERS) + '$'),
                CallbackQueryHandler(my_order, pattern='^' +
                                     str(END_MY_ORDERS) + '$'),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(end_second, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: END,
            END: MAIN_MENU
        }
    )
    # Second level (Item selection)
    helps_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            helps, pattern='^' + str(HELP) + '$')],

        states={
            HELPS: [
                CallbackQueryHandler(helps_faq, pattern='^' + str(FAQ) + '$'),
                CallbackQueryHandler(
                    helps_contact, pattern='^' + str(CONTACT) + '$'),
                CallbackQueryHandler(
                    change_address, pattern='^' + str(CHANGE_ADDRESS) + '$'),
                CallbackQueryHandler(helps, pattern='^' +
                                     str(END_HELPS) + '$'),
                CallbackQueryHandler(proceed, pattern='^' + str(PROCEED) + '$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(end_second, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: END,
            END: MAIN_MENU
        }
    )
    # Second level (Item selection)
    info_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            info, pattern='^' + str(INFO) + '$')],

        states={
            INFOS: [
                CallbackQueryHandler(
                    info_about, pattern='^' + str(ABOUT) + '$'),
                CallbackQueryHandler(
                    info_privacy, pattern='^' + str(PRIVACY) + '$'),
                CallbackQueryHandler(info, pattern='^' + str(END_INFO) + '$')
            ]
        },

        fallbacks=[
            CallbackQueryHandler(end_second, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: END,
            END: MAIN_MENU
            #ENDS: REGISTER
        }
    )
    # Second level (Item selection)
    recycle_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(recycle, pattern='^' + str(RECYCLE) + '$')],

        states={
            RECYCLABLES: [papers_level, electronics_level, clothes_level]
        },

        fallbacks=[
            CallbackQueryHandler(end_second, pattern='^' + str(END) + '$'),
            CommandHandler('cancel', end_nested)
        ],

        map_to_parent={
            STOPPING: END,
            END: MAIN_MENU,
        }
    )
    # Address registration
    register_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(
            register, pattern='^' + str(REGISTERYES) + '$')],

        states={
            POSTAL: [MessageHandler(Filters.regex(r"^[^\/].+$"), postal)],

            ADDRESS: [CallbackQueryHandler(address)],

            UNIT: [MessageHandler(Filters.regex(r"^[^\/].+$"), unit)],
        },

        fallbacks=[
            CommandHandler('cancel', cancel_reg)],

        map_to_parent={
            STOPPING: END,
            END: MAIN_MENU
        }
    )

    # First level (Main menu)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            REGISTER: [register_level,
                       CallbackQueryHandler(end_reg, pattern='^' + str(REGISTERNO) + '$')],

            MAIN_MENU: [
                recycle_level,
                info_level,
                helps_level,
                orders_level,
                CallbackQueryHandler(end, pattern='^' + str(END) + '$')],

        },

        fallbacks=[CommandHandler('cancel', cancel)],
    )
    conv_handler.states[RECYCLABLES, INFOS, HELPS, MY_ORDERS] = conv_handler.states[MAIN_MENU]
    conv_handler.states[STOPPING] = conv_handler.entry_points
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    # For production deployment
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=int(PORT),
    #                       url_path=TOKEN)
    # updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))

    # For local hosting ONLY
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
