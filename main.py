from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, 
                      ReplyKeyboardRemove, KeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)


# States
FIRST, SECOND, THIRD, CONFIRM = range(4)
# Primary callbacks
RECYCLE, INFO, FAQ, DONE = range(4)
# Secondary callbacks
PAPERS, ELECTRONICS, CLOTHES, BACK1, BACK2, PAPER1, PAPER2, PAPER3 = range(8)

END = ConversationHandler.END

# Main Defs
def start(update, context):
    keyboard = [[InlineKeyboardButton('Start recycling! ♻️', callback_data=str(RECYCLE))],
                [InlineKeyboardButton('Info 📋', callback_data=str(INFO))],
                [InlineKeyboardButton('Help 🙋🏻‍♀️', callback_data=str(FAQ))],
                [InlineKeyboardButton('Done', callback_data=str(DONE))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        'Hi! I am a recycling bot'\
        '\n\nWhat would you like to do?',
        reply_markup=reply_markup
    )

    return FIRST


def recycle(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [[InlineKeyboardButton('Papers', callback_data=str(PAPERS))],
                [InlineKeyboardButton('Electronics', callback_data=str(ELECTRONICS))],
                [InlineKeyboardButton('Clothes', callback_data=str(CLOTHES))],
                [InlineKeyboardButton('Back', callback_data=str(BACK1))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text='Please select the type of recyclables:',
        reply_markup=reply_markup
    )

    return SECOND

def papers(update, context):
    query = update.callback_query
    bot = context.bot
    keyboard = [[InlineKeyboardButton('Less than 20KG', callback_data=str(PAPER1))],
                [InlineKeyboardButton('20KG to 30KG', callback_data=str(PAPER2))],
                [InlineKeyboardButton('30KG to 40KG', callback_data=str(PAPER3))],
                [InlineKeyboardButton('Back', callback_data=str(BACK2))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text='Please select an estimated weight of your papers:',
        reply_markup=reply_markup
    )

    return THIRD

def p1(update, context):
    query = update.callback_query
    bot = context.bot
    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text='You will receive [$1.00 - $1.50] for your recyclables'
    )

    keyboard = [['Yes','No']]
    reply_markup = ReplyKeyboardMarkup(keyboard, 
                   one_time_keyboard=True, 
                   resize_keyboard=True
                   )

    bot.send_message(
                     chat_id=query.message.chat_id,
                     message_id=query.message.message_id,
                     text='Kindly confirm your order:', 
                     reply_markup=reply_markup
        )

    return CONFIRM

def choiceyes(update, context):
    text =  '*Your order has been confirmed*'

    text2 = '\n\nOrder No #01'\
            '\n--------------------'\
            '\n*Item*: Papers'\
            '\n*Weight*: Less than 20KG'\
            '\n*Price* ≈ $1.00 - $1.50'\

    text3 = '\n\nSee FAQ or /help should you need any help'
    update.message.reply_text(text=text+text2+text3, 
                              parse_mode='Markdown',
                              reply_markup=ReplyKeyboardRemove(True)
                              )
    #bot = context.bot
    #chat_id='-351944461'
    #bot.send_message(chat_id=chat_id, 
    #                 parse_mode='Markdown', 
    #                 text=text2)


    return end

def choiceno(update, context):
    update.message.reply_text('Sure thing, no worries!', reply_markup=ReplyKeyboardRemove(True))

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
        text="WIP!"
    )

    return END

def faq(update, context):
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
        text='Thank you and have a nice day! See you next time!'
    )

    return END


def main():
    updater = Updater('945909213:AAHynjzuKmbJA2f_IoRmUJsSQG2QGr8077U', use_context=True)
    dp = updater.dispatcher

    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            FIRST:  [CallbackQueryHandler(recycle, pattern='^' + str(RECYCLE) + '$'),
                     CallbackQueryHandler(info, pattern='^' + str(INFO) + '$'),
                     CallbackQueryHandler(faq, pattern='^' + str(FAQ) + '$'),
                     CallbackQueryHandler(end, pattern='^' + str(DONE) + '$')],

            SECOND: [CallbackQueryHandler(papers, pattern='^' + str(PAPERS) + '$'),
                     CallbackQueryHandler(electronics, pattern='^' + str(ELECTRONICS) + '$'),
                     CallbackQueryHandler(clothes, pattern='^' + str(CLOTHES) + '$'),
                     CallbackQueryHandler(start, pattern='^' + str(BACK1) + '$')],

            THIRD:  [CallbackQueryHandler(p1, pattern='^' + str(PAPER1) + '$'),
                     CallbackQueryHandler(p1, pattern='^' + str(PAPER2) + '$'),
                     CallbackQueryHandler(p1, pattern='^' + str(PAPER3) + '$'),
                     CallbackQueryHandler(recycle, pattern='^' + str(BACK2) + '$')],

            CONFIRM:  [MessageHandler(Filters.regex('^Yes$'), choiceyes),
                       MessageHandler(Filters.regex('^No$'), choiceno)
                      ],
                     
        },

        fallbacks=[CommandHandler('start', start)]
    )
    dp.add_handler(CommandHandler('choiceyes', choiceyes))
    dp.add_handler(conv_handler)
    updater.start_polling(read_latency=0)
    updater.idle()

if __name__ == '__main__':
    main()
