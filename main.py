import gspread, re, logging, telegram.bot, pricelist, os, requests
from oauth2client.service_account import ServiceAccountCredentials
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup,
                    ReplyKeyboardRemove, KeyboardButton, ChatAction)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                        ConversationHandler, CallbackQueryHandler)
from telegram.ext import messagequeue as mq
from datetime import date
from datetime import timedelta
from datetime import datetime
from dotenv import load_dotenv

# load env file
load_dotenv()

## gspread stuffs ##
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(creds)
sheet = gc.open("Recyclables (Database)").worksheet("Address")
sheet2 = gc.open("Recyclables (Database)").worksheet("Orders")
this_friday = sheet2.acell('G1').value
next_friday = sheet2.acell('G2').value
this_saturday = sheet2.acell('I1').value
next_saturday = sheet2.acell('I2').value

class MQBot(telegram.bot.Bot):

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
REGISTER, REGISTERYES, REGISTERNO, MAIN_MENU, RECYCLE, INFO, HELP,  = map(chr, range(7))
# Sub second level state
POSTAL, ADDRESS, UNIT = map(chr, range(7,10))
# Second level states
HELPS, FAQ, CONTACT, CHANGE_ADDRESS, END_HELPS, PROCEED = map(chr, range(10, 16))
# Second level states
INFOS, ABOUT, PRIVACY, END_INFO = map(chr, range(16, 20))
# Second level states
RECYCLABLES, ITEM_PAPERS, ITEM_ELECTRONICS, ITEM_CLOTHES = map(chr, range(20, 24))
# Third level states
WEIGHT, CONFIRM, SELECT_DATE, CLEAR_ITEM, CLEAR, END_CLEAR, END_ELECTRONICS = map(chr, range(24, 31))
# Fourth level states
DATES, AGREEMENT, END_AGREEMENT = map(chr, range(31, 34))
# Fifth level states
CONFIRM_ORDER, CHECKOUT = map(chr, range(34, 36))
# Constants
(START_OVER, PAPERS, CLOTHES, DAYS, TIMES, BASKET,
 ITEM_TYPE, ROW, FULL_ADDRESS) = map(chr, range(36,45))
# Meta states
STOPPING = map(chr, range(45,46))
# Paper meta states
PAPER1, PAPER2, PAPER3, PAPER4 = map(chr, range(4))
# Clothes meta states
CLOTHES1, CLOTHES2, CLOTHES3, CLOTHES4 = map(chr, range(4, 8))
# Choices meta states
CHOICE1, CHOICE2 = map(chr, range(8,10))

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

def collection_format(user_data):
    collect = list()
    for key, value in user_data.items():
        if key == DAYS or key == TIMES:
            collect.append('{}'.format(value))
    return "\n".join(collect)

def final_address_format(text):
    data = list()
    for i in text:
        data.append('{}'.format(i))
    return "\n\n".join(data)

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
                    "\n\nWe are currently only operating in:"\
                    "\n📍 Choa Chu Kang"\
                    "\n📍 Yew Tee"\
                    "\n\n*Would you like to proceed?*"\
                    "\n\nType /cancel to exit the bot."

    basket_text = "\n\n_You still have item(s) in your basket.\nDon't forget!_"

    main_keyboard = [[InlineKeyboardButton("♻️  Start recycling!", callback_data=str(RECYCLE))],
                    [InlineKeyboardButton("📋  Info", callback_data=str(INFO))],
                    [InlineKeyboardButton("🙋🏻‍♀️  Help", callback_data=str(HELP))],
                    [InlineKeyboardButton("« Exit", callback_data=str(END))]]

    main_markup = InlineKeyboardMarkup(main_keyboard)

    reg_keyboard = [[InlineKeyboardButton("Yes", callback_data=str(REGISTERYES))],
                    [InlineKeyboardButton("No", callback_data=str(REGISTERNO))]]

    reg_markup = InlineKeyboardMarkup(reg_keyboard)

    if context.user_data.get(START_OVER):
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
        update.message.reply_text(
            "*Hello " + str(update.message.from_user.first_name) +"!* 👋🏻 \nWelcome to Recyclables!",
            parse_mode="Markdown"
        )
        try:
            gc.login()
            cells = sheet.find(userids)
            context.user_data[ROW] = cells.row
            update.message.reply_text(
                text=main_text,
                parse_mode="Markdown",
                reply_markup=main_markup
            )
            return MAIN_MENU

        except gspread.exceptions.CellNotFound: #gspread exceptions
            update.message.reply_text(
                text= register_text,
                reply_markup=reg_markup,
                parse_mode ="Markdown"
            )
            return REGISTER

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
                "\n\nType /cancel to exit the bot.",
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
                "_$0.06 per KG_"\
                "\nNeed help in estimating the weight?"\
                "\nClick [here](https://i.imgur.com/6zd9K5P.png)!"
                "\n\nType /cancel to exit the bot."),
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    return WEIGHT

