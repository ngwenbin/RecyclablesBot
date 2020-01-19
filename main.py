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
sheet3 = gc.open("remeBot Database").worksheet("Prices")

# First level states
MAIN_MENU, REGISTER, REGISTERNO, REGISTERYES, INFO, HELP, POSTAL, ADDRESS, UNIT = map(chr, range(9))
# Second level states
RECYCLABLES, RECYCLE = map(chr, range(9, 11))
# Third level states
PAPER_WEIGHT, CONFIRM, ITEM_PAPERS, ITEM_ELECTRONICS, ITEM_CLOTHES = map(chr, range(11, 16))
# Third level states
PAPER1, PAPER2, PAPER3, PAPER4 = map(chr, range(16,20))
# Metal states
STOPPING = map(chr, range(20,21))

# Others
START_OVER = map(chr,range(21,22))

END = ConversationHandler.END

#Cache formatting
def cache_format(user_data):
    facts = list()
    for key, value in user_data.items():
        facts.append('{}: {}'.format(key, value))

    return "\n".join(facts).join(['\n', '\n'])

# Main Defs
def start(update, context):
    main_text = "*remeBot* can help you to schedule recyclables collection bookings conveniently."\
                "With remeBot, you can play your part in helping the environment while improving the producitivty of  "\
                "local rag n' bone collectors. In addition to that, you can receive incentives for your recyclables! ☺️"\
                "\n\nNow, what can I do for you?"
                
    register_text = "Oops! Looks like you are not registered with us."\
                    "\nIn order to use our service,"\
                    " I will require your residential address for registration purposes."\
                    "\n\nWould you like to proceed?"\
                    "\n\nType /cancel to cancel."

    main_keyboard = [[InlineKeyboardButton("Start recycling! ♻️", callback_data=str(RECYCLE))],
                    [InlineKeyboardButton("Info 📋", callback_data=str(INFO))],
                    [InlineKeyboardButton("Help 🙋🏻‍♀️", callback_data=str(HELP))],
                    [InlineKeyboardButton("Exit", callback_data=str(END))]]

    main_markup = InlineKeyboardMarkup(main_keyboard)

    reg_keyboard = [[InlineKeyboardButton("Yes", callback_data=str(REGISTERYES))],
                    [InlineKeyboardButton("No", callback_data=str(REGISTERNO))]]

    reg_markup = InlineKeyboardMarkup(reg_keyboard)

    if context.user_data.get(START_OVER):
        update.callback_query.edit_message_text(
             text=main_text,
             parse_mode="Markdown",
             reply_markup=main_markup
        )
        context.user_data[START_OVER] = False
        return MAIN_MENU
    else:
        userids = str(update.message.from_user.id)
        update.message.reply_text(
            "*Hello " + str(update.message.from_user.first_name)+"!* 👋🏻 \nWelcome to remeBot!",
            parse_mode="Markdown")
        try:
            _cell = sheet.find(userids)
            update.message.reply_text(
                text=main_text,
                parse_mode="Markdown",
                reply_markup=main_markup
            )

            return MAIN_MENU
            
        except gspread.exceptions.CellNotFound: #gspread exceptions
            update.message.reply_text(
                text= register_text,
                reply_markup=reg_markup
            )

            return REGISTER

