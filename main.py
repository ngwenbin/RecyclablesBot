import gspread, pprint
from oauth2client.service_account import ServiceAccountCredentials
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, 
                      ReplyKeyboardRemove, KeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

## gspread stuffs ##
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("remebot.json", scope)
gc = gspread.authorize(creds)
sheet = gc.open("remeBot Database").worksheet("Address")
sheet2 = gc.open("remeBot Database").worksheet("Orders")

# States
FIRST, SECOND, THIRD, CONFIRM, REGISTER, POSTAL, ADDRESS, UNIT = range(8)
# Primary callbacks
RECYCLE, INFO, HELP, DONE, REGISTERYES, REGISTERNO = range(6)
# Secondary callbacks
PAPERS, ELECTRONICS, CLOTHES, BACK1, BACK2, PAPER1, PAPER2, PAPER3 = range(8)

END = ConversationHandler.END

#Cache formatting
def facts_to_str(user_data):
    facts = list()
    for key, value in user_data.items():
        facts.append('{}: {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])

# Main Defs
def start(update, context):
    userids = str(update.message.from_user.id)
    try:
        _cell = sheet.find(userids)
        keyboard = [[InlineKeyboardButton("Start recycling! ♻️", callback_data=str(RECYCLE))],
                    [InlineKeyboardButton("Info 📋", callback_data=str(INFO))],
                    [InlineKeyboardButton("Help 🙋🏻‍♀️", callback_data=str(HELP))],
                    [InlineKeyboardButton("Exit", callback_data=str(DONE))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            "*Hello " + str(update.message.from_user.first_name)+"! 👋🏻*"\
            "\n\n*remeBot* can help you to schedule recyclables collection bookings conveniently. "\
            "With remeBot, you can play a part in saving the earth while helping to improve the producitivty of  "\
            "local rag n' bone collectors. In addition to that, you will be rewarded with incentives for your recyclables! ☺️"\
            "\n\nNow, what can I do for you?",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return FIRST
        
    except gspread.exceptions.CellNotFound: #gspread exceptions
        
        keyboard = [[InlineKeyboardButton("Yes", callback_data=str(REGISTERYES))],
                    [InlineKeyboardButton("No", callback_data=str(REGISTERNO))]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            text="Oops! Looks like you are not registered with us."\
                 "\nIn order to use our service,"\
                 " I will require your residential address for registration purposes."\
                 "\n\nWould you like to proceed?"\
                 "\n\nType /cancel to cancel.",
            reply_markup=reply_markup
        )

        return REGISTER

def start_callback(update, context):
    query = update.callback_query
    bot = context.bot
    #user_firstname = str(update.message.from_user.first_name)
    keyboard = [[InlineKeyboardButton("Start recycling! ♻️", callback_data=str(RECYCLE))],
                [InlineKeyboardButton("Info 📋", callback_data=str(INFO))],
                [InlineKeyboardButton("Help 🙋🏻‍♀️", callback_data=str(HELP))],
                [InlineKeyboardButton("Exit", callback_data=str(DONE))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="*Hello! 👋🏻*"\
             "\n\n*remeBot* can allow you to schedule recyclables collection bookings easily. "\
             "With remeBot, you can play a part in saving the earth while helping to improve the producitivty of  "\
             "local rag n' bone collectors. In addition to that, you are rewarded with incentives for your recyclables! "\
             "\n\nIt's definitely a win-win-win! ☺️"\
             "\n\nNow, what can I do for you?",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

    return FIRST

def recycle(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [[InlineKeyboardButton("Papers", callback_data=str(PAPERS))],
                [InlineKeyboardButton("Electronics", callback_data=str(ELECTRONICS))],
                [InlineKeyboardButton("Clothes", callback_data=str(CLOTHES))],
                [InlineKeyboardButton("Back", callback_data=str(BACK1))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Please select the type of recyclables:",
        reply_markup=reply_markup
    )

    return SECOND

def papers(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [[InlineKeyboardButton("Less than 20KG", callback_data=str(PAPER1))],
                [InlineKeyboardButton("20KG to 30KG", callback_data=str(PAPER2))],
                [InlineKeyboardButton("30KG to 40KG", callback_data=str(PAPER3))],
                [InlineKeyboardButton("Back", callback_data=str(BACK2))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Please select an estimated weight of your papers:",
        reply_markup=reply_markup
    )

    return THIRD

def p1(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="You will receive [$1.00 - $1.50] for your recyclables"
    )

    keyboard = [["Yes","No"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    bot.send_message(
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text="Kindly confirm your order:", 
                     reply_markup=reply_markup
    )

    return CONFIRM

def choiceyes(update, context):
    text =  "*Your order has been confirmed*"

    text2 = "\n\nOrder No #01"\
            "\n--------------------"\
            "\n*Item*: Papers"\
            "\n*Weight*: Less than 20KG"\
            "\n*Price* ≈ $1.00 - $1.50"\

    text3 = "\n\nSee FAQ or /help should you need any help"
    update.message.reply_text(text=text+text2+text3, 
                              parse_mode="Markdown",
                              reply_markup=ReplyKeyboardRemove(True)
                              )
    """#this is for order message notification
    bot = context.bot
    chat_id="-351944461"
    bot.send_message(chat_id=chat_id, 
                     parse_mode="Markdown", 
                     text=text2)
    """

    return end

def choiceno(update, context):
    update.message.reply_text("Sure thing, no worries!", reply_markup=ReplyKeyboardRemove(True))

    return end

def electronics(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="WIP!"
    )

    return END

def clothes(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="WIP!"
    )

    return END

def info(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Info placeholder!"
    )

    return END

def help(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="WIP!"
    )

    return END

def end(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Thank you and have a nice day! Hope to see you soon!"
    )
    return END

def end_reg(update, context):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text(
        text='No problem! Hope to see you soon!'
    )
    return END

def register(update, context):
    #sheet.append_row([userids],value_input_option="RAW") #Append full row
    bot = context.bot
    query = update.callback_query
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text="Okay, please tell me your postal code in six digits."\
             "\nFor example: 520123"\
             "\n\nType /cancel to cancel"
    )
    
    return POSTAL

def postal(update, context):
    postal = update.message.text
    invalid_text="Invalid postal code, please try again."
    text="Please tell me your address: \n(Block number/ Street number/ Building number)"\
         "\nFor example: BLK 123 Orchard street 1"\
         "\n\nType /cancel to cancel"
    try:
        postal = int(postal)
        if 0<=postal<=999999:
            context.user_data['Postal code'] = postal
            update.message.reply_text(text=text)

            return ADDRESS

        else:
            update.message.reply_text(text=invalid_text + text)

            return POSTAL

    except ValueError:
        update.message.reply_text(text=invalid_text + text)

        return POSTAL


def address(update, context):
    address = update.message.text
    context.user_data['Address'] = address
    update.message.reply_text(
        text="Okay, please tell me your unit number: \n(#Floor - unit number)"\
             "\nFor example: #01-01"
             "\n\nType /cancel to cancel"
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
        update.message.reply_text("Your address:\n{}"\
                                  "\n\nThank you for registering! To change your address,"\
                                  " navigate to Help in the menu.".format(facts_to_str(user_data)))
        
        sheet.append_row([userids,username,userfirstname,postal,address,unit],value_input_option="RAW")
        user_data.clear()

        return start(update, context)

    except KeyError:
        update.message.reply_text('error')

        return end_reg(update, context)

def main():
    updater = Updater('945909213:AAHynjzuKmbJA2f_IoRmUJsSQG2QGr8077U', use_context=True)
    dp = updater.dispatcher

    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow "ABC"
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            REGISTER: [CallbackQueryHandler(register, pattern='^' + str(REGISTERYES) + '$'),
                       CallbackQueryHandler(end, pattern='^' + str(REGISTERNO) + '$')],

            POSTAL: [MessageHandler(Filters.text, postal)],

            ADDRESS: [MessageHandler(Filters.text, address)],

            UNIT: [MessageHandler(Filters.text, unit)],
            
            FIRST:  [CallbackQueryHandler(recycle, pattern='^' + str(RECYCLE) + '$'),
                     CallbackQueryHandler(info, pattern='^' + str(INFO) + '$'),
                     CallbackQueryHandler(help, pattern='^' + str(HELP) + '$'),
                     CallbackQueryHandler(end, pattern='^' + str(DONE) + '$')],

            SECOND: [CallbackQueryHandler(papers, pattern='^' + str(PAPERS) + '$'),
                     CallbackQueryHandler(electronics, pattern='^' + str(ELECTRONICS) + '$'),
                     CallbackQueryHandler(clothes, pattern='^' + str(CLOTHES) + '$'),
                     CallbackQueryHandler(start_callback, pattern='^' + str(BACK1) + '$')],

            THIRD:  [CallbackQueryHandler(p1, pattern='^' + str(PAPER1) + '$'),
                     CallbackQueryHandler(p1, pattern='^' + str(PAPER2) + '$'),
                     CallbackQueryHandler(p1, pattern='^' + str(PAPER3) + '$'),
                     CallbackQueryHandler(recycle, pattern='^' + str(BACK2) + '$')],

            CONFIRM:  [MessageHandler(Filters.regex('^Yes$'), choiceyes),
                       MessageHandler(Filters.regex('^No$'), choiceno)
                      ],
                     
        },

        fallbacks=[CommandHandler('cancel', end_reg)]
    )
    
    dp.add_handler(conv_handler)
    updater.start_polling(read_latency=0)
    updater.idle()

if __name__ == '__main__':
    main()