def clothes(update, context):
    update.callback_query.answer(
        text="Do ensure your clothes are clean as they are meant to be reused not recycled.",
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
                "\n\nCurrent estimated prices:\n"\
                "_$0.20 per KG_"\
                "\n\nType /cancel to exit the bot."),
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
    name= str(update.effective_user.first_name)
    row = context.user_data[ROW]
    values = sheet.range("D{0}:F{1}".format(row, row))
    address = ""
    for cell in values:
        address += ("{}\n".format(cell.value))
    update.callback_query.answer(
        text="Electronic recycling will be done via google forms."\
             "\n\nDo note that electronics recycling requests are processed manually.",
        show_alert=True)
    keyboard = InlineKeyboardButton(" « Back", callback_data=str(END))
    reply_markup = InlineKeyboardMarkup.from_button(keyboard)

    update.callback_query.edit_message_text(
        text=("Please fill in the form in [this link](" + get_link(name, address) + ") to receive a quotation."),
            # "https://forms.google.com/e_waste"),
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    return END_ELECTRONICS

def _item_text(item):
    x = 0
    y = 0
    # Papers
    if item == PAPER1:
        x=1
    elif item == PAPER2:
        x=2
    elif item == PAPER3:
        x=3
    elif item == PAPER4:
        x=4

    # Clothes
    elif item == CLOTHES1:
        y=1
    elif item == CLOTHES2:
        y=2
    elif item == CLOTHES3:
        y=3
    elif item == CLOTHES4:
        y=4

    if x > 0:
        text_item = ('Papers ({0}KG to {1}KG)'\
                     '\n$0.06 per KG'.format((x)*10,
                                                    (x+1)*10))
    elif y > 0:
        text_item = ('Clothes ({0}KG to {1}KG)'\
                     '\n$0.20 per KG'.format((y)*10,
                                                    (y+1)*10))
    return text_item

def item_basket(update, context):
    user_data = context.user_data
    context.user_data[BASKET] = True

    if context.user_data.get(START_OVER):
        #For item name updates
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
            update.callback_query.answer(text="Clothes added!", show_alert=True)

    keyboard = [[InlineKeyboardButton("🗓 Select date", callback_data=str(SELECT_DATE))],
                [InlineKeyboardButton("➕  Add item(s)", callback_data=str(END))],
                [InlineKeyboardButton("➖  Clear item(s)", callback_data=str(CLEAR_ITEM))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
                    text=("*Your current recyclables:*\n{}"\
                        "\n\nType /cancel to exit the bot.".format(item_format(user_data))),
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

def date_filter(day):
    today = date.today()
    current_limits = 10

    if day == 6:
        dates = today + timedelta(6 - (today.weekday()) % 7)
        if today >= dates: # Check if today is the week's day or past the week's day
            dates = today + timedelta(days=day-today.weekday(), weeks=1)

    else:
        dates = today + timedelta(days=day-today.weekday() % 7)
        if today >= dates or (int(this_friday) >= current_limits and day == 4) or (int(this_saturday) >= current_limits and day == 5):
            dates = today + timedelta(days=day-today.weekday(), weeks=1)


    return dates.strftime("%A (%d/%m/%y)")

    # Mon to Sun (0 to 6)

def date_selection(update, context):
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    if creds.access_token_expired:
            gc.login()
    context.user_data[START_OVER] = True
    current_limits = 10
    sheet2 = gc.open("Recyclables (Database)").worksheet("Orders")
    if context.user_data.get(BASKET):
        keyboard = [#[InlineKeyboardButton("Monday", callback_data='Monday'),
                    #InlineKeyboardButton("Tuesday", callback_data='Tuesday')],
                    #[InlineKeyboardButton("Wednesday", callback_data='Wednesday'),
                    #InlineKeyboardButton("Thursday", callback_data='Thursday')],
                    [InlineKeyboardButton(date_filter(4), callback_data='4'),
                    InlineKeyboardButton(date_filter(5), callback_data='5')],
                    [#InlineKeyboardButton("Sunday", callback_data='Sunday'),
                    InlineKeyboardButton("« Back to item basket", callback_data=str(END))]
        ]
        text = "*Please select your preferred date:*"\
                "\n\nType /cancel to exit the bot."

        if int(next_friday) >= current_limits:
            keyboard = [[InlineKeyboardButton(date_filter(5), callback_data='5'),
                        InlineKeyboardButton("« Back to item basket", callback_data=str(END))]
            ]

        if int(next_saturday) >= current_limits:
            keyboard = [[InlineKeyboardButton(date_filter(4), callback_data='4'),
                        InlineKeyboardButton("« Back to item basket", callback_data=str(END))]
            ]

        if int(next_friday) >= current_limits and int(next_saturday) >= current_limits:
            text = "*Sorry, our collection slots are full, please try again next week!*"\
                    "\n\nType /cancel to exit the bot."
            keyboard = [[InlineKeyboardButton("« Back to item basket", callback_data=str(END))]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.callback_query.answer()
        update.callback_query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        return DATES

    else:
        update.callback_query.answer(
            text="You cannot proceed to select date"\
                    " with nothing in your basket!"\
                    "\n\nPlease add items into your basket.",
            show_alert=True
        )
        return END

def agreement(update, context):
    if context.user_data.get(START_OVER):
        days = update.callback_query.data
        context.user_data[DAYS] = date_filter(int(days))
    else:
        context.user_data[START_OVER] = True
    keyboard = [[InlineKeyboardButton("Yes, I agree", callback_data=('agree')),
                #InlineKeyboardButton("PM", callback_data=('2pm to 5pm'))],
                InlineKeyboardButton("« Back to select date", callback_data=str(END_AGREEMENT))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="*Please do ensure your recyclables are reasonably accurate to the weight indicated*."\
                "\nCollection times will be between 11am to 2pm."
                "\n\nType /cancel to exit the bot.",
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
    row = user_data[ROW]
    if creds.access_token_expired:
            gc.login()
    values = sheet.range("D{0}:F{1}".format(row, row))
    text_address =''

    for cell in values:
        text_address += ("{}\n".format(cell.value))

    text = ("*Your current order is as follows:*\n"\
            "Item basket:\n_{0}_"\
            "\n\nCollection address:\n{1}"\
            "\nCollection details:\n{2}"\
            "\n11am to 2pm".format(item_format(user_data),
                                  text_address,
                                  days))
    end_text = "\n\nType /cancel to exit the bot."
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
    user_data[FULL_ADDRESS] = text_address
    return CONFIRM_ORDER

def success(update, context):
    if creds.access_token_expired:
            gc.login()
    user_data = context.user_data
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
    order_number = sheet2.acell('C3').value
    userids = str(update.effective_user.id)
    items = item_format(user_data)
    text_address = user_data[FULL_ADDRESS]
    #times = user_data[TIMES]
    days = user_data[DAYS]

    header_text = ("*Your order has been confirmed! 👍🏻\n\n*")
    order_text = ("*Order No #{}*"\
                    "\n-------------------------".format(order_number))
    item_text = ("\n*Recyclables to be collected:*\n{}".format(items))
    collection_add = ("\n\n*Collection address:*\n{}".format(text_address))
    collection_detail = ("\n*Collection details:*\n{0}".format(days))
    end_text = "\n\n_See FAQ should you need any help_"
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=header_text + order_text + item_text + collection_add + collection_detail + end_text,
        parse_mode="Markdown"
    )

    #this is for order message notification
    bot = context.bot
    groupchat="-1001427022537"
    bot.send_message(chat_id=groupchat,
                     parse_mode="Markdown",
                     text=order_text+item_text+collection_add+collection_detail)

    sheet2.append_row([order_number, userids, items, days, text_address],value_input_option="RAW")
    user_data.clear()
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
                [InlineKeyboardButton("🔐 Privacy policy", callback_data=str(PRIVACY))],
                [InlineKeyboardButton("« Back", callback_data=str(END))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="What info would you like to see?"\
            "\n\nType /cancel to exit the bot.",
        reply_markup=reply_markup
    )
    return INFOS

def info_privacy(update, context):
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END_INFO))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="We treat your data very seriously. Do visit our [Facebook](https://www.facebook.com/recyclables.sg/) page for more information.",
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
        text="Hello 👋🏻! We are a group of NUS students from NUS Social Impact Catalyst.\n\n"
            "Our goal is to improve Singapore’s domestic recycling efforts by "
            "partnering with the local karung guni community. "
            "By bridging the gap between residents and the collectors "
            "via a digital platform, household recycling is "
            "made more convenient and at the same time, "
            "it reduces recycling waste contamination which "
            "makes recycling overall more effective.",

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
             "\n\nType /cancel to exit the bot.",
        reply_markup=reply_markup
    )
    return HELPS

def helps_faq(update, context):
    keyboard = [[InlineKeyboardButton("« Back", callback_data=str(END_HELPS))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Our FAQ can be found on our [Facebook page](https://www.facebook.com/recyclables.sg/).",
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
             "\n*Facebook*: [recyclables.sg](https://www.facebook.com/recyclables.sg/)",
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
    cells = sheet.find(userids)
    sheet.delete_row(cells.row)
    user_data = context.user_data
    user_data.clear()
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Reset completed, your details are removed. \n\nType /start to enter your new details!"
    )
    return STOPPING

def register(update, context):
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="*Okay, please tell me your postal code in six digits.*"\
                "\n\nWe are currently only operating in:"\
                "\n📍 Choa Chu Kang"\
                "\n📍 Yew Tee"\
                "\n\n_For example: 520123_"\
                "\n\nType /cancel to cancel",
        parse_mode='Markdown',
    )
    return POSTAL
def build_menu(buttons,n_cols,header_buttons=None,footer_buttons=None):
  menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
  if header_buttons:
    menu.insert(0, header_buttons)
  if footer_buttons:
    menu.append(footer_buttons)
  return menu

def postal(update, context):
    postal = update.message.text

    # One map SG api-endpoint
    URL = "https://developers.onemap.sg/commonapi/search"
    PARAMS = {'searchVal': postal,
              'returnGeom': 'Y',
              'getAddrDetails' : 'Y'}

    invalid_text="*Invalid postal code, please try again.*"\
                    "\n\nType /cancel to cancel"
    unavailable_text = "Sorry! Our services are currently not available in your region!"\
                        "\n\nWe are currently only operating in:"\
                        "\n📍 Choa Chu Kang"\
                        "\n📍 Yew Tee"\
                        "\n\nFollow us on [Instagram](https://www.instagram.com/recyclables.sg/) or [Facebook](https://www.facebook.com/recyclables.sg/) for updates!"

    text="*Please select your address from the following:* \n\n"

    try:
        postal = int(postal)
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        r = requests.get(url = URL, params=PARAMS)
        add_data = r.json()
        if add_data['found'] > 0:
            try:
                sheet3 = gc.open("Recyclables (Database)").worksheet("Postals")
                sheet3.find(str(postal))
                context.user_data['Postal code'] = postal
                keyboard_button = []
                x = 0
                text_address = []
                for i in add_data['results']:
                    block = add_data['results'][x]['BLK_NO']
                    street = add_data['results'][x]['ROAD_NAME']
                    building = add_data['results'][x]['BUILDING']
                    full_add = block+ ' ' + street + ', '+ building
                    lat = round(float(add_data['results'][x]['LATITUDE']),3)
                    lng = round(float(add_data['results'][x]['LONGITUDE']),3)

                    keyboard_button.append(InlineKeyboardButton("📍 Address #" + str(x+1), callback_data=(full_add +','+str(lat)+','+str(lng))))
                    x+=1
                    text_address.append("Address #"+ str(x) + "\n"+ full_add)

                reply_markup = InlineKeyboardMarkup(build_menu(keyboard_button,n_cols=1))
                update.message.reply_text(
                    text=text + final_address_format(text_address) + "\n\nType /cancel to cancel",
                    parse_mode='Markdown',
                    reply_markup=reply_markup,
                    disable_web_page_preview=True,
                )
                return ADDRESS

            except gspread.exceptions.CellNotFound: #gspread exceptions
                update.message.reply_text(text=unavailable_text,
                    parse_mode='Markdown',
                    disable_web_page_preview=True)
                return STOPPING

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
                "\nFor example: #01-01"
                "\n\nType /cancel to cancel",
        parse_mode='Markdown'
    )
    return UNIT

def unit(update, context):
    unit = update.message.text
    context.user_data['Unit'] = unit

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

        sheet.append_row([userids, username, userfirstname, address, unit,postal, latitude, longitude],value_input_option="RAW")
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
    update.message.reply_text(
        text='No problem! Hope to see you soon!'
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
    TOKEN = os.getenv("TELEGRAM_TOKEN")

    # For production deployment
    NAME = "recyclables"
    PORT = os.environ.get('PORT')

    mainBot = MQBot(TOKEN, request=request, mqueue=q)
    updater = Updater(bot=mainBot, use_context=True)
    dp = updater.dispatcher

    # Fifth level (time + confirm)
    confirm_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(basket_confirm, pattern='^{0}$'.format(('agree')))],

        states ={
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

        states ={
            DATES: [
                CallbackQueryHandler(agreement, pattern='^{0}$|^{1}$|^{2}$|^{3}$|^{4}$|^{5}$|^{6}$'.format(("0"),
                                                                                                                ('1'),
                                                                                                                ('2'),
                                                                                                                ('3'),
                                                                                                                ('4'),
                                                                                                                ('5'),
                                                                                                                ('6'))),
            ],
            AGREEMENT: [confirm_level,
                    CallbackQueryHandler(date_selection, pattern='^' + str(END_AGREEMENT) + '$'),]
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
        entry_points=[CallbackQueryHandler(papers, pattern='^' + str(ITEM_PAPERS) + '$')],

        states={
            WEIGHT: [
                CallbackQueryHandler(item_basket, pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(PAPER1),
                                                                                                str(PAPER2),
                                                                                                str(PAPER3),
                                                                                                str(PAPER4)))
            ],
            CONFIRM: [
                select_date_level,
                CallbackQueryHandler(clear_item, pattern='^' + str(CLEAR_ITEM) + '$')
            ],
            CLEAR: [
                CallbackQueryHandler(clear_confirm, pattern='^{0}$|^{1}$'.format(str(CHOICE1),
                                                                                str(CHOICE2))),
                CallbackQueryHandler(item_basket, pattern='^' + str(END_CLEAR) + '$')
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
        entry_points=[CallbackQueryHandler(clothes, pattern='^' + str(ITEM_CLOTHES) + '$')],

        states={
            WEIGHT: [
                CallbackQueryHandler(item_basket, pattern='^{0}$|^{1}$|^{2}$|^{3}$'.format(str(CLOTHES1),
                                                                                                str(CLOTHES2),
                                                                                                str(CLOTHES3),
                                                                                                str(CLOTHES4)))
            ],
            CONFIRM: [
                select_date_level,
                CallbackQueryHandler(clear_item, pattern='^' + str(CLEAR_ITEM) + '$')
            ],
            CLEAR: [
                CallbackQueryHandler(clear_confirm, pattern='^{0}$|^{1}$'.format(str(CHOICE1),
                                                                                str(CHOICE2))),
                CallbackQueryHandler(item_basket, pattern='^' + str(END_CLEAR) + '$')
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
        entry_points=[CallbackQueryHandler(electronics, pattern='^' + str(ITEM_ELECTRONICS) + '$')],

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
    helps_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(helps, pattern='^' + str(HELP) + '$')],

        states={
            HELPS: [
                CallbackQueryHandler(helps_faq, pattern='^' + str(FAQ) + '$'),
                CallbackQueryHandler(helps_contact, pattern='^' + str(CONTACT) + '$'),
                CallbackQueryHandler(change_address, pattern='^' + str(CHANGE_ADDRESS) + '$'),
                CallbackQueryHandler(helps, pattern='^' + str(END_HELPS) + '$'),
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
        entry_points=[CallbackQueryHandler(info, pattern='^' + str(INFO) + '$')],

        states={
            INFOS: [
                CallbackQueryHandler(info_about, pattern='^' + str(ABOUT) + '$'),
                CallbackQueryHandler(info_privacy, pattern='^' + str(PRIVACY) + '$'),
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
        entry_points=[CallbackQueryHandler(register, pattern='^' + str(REGISTERYES) + '$')],

        states={
            POSTAL: [MessageHandler(Filters.text, postal)],

            ADDRESS: [CallbackQueryHandler(address)],

            UNIT: [MessageHandler(Filters.text, unit)],
        },

        fallbacks=[
            CommandHandler('cancel', end_reg)],

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
                CallbackQueryHandler(end, pattern='^' + str(END) + '$')],

        },

        fallbacks=[CommandHandler('cancel', cancel)],
    )
    conv_handler.states[RECYCLABLES, INFOS, HELPS] = conv_handler.states[MAIN_MENU]
    conv_handler.states[STOPPING] = conv_handler.entry_points
    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    # For production deployment
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))

    # For local hosting ONLY
    # updater.start_polling()
    # updater.idle()

if __name__ == '__main__':
    main()