def recycle(update, context):
    keyboard = [[InlineKeyboardButton("Papers", callback_data=str(ITEM_PAPERS))],
                [InlineKeyboardButton("Electronics", callback_data=str(ITEM_ELECTRONICS))],
                [InlineKeyboardButton("Clothes", callback_data=str(ITEM_CLOTHES))],
                [InlineKeyboardButton("Back", callback_data=str(END))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text="Please select the type of recyclables you want to recycle:",
        reply_markup=reply_markup
    )

    return RECYCLABLES

def papers(update, context):
    keyboard = [[InlineKeyboardButton("Less than 10KG", callback_data=str(PAPER1))],
                [InlineKeyboardButton("20KG to 30KG", callback_data=str(PAPER2))],
                [InlineKeyboardButton("30KG to 40KG", callback_data=str(PAPER3))],
                [InlineKeyboardButton("More than 50KG", callback_data=str(PAPER4))],
                [InlineKeyboardButton("Back", callback_data=str(END))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text="*Please select an estimated weight of your papers:*"\
             "\n\nNeed help in estimating the weight? Click [here](https://i.imgur.com/OvameYt.png)!",
        parse_mode='Markdown',
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )

    return PAPER_WEIGHT

def p1(update, context):
    query = update.callback_query
    bot = context.bot
    user_data = context.user_data
    context.user_data['Papers'] = "Less than 10KG"
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=("*Your current order:*\n{}".format(cache_format(user_data))),
        parse_mode='Markdown'
    )

    keyboard = [["Confirm","Cancel"],
                ["Wait! I have more items to recycle!"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    bot.send_message(
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text="Kindly confirm your order:", 
                     reply_markup=reply_markup
    )

    return CONFIRM

def success(update, context):
    user_data = context.user_data
    order_number = sheet2.acell('C3').value
    userids = str(update.message.from_user.id)
    orders = cache_format(user_data)
    price = sheet3.acell('B2').value
    text = ("*Your order has been confirmed!* 👍🏻")
    
    text2 = ("\n\n*Order No #{0}*"\
             "\n-------------------------"\
             "{1}"\
             "\n*Price* = {2}".format(order_number, orders, price)
    )

    text3 = "\n\nSee FAQ or /help should you need any help"
    #text4= ("Address: {}".format())
    update.message.reply_text(text=text+text2+text3, 
                              parse_mode="Markdown",
                              reply_markup=ReplyKeyboardRemove(True)
                              )
    
    """this is for order message notification
    bot = context.bot
    chat_id="-351944461"
    bot.send_message(chat_id=chat_id, 
                     parse_mode="Markdown", 
                     text=text2)
    """
    sheet2.append_row([order_number, userids, orders, price],value_input_option="RAW")
    return STOPPING

def failure(update, context):
    update.message.reply_text("Sure thing, no worries!", reply_markup=ReplyKeyboardRemove(True))

    return STOPPING

def electronics(update, context):
    keyboard = [[InlineKeyboardButton("Back", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text="WIP!",
        reply_markup=reply_markup
    )
    
    return END

def clothes(update, context):
    keyboard = [[InlineKeyboardButton("Back", callback_data=str(END))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.callback_query.edit_message_text(
        text="WIP!",
        reply_markup=reply_markup
    )
    
    return END

def info(update, context):
    update.callback_query.edit_message_text(
        text="Info placeholder!"
    )

    return END

def helps(update, context):
    update.callback_query.edit_message_text(
        text="WIP!"
    )

    return END

def register(update, context):
    update.callback_query.edit_message_text(
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
                                  "\nThank you for registering! To change your address,"\
                                  " navigate to Help in the menu.".format(cache_format(user_data)))
        
        sheet.append_row([userids,username,userfirstname,postal,address,unit],value_input_option="RAW")
        user_data.clear()

        return start(update, context)

    except KeyError:
        update.message.reply_text('error')

        return end_reg(update, context)

def end(update, context):
    user_data = context.user_data
    user_data.clear()
    update.callback_query.edit_message_text(
        text="Alright! Thank you and have a nice day!"
    )
    return END

def end_reg(update, context):
    user_data = context.user_data
    user_data.clear()
    update.message.reply_text(
        text='No problem! Hope to see you soon!'
    )
    return END

def end_nested(update, context):
    update.callback_query.edit_message_text(
        text="Alright! Thank you and have a nice day!"
    )
    return STOPPING

def end_recycle(update, context):
    data = context.user_data
    data[START_OVER] = True
    start(update, context)
    return END

def end_papers(update, context):
    recycle(update, context)
    return END

def end_clothes(update, context):
    recycle(update, context)
    return END

def end_electronics(update, context):
    recycle(update, context)
    return END

def main():
    updater = Updater('945909213:AAHynjzuKmbJA2f_IoRmUJsSQG2QGr8077U', use_context=True)
    dp = updater.dispatcher

    # Third level (Papers)
    papers_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(papers, pattern='^' + str(ITEM_PAPERS) + '$')],

        states={
            PAPER_WEIGHT: [
                CallbackQueryHandler(p1, pattern='^' + str(PAPER1) + '$')
                #CallbackQueryHandler(p1, pattern='^' + str(PAPER2) + '$'),
                #CallbackQueryHandler(p1, pattern='^' + str(PAPER3) + '$'),
                #CallbackQueryHandler(p1, pattern='^' + str(PAPER4) + '$'),
                
            ],

            CONFIRM: [
                MessageHandler(Filters.regex('^Confirm$'), success),
                MessageHandler(Filters.regex('^Cancel$'), failure)
            ],
        },

        fallbacks=[
            CallbackQueryHandler(end_papers, pattern='^' + str(END) + '$'),
            CommandHandler('stop', end_nested)
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

        },        

        fallbacks=[
            CallbackQueryHandler(end_electronics, pattern='^' + str(END) + '$'),
            CommandHandler('stop', end_nested)
        ],

        map_to_parent={
            STOPPING: END,
            END: RECYCLABLES,
        }
    )

    # Third level (Clothes)
    clothes_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(clothes, pattern='^' + str(ITEM_CLOTHES) + '$')],

        states={

        },        

        fallbacks=[
            CallbackQueryHandler(end_clothes, pattern='^' + str(END) + '$'),
            CommandHandler('stop', end_nested)
        ],

        map_to_parent={
            STOPPING: END,
            END: RECYCLABLES,
        }
    )

    # Second level (Item selection)
    recycle_level = ConversationHandler(
        entry_points=[CallbackQueryHandler(recycle, pattern='^' + str(RECYCLE) + '$')],

        states={
            RECYCLABLES: [papers_level, electronics_level, clothes_level]
        },        

        fallbacks=[
            CallbackQueryHandler(end_recycle, pattern='^' + str(END) + '$'),
            CommandHandler('stop', end_nested)
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

            ADDRESS: [MessageHandler(Filters.text, address)],

            UNIT: [MessageHandler(Filters.text, unit)],
        },
        
        fallbacks=[
            CommandHandler('cancel', end_reg),
            CommandHandler('stop', end_reg)],
    )

    # First level (Main menu)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            REGISTER: [register_level,
                       CallbackQueryHandler(end_reg, pattern='^' + str(REGISTERNO) + '$')],

            MAIN_MENU: [
                recycle_level,
                CallbackQueryHandler(info, pattern='^' + str(INFO) + '$'),
                CallbackQueryHandler(helps, pattern='^' + str(HELP) + '$'),
                CallbackQueryHandler(end, pattern='^' + str(END) + '$')],

        },

        fallbacks=[CommandHandler('stop', end)]
    )

    conv_handler.states[PAPER_WEIGHT] = conv_handler.states[MAIN_MENU]
    conv_handler.states[STOPPING] = conv_handler.entry_points
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
