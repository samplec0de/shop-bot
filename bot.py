import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler, CallbackQueryHandler

SEND_ORDERS_TO = 131898478


def new_message(update: Update, context: CallbackContext):
    update.effective_message.reply_text('Hello!')


def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton('Выпечка', callback_data='category_bakery')],
        [InlineKeyboardButton('Напитки', callback_data='category_drinks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.reply_text('Здравствуйте! Выберете категорию товара:',
                                        reply_markup=reply_markup)


def set_category(update: Update, context: CallbackContext):
    query = update.callback_query
    category = query.data.split('_')[-1]
    if category == 'bakery':
        keyboard = [
            [InlineKeyboardButton('Пирожок', callback_data='item_pirozhok'),
             InlineKeyboardButton('Булочка', callback_data='item_bulochka')]
        ]
    elif category == 'drinks':
        keyboard = [
            [InlineKeyboardButton('Вода', callback_data='item_water'),
             InlineKeyboardButton('Лимонад', callback_data='item_lemonade')]
        ]
    else:
        keyboard = []
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.edit_text('Доступные товары:',
                                       reply_markup=reply_markup)
    query.answer('Приятных покупок')


def get_new_order_id() -> int:
    """ Возвращает ид нового заказ """
    with open('last_order', 'r') as file:
        last_order_id = int(file.read())
    with open('last_order', 'w') as file:
        file.write(str(last_order_id + 1))
    return last_order_id + 1


def buy_item(update: Update, context: CallbackContext):
    query = update.callback_query
    item = query.data.split('_')[-1]
    order_id = get_new_order_id()
    update.effective_message.edit_text(f'Ваш заказ отправлен на сборку, ожидайте!\n'
                                       f'Номер заказа: {order_id}\n'
                                       f'Оплата: наличиными или по карте на кассе')
    keyboard = [
        [InlineKeyboardButton('Готов', callback_data=f'ready_{order_id}_{update.effective_user.id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=SEND_ORDERS_TO, reply_markup=reply_markup,
                             text=f'Пришел новый заказ #{order_id}, содержимое: {item}')
    query.answer(f'Ваш заказ {order_id} отправлен на сборку')


def order_ready(update: Update, context: CallbackContext):
    query = update.callback_query
    order_id, user_id = query.data.split('_')[1:]
    context.bot.send_message(chat_id=user_id, text=f'Ваш заказ {order_id} готов. Забирайте!')
    keyboard = [
        [InlineKeyboardButton("Закрыть", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_message.edit_text(f'Заказ {order_id} выполнен', reply_markup=reply_markup)


def close_message(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer('Спасибо за ващу работу!')
    update.effective_message.delete()


def get_id(update: Update, context: CallbackContext):
    update.effective_message.reply_text(f'Ваш id: {update.effective_user.id}')


def main():
    """ Запуск бота """
    BOT_TOKEN = os.environ.get('TOKEN')
    if BOT_TOKEN is None:
        print('Ошибка: токен не задан!')
        exit(0)
    # Создаем Updater и передаем ему токен.
    updater = Updater(BOT_TOKEN)
    # Получаем dispatcher для регистрации обработчиков
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('id', get_id))
    dispatcher.add_handler(MessageHandler(Filters.text, new_message))
    dispatcher.add_handler(CallbackQueryHandler(set_category, pattern=r'^category_.*$'))
    dispatcher.add_handler(CallbackQueryHandler(buy_item, pattern=r'^item_.*$'))
    dispatcher.add_handler(CallbackQueryHandler(order_ready, pattern=r'^ready_.*$'))
    dispatcher.add_handler(CallbackQueryHandler(close_message, pattern=r'^close$'))
    # Запускаем бота
    updater.start_polling()
    # Делаем так, чтобы бот работал пока не нажмем Ctrl-C или процесс получит
    # сигнал остановки (SIGINT, SIGTERM или SIGABRT). Это необходимо, потому что
    # start_polling() не блокирует программу и нам нужно аккуратно остановить бота.
    updater.idle()


main()
