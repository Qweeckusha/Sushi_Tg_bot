import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import sys
sys.setrecursionlimit(50000)
from functools import *

# Создайте базу данных
conn = sqlite3.connect('store.sql')
cursor = conn.cursor()

# Создаём таблицу для общих последовательностей
cursor.execute('''CREATE TABLE IF NOT EXISTS sequence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    current_value INTEGER
)''')

# Вставьте начальное значение в таблицу последовательности
cursor.execute('INSERT INTO sequence (current_value) VALUES (1)')

# Таблица с суши
cursor.execute('''CREATE TABLE IF NOT EXISTS sushi (
    product_id INTEGER,
    img BLOB,
    name TEXT,
    price INTEGER,
    FOREIGN KEY (product_id) REFERENCES sequence(id)
)''')
# Таблица с напитками
cursor.execute('''CREATE TABLE IF NOT EXISTS drinks (
    product_id INTEGER,
    img BLOB,
    name TEXT,
    price INTEGER,
    FOREIGN KEY (product_id) REFERENCES sequence(id)
)''')

# Таблица с соусами
cursor.execute('''CREATE TABLE IF NOT EXISTS sous (
    product_id INTEGER,
    img BLOB,
    name TEXT,
    price INTEGER,
    FOREIGN KEY (product_id) REFERENCES sequence(id)
)''')

# Общая база всех товаров
cursor.execute('''CREATE TABLE IF NOT EXISTS products
                      (product_id INTEGER,
                       img BLOB,
                       name TEXT,
                       price INTEGER)''')

# Таблицу корзин пользователей
cursor.execute('''CREATE TABLE IF NOT EXISTS carts
                  (user_id TEXT,
                   product_id TEXT,
                   quantity INTEGER)''')

conn.commit()
conn.close()


class SushiProductForm(StatesGroup):
    name = State()  # Ожидание названия товара
    img = State()    # Ожидание картинки для товара
    price = State()   # Ожидание цены товара

class DrinksProductForm(StatesGroup):
    name = State()  # Ожидание названия товара
    img = State()    # Ожидание картинки для товара
    price = State()   # Ожидание цены товара

class SousProductForm(StatesGroup):
    name = State()  # Ожидание названия товара
    img = State()    # Ожидание картинки для товара
    price = State()   # Ожидание цены товара

class UserOrder(StatesGroup):
    name = State()
    phone = State()
    description = State()
    location = State()

API_TOKEN = '6546644497:AAFPX6SIrAX4P89go3MzU_bik2YeTXf_A5A'
PAYMENT_TOKEN = '1744374395:TEST:f1e902e3d3060fb269c9'
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
log = LoggingMiddleware()

class Product:
    def __init__(self, id, img, name, price):
        self.img = img
        self.id = id
        self.name = name
        self.price = price




markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = types.KeyboardButton('Корзина 🛒🍣🛒')
btn2 = types.KeyboardButton('Каталог 🍣🥤🥣')
btn3 = types.KeyboardButton('Настройки ⚙️')
btn4 = types.KeyboardButton('Оператор ☎')
btn5 = types.KeyboardButton('Инфо ℹ️')
markup.add(btn2).row(btn1,btn3).row(btn4, btn5)
@lru_cache(None)
@dp.message_handler(commands=['start'])
async def on_start(message: types.Message):
    await message.answer("Добро пожаловать! Выберите опцию:", reply_markup=markup)
    await message.delete()

async def on_start_rewind(message: types.Message):
    await message.answer("Выберите опцию:", reply_markup=markup)

async def list_of_products(message: types.Message):
    markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Суши-Роллы 🍣')
    btn2 = types.KeyboardButton('Напитки 🥤')
    btn3 = types.KeyboardButton('Соусы 🥣')
    btn4 = types.KeyboardButton('Назад 🔙')
    markup2.row(btn1, btn2)
    markup2.row(btn3, btn4)
    await message.answer('Выберите категорию.', reply_markup=markup2)

async def developer(message: types.Message):
    markup3 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Суши-Роллы add')
    btn2 = types.KeyboardButton('Напитки add')
    btn3 = types.KeyboardButton('Соусы add')
    btn4 = types.KeyboardButton('Удаление из каталога')
    btn5 = types.KeyboardButton('Назад 🔙 ')

    markup3.row(btn1, btn2, btn3).add(btn4,btn5)
    await message.answer('Выберите категорию товара.', reply_markup=markup3)

async def settings(message: types.Message):
    markup4 = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Режим разработчика 👨‍💻')
    btn2 = types.KeyboardButton('Назад 🔙')
    markup4.row(btn1, btn2)
    await message.answer('Вы разделе настройки, выберите опцию.', reply_markup=markup4)

@dp.callback_query_handler(text='order')
async def order(call: types.CallbackQuery):

    user_id = call.message.chat.id
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()

    # Функционал корзины в БД
    cursor.execute('''
            SELECT products.name, products.price, carts.quantity
            FROM carts
            JOIN products ON carts.product_id = products.product_id
            WHERE carts.user_id = ?''', (user_id,))
    cart_items = cursor.fetchall()
    print(f'cart_items for order: {cart_items}')
    conn.commit()
    conn.close()

    if cart_items:
        total_price = 0
        text_desc = "Содержимое корзины:\n"
        await call.message.answer('Корзина: ')
        for item in cart_items:
            print(f'Item for order: {item}')
            product_name, product_price, quantity = item
            total_price += product_price * quantity
            text_desc += f'{product_name} - {product_price} кол-во: {quantity}\n'
        await bot.send_invoice(call.message.chat.id, f'Заказ {user_id}', f'{text_desc}', 'invoice',
                               PAYMENT_TOKEN, 'RUB', [types.LabeledPrice('ORDER', total_price * 100)])

    else:
        await call.message.answer("Ваша корзина пуста.")

@dp.message_handler(content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)
async def payment(msg: types.Message):
    await msg.answer(f'Платеж прошёл успешно.\nИнформация о платеже: {msg.successful_payment.order_info}\n'
                     f'Ваш уникальный ID:{msg.successful_payment.shipping_option_id}')
    await bot.send_message('907894764','1')


@dp.message_handler()
async def buttons(message: types.Message):
    if message.text == 'Корзина 🛒🍣🛒':
        await show_cart(message)
    if message.text == 'Каталог 🍣🥤🥣':
        await list_of_products(message)
    if message.text == 'Настройки ⚙️':
        await settings(message)
    if message.text == 'Суши-Роллы 🍣':
        await show_sushi(message)
    if message.text == 'Напитки 🥤':
        await show_drinks(message)
    if message.text == 'Соусы 🥣':
        await show_sous(message)
    if message.text == 'Назад 🔙 ':
        await on_start_rewind(message)
    if message.text == 'Назад 🔙':
        await on_start_rewind(message)
    if message.text == 'Режим разработчика 👨‍💻':
        await developer(message)
    if message.text == 'Суши-Роллы add':
        await add_product_sushi(message)
    if message.text == 'Напитки add':
        await add_product_drinks(message)
    if message.text == 'Соусы add':
        await add_product_sous(message)
    if message.text == 'Оператор ☎':
        await message.answer(text='@Antyoi\n@moliarka')
    if message.text == 'Инфо ℹ️':
        await bot.send_location(message.from_user.id, '35.6854238', '139.7751616')
        await message.answer('НЕ ПОКУПАЙТЕ ЗДЕСЬ, ЭТО ПРОСТО ПРИМЕР!')
    if message.text == 'Оплатить 💰':
        await register_user_order(message)
    if message.text == 'Удаление из каталога':
        await delete_item(message)
    if message.text == 'Удаление из sushi':
        await delete_item_sushi(message)
    if message.text == 'Удаление из drinks':
        await delete_item_drinks(message)
    if message.text == 'Удаление из sous':
        await delete_item_sous(message)


    await message.delete()

@dp.message_handler(commands=['sushi'])
async def show_sushi(message: types.Message):
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, img, name, price FROM sushi')
    prod_sushi = cursor.fetchall()
    conn.close()

    if prod_sushi:
        products_text = "Список Суши и Роллов:\n"
        for product in prod_sushi:
            product_obj = Product(*product)
            markup = types.InlineKeyboardMarkup()
            btn1 = markup.add(types.InlineKeyboardButton('Добавить', callback_data=f'cartadd:{product_obj.id}'))
            btn2 = markup.add(types.InlineKeyboardButton('Удалить', callback_data=f'cartremove:{product_obj.id}'))
            products_text += f"{product_obj.name} - {product_obj.price} руб.\nНомер товара: {product_obj.id}"
            await bot.send_photo(message.chat.id, photo=f'{product_obj.img}', caption=products_text, reply_markup=markup)
            products_text = "Список Суши и Роллов:\n"
    else:
        await message.answer("В магазине нет товаров.")

@dp.message_handler(commands=['drinks'])
async def show_drinks(message: types.Message):
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, img, name, price FROM drinks')
    prod_drinks = cursor.fetchall()
    conn.close()

    if prod_drinks:
        products_text = "Список Напитков:\n"
        for product in prod_drinks:
            product_obj = Product(*product)
            markup = types.InlineKeyboardMarkup()
            btn1 = markup.add(types.InlineKeyboardButton('Добавить', callback_data=f'cartadd:{product_obj.id}'))
            btn2 = markup.add(types.InlineKeyboardButton('Удалить', callback_data=f'cartremove:{product_obj.id}'))
            products_text += f"{product_obj.name} - {product_obj.price} руб.\nНомер товара: {product_obj.id}"
            await bot.send_photo(message.chat.id, photo=f'{product_obj.img}', caption=products_text, reply_markup=markup)
            products_text = "Список Напитков:\n"
    else:
        await message.answer("В магазине нет товаров.")

@dp.message_handler(commands=['sous'])
async def show_sous(message: types.Message):
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, img, name, price FROM sous')
    prod_sous = cursor.fetchall()
    conn.close()

    if prod_sous:
        products_text = "Список Соусов:\n"
        for product in prod_sous:
            product_obj = Product(*product)
            markup = types.InlineKeyboardMarkup()
            btn1 = markup.add(types.InlineKeyboardButton('Добавить', callback_data=f'cartadd:{product_obj.id}'))
            btn2 = markup.add(types.InlineKeyboardButton('Удалить', callback_data=f'cartremove:{product_obj.id}'))
            products_text += f"{product_obj.name} - {product_obj.price} руб.\nНомер товара: {product_obj.id}"
            await bot.send_photo(message.chat.id, photo=f'{product_obj.img}', caption=products_text, reply_markup=markup)
            products_text = "Список Соусов:\n"
    else:
        await message.answer("В магазине нет товаров.")

@dp.callback_query_handler(lambda a: a.data.startswith('cart'))
async def add_to_cart(call: types.CallbackQuery):
    data_list = call.data.split(':')
    operation = data_list[0]
    product_id = data_list[1]
    print(data_list)
    print(product_id)

    if operation == 'cartadd':
        user_id = call.message.chat.id
        conn = sqlite3.connect('store.sql')
        cursor = conn.cursor()

        # Выбор изображения и имени товара

        cursor.execute('SELECT img, name FROM products WHERE product_id = ?', (product_id,))
        product = cursor.fetchone()
        print(f"Product: {product}")
        product_img, product_name = product

        # Проверяем, есть ли уже данный товар в корзине
        cursor.execute('SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        existing_quantity = cursor.fetchone()

        if existing_quantity:
            # Если товар уже есть, увеличиваем его количество на 1
            new_quantity = existing_quantity[0] + 1
            cursor.execute('UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?',
                           (new_quantity, user_id, product_id))
        else:
            # Если товара нет в корзине, добавляем новую запись с количеством 1
            cursor.execute('INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, 1)', (user_id, product_id))

        conn.commit()
        conn.close()

        print(f"User ID: {user_id}, Product ID: {product_id}")
        await call.message.answer(f"Товар '{product_name}' добавлен в корзину.")

    if operation == 'cartremove':
        user_id = call.message.chat.id
        conn = sqlite3.connect('store.sql')
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        existing_quantity = cursor.fetchone()

        # Изменяем количество, уменьшая на 1.
        if existing_quantity[0] > 1:
            new_quantity = existing_quantity[0] - 1
            cursor.execute('UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?',
                           (new_quantity, user_id, product_id))
            conn.commit()
            await call.message.answer('Вы удалили 1 товар из корзины.')
        else:
            # Удаляем товар из корзины полностью
            cursor.execute('DELETE FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id))
            conn.commit()
            conn.close()
            await call.message.answer('Вы удалили товар из корзины полностью.')


@dp.message_handler(commands=['mycart'])
async def show_cart(message: types.Message):

    user_id = message.from_user.id
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    # Функционал корзины в БД
    cursor.execute('''
        SELECT products.img, products.product_id, products.name, products.price, carts.quantity
        FROM carts
        JOIN products ON carts.product_id = products.product_id
        WHERE carts.user_id = ?''', (user_id,))
    cart_items = cursor.fetchall()
    print(f'cart_items: {cart_items}')
    conn.commit()
    conn.close()
    markup_cart = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_oplata = types.KeyboardButton('Оплатить 💰')
    btn_nazad = types.KeyboardButton('Назад 🔙')
    markup_cart.row(btn_oplata, btn_nazad)

    if cart_items:
        total_price = 0
        cart_text = "Содержимое корзины:\n"
        await message.answer('Корзина: ')
        for item in cart_items:
            print(f'Item: {item}')
            product_img, product_id, product_name, product_price, quantity = item
            total_price += product_price * quantity
            # TODO: добавить проверку на последний элемент в цикле и добавить к нему кнопку, при этом стоит учесть,
            #  что кнопки меняются в cart_handler и полностью заменяются. Если сможем реализовать, то ТОП!
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(f'+', callback_data=f'1cartadd:{product_id}'),
                 InlineKeyboardButton(f'Кол-во: {quantity}', callback_data='ignore'),
                 InlineKeyboardButton(f'-', callback_data=f'1cartremove:{product_id}')],
                [InlineKeyboardButton(f'Итого: {total_price} 💳', callback_data=f'ignore')]
            ])
            await bot.send_photo(message.chat.id, photo=f'{product_img}', caption=f'{product_name} - {product_price} руб.', reply_markup=keyboard)

        await message.answer(f"Вы можете совершить оплату.", reply_markup=markup_cart)

    elif not cart_items:
        await message.answer("Ваша корзина пуста.")

# Обработчик для обработки нажатия кнопок удаления товара из корзины
@dp.callback_query_handler(lambda y: y.data.startswith('1cart'))
async def cart_handler(call: types.CallbackQuery):
    user_id = call.message.chat.id
    data_list = call.data.split(':')
    print(data_list)
    operation = data_list[0]
    product_id = data_list[1]

    # ------------
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    current_quantity = cursor.fetchone()[0]
    print(f'cur_quantity: {current_quantity}')



    if operation == '1cartadd':
        new_quantity = current_quantity + 1
        cursor.execute('UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?',
                       (new_quantity, user_id, product_id))
        conn.commit()
        cursor.execute('''
                    SELECT name, price FROM products WHERE product_id = ?''', (product_id,))
        product_info_add = cursor.fetchone()
        product_name_add, product_price_add = product_info_add
        print(f'Product_info: {product_info_add}')
        # ------------
        # Всё ради total_price
        # FIXME: было бы славно как-то total price сделать глобальным для клавиатур, то есть надо обновлять как-то клавиатуры одновременно
        cursor.execute('''
                    SELECT products.price, carts.quantity
                    FROM carts
                    JOIN products ON carts.product_id = products.product_id
                    WHERE carts.user_id = ?''', (user_id,))
        cart_items = cursor.fetchall()
        if cart_items:
            total_price = 0
            for item in cart_items:
                product_price, quantity = item
                total_price += product_price * quantity
        # -------------

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(f'+', callback_data=f'1cartadd:{product_id}'),
             InlineKeyboardButton(f'Кол-во: {new_quantity}', callback_data=f'1cartadd:{product_id}'),
             InlineKeyboardButton(f'-', callback_data=f'1cartremove:{product_id}')],
            [InlineKeyboardButton(f'Итого: {total_price} 💳', callback_data=f'ignore')]
        ])

        await call.message.edit_caption(f'{product_name_add} - {product_price_add} руб.', reply_markup=keyboard)


    if operation == '1cartremove' and current_quantity > 1:
        new_quantity = current_quantity - 1
        cursor.execute('UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?',
                       (new_quantity, user_id, product_id))
        conn.commit()
        cursor.execute('''
                    SELECT name, price FROM products WHERE product_id = ?''', (product_id,))
        product_info_remove = cursor.fetchone()
        product_name_remove, product_price_remove = product_info_remove
        print(f'Product_info: {product_info_remove}')

        # ------------
        # Всё ради total_price
        # FIXME: было бы славно как-то total price сделать глобальным для клавиатур, то есть надо обновлять как-то клавиатуры одновременно
        cursor.execute('''
                    SELECT products.price, carts.quantity
                    FROM carts
                    JOIN products ON carts.product_id = products.product_id
                    WHERE carts.user_id = ?''', (user_id,))
        cart_items = cursor.fetchall()
        if cart_items:
            total_price = 0
            for item in cart_items:
                product_price, quantity = item
                total_price += product_price * quantity
        # -------------

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(f'+', callback_data=f'1cartadd:{product_id}'),
             InlineKeyboardButton(f'Кол-во: {new_quantity}', callback_data=f'ingore'),
             InlineKeyboardButton(f'-', callback_data=f'1cartremove:{product_id}')],
            [InlineKeyboardButton(f'Итого: {total_price} 💳', callback_data=f'ingore')]
        ])

        await call.message.edit_caption(f'{product_name_remove} - {product_price_remove} руб.', reply_markup=keyboard)


    if operation == '1cartremove' and current_quantity == 1:
            # Удаляем товар из корзины полностью
        cursor.execute('DELETE FROM carts WHERE user_id = ? AND product_id = ?', (user_id, product_id))
        conn.commit()
        conn.close()
        await call.message.delete()
        await call.message.answer('Вы удалили товар из корзины.')


    # # Обновляем сообщение с корзиной
    # await show_cart(call.message)

    # # Очистка корзины после оформления заказа
    # cursor.execute('DELETE FROM carts WHERE user_id = ?', (user_id,))
    # conn.commit()
    # conn.close()
    # await message.answer("Ваш заказ оформлен. Спасибо!")


async def register_user_order(message: types.Message):
    await message.answer('Оформите заказ:')
    await message.answer('Введите своё имя.')
    await UserOrder.name.set()

@dp.message_handler(state=UserOrder.name)
async def order_name(message: types.Message, state: FSMContext):
    async with state.proxy() as dataOrder:
        dataOrder['name'] = message.text

    await message.answer('Введите свой номер телефона в любом удобном вам формате (Например: +7 (9xx) xxx xx-xx)')

    await UserOrder.phone.set()

@dp.message_handler(state=UserOrder.phone)
async def order_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as dataOrder:
        dataOrder['phone'] = message.text

    await message.answer('Введите комментарий к заказу, если нет комментария, то отправьте "нет".')

    await UserOrder.description.set()

@dp.message_handler(state=UserOrder.description)
async def order_desc(message: types.Message, state: FSMContext):
    async with state.proxy() as dataOrder:
        dataOrder['desc'] = message.text

    await message.answer('Отправьте свой адрес. (Пример: Город, улица, номер дома, корпус, подъезд, этаж, квартира)')

    await UserOrder.location.set()

@dp.message_handler(state=UserOrder.location)
async def order_loc(message: types.Message, state: FSMContext):
    async with state.proxy() as dataOrder:
        dataOrder['loc'] = message.text

    await message.answer('Проверьте данные к заказу.', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton('Оплатить', callback_data='order')]
    ]))
    await state.finish()



    # await bot.send_invoice(call.message.chat.id, f'Заказ {user_id}', f'{text_desc}', 'invoice',
    #                        config.PAYMENT_TOKEN, 'RUB', [types.LabeledPrice('ORDER', total_price * 100)])














# Обработка удаления из каталога

async def delete_item(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Удаление из sushi')
    btn2 = types.KeyboardButton('Удаление из drinks')
    btn3 = types.KeyboardButton('Удаление из sous')
    btn4 = types.KeyboardButton('Назад 🔙')
    markup.row(btn1)
    markup.row(btn2)
    markup.row(btn3)
    markup.row(btn4)
    await message.answer('Выберите раздел.', reply_markup=markup)
# @dp.message_handler()
# async def buttons(message: types.Message):
#     if message.text == '':
#         await show_cart(message)
#     if message.text == 'Каталог 🍣🥤🥣':
#         await list_of_products(message)
#     if message.text == 'Настройки ⚙️':
#         await settings(message)
@dp.message_handler(commands=['deletesushi'])
async def delete_item_sushi(message: types.Message):
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, img, name, price FROM sushi')
    prod_sushi = cursor.fetchall()
    conn.close()

    if prod_sushi:
        products_text = "Суши и Роллы:\n"
        for product in prod_sushi:
            product_obj = Product(*product)
            markup = types.InlineKeyboardMarkup()
            btn1 = markup.add(types.InlineKeyboardButton('Удалить полностью', callback_data=f'remsushi:{product_obj.id}'))
            products_text += f"{product_obj.name} - {product_obj.price} руб.\nНомер товара: {product_obj.id}"
            await bot.send_photo(message.chat.id, photo=f'{product_obj.img}', caption=products_text,
                                 reply_markup=markup)
            products_text = "Суши и Роллы:\n"
    else:
        await message.answer("В магазине нет товаров.")

@dp.message_handler(commands=['deletedrink'])
async def delete_item_drinks(message: types.Message):
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, img, name, price FROM drinks')
    prod_drinks = cursor.fetchall()
    conn.close()

    if prod_drinks:
        products_text = "Напитки:\n"
        for product in prod_drinks:
            product_obj = Product(*product)
            markup = types.InlineKeyboardMarkup()
            btn1 = markup.add(types.InlineKeyboardButton('Удалить полностью', callback_data=f'remdrinks:{product_obj.id}'))
            products_text += f"{product_obj.name} - {product_obj.price} руб.\nНомер товара: {product_obj.id}"
            await bot.send_photo(message.chat.id, photo=f'{product_obj.img}', caption=products_text,
                                 reply_markup=markup)
            products_text = "Напитки:\n"
    else:
        await message.answer("В магазине нет товаров.")

@dp.message_handler(commands=['deletesous'])
async def delete_item_sous(message: types.Message):
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute('SELECT product_id, img, name, price FROM sous')
    prod_sous = cursor.fetchall()
    conn.close()

    if prod_sous:
        products_text = "Соусы:\n"
        for product in prod_sous:
            product_obj = Product(*product)
            markup = types.InlineKeyboardMarkup()
            btn1 = markup.add(types.InlineKeyboardButton('Удалить полностью', callback_data=f'remsous:{product_obj.id}'))
            products_text += f"{product_obj.name} - {product_obj.price} руб.\nНомер товара: {product_obj.id}"
            await bot.send_photo(message.chat.id, photo=f'{product_obj.img}', caption=products_text,
                                 reply_markup=markup)
            products_text = "Соусы:\n"
    else:
        await message.answer("В магазине нет товаров.")




# callback на удаление
@dp.callback_query_handler(lambda c: c.data.startswith('rem'))
async def remove_item(call: types.CallbackQuery):
    data_list = call.data.split(':')
    operation = data_list[0]
    product_id = data_list[1]
    print(operation, product_id)
    if operation == 'remsushi':
        conn = sqlite3.connect('store.sql')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        cursor.execute('DELETE FROM sushi WHERE product_id = ?', (product_id,))
        conn.commit()
        conn.close()
        await call.message.answer('Вы полностью удалили товар')
    if operation == 'remdrinks':
        conn = sqlite3.connect('store.sql')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        cursor.execute('DELETE FROM drinks WHERE product_id = ?', (product_id,))
        conn.commit()
        conn.close()
        await call.message.answer('Вы полностью удалили товар')
    if operation == 'remsous':
        conn = sqlite3.connect('store.sql')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        conn.commit()
        cursor.execute('DELETE FROM sous WHERE product_id = ?', (product_id,))
        conn.commit()
        conn.close()
        await call.message.answer('Вы полностью удалили товар')


# Обработка добавления в БД sushi

@dp.message_handler(commands=['add_sushi'])
async def add_product_sushi(message: types.Message):
    user_id = message.from_user.id

    # Проверка, что пользователь - администратор (вам нужно реализовать эту проверку в соответствии с вашими требованиями)
    is_admin = True  # Предположим, что пользователь с ID 123 является администратором
    if not is_admin:
        await message.answer("Вы не администратор. Эта команда доступна только администраторам.")
        return

    # Ожидание названия товара
    await message.answer("Введите название товара для Суши и Роллов:")
    await SushiProductForm.name.set()


@dp.message_handler(lambda message: 'отмена' in message.text.lower(), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('ok')

# Обработчик для ожидания названия товара
@dp.message_handler(state=SushiProductForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as dataSushi:
        dataSushi['name'] = message.text

    # Переход к ожиданию цены
    await message.answer("Отправьте картинку товара для Суши и Роллов:")
    await SushiProductForm.next()


# Обработчик для ожидания картинки товара
@dp.message_handler(content_types=['photo'], state=SushiProductForm.img)
async def process_img(message: types.Message, state: FSMContext):
    async with state.proxy() as dataSushi:
        dataSushi['img'] = message.photo[-1].file_id

    # Переход к ожиданию цены
    await message.answer("Введите цену товара для Суши и Роллов:")
    await SushiProductForm.next()

# Обработчик для ожидания цены
@dp.message_handler(lambda message: not message.text.isdigit(), state=SushiProductForm.price)
async def process_price_invalid(message: types.Message):
    await message.answer("Пожалуйста, введите цену числом (например, 100).")

# Обработчик для цены товара и добавление в БД
@dp.message_handler(lambda message: message.text.isdigit(), state=SushiProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as dataSushi:
        dataSushi['price'] = int(message.text)

    # Получаем данные из формы
    product_dataSushi = dataSushi['img'], dataSushi['name'], dataSushi['price']

    # Добавляем товар в базу данных
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sushi (product_id, img, name, price) VALUES ((SELECT current_value FROM sequence WHERE id = 1),?, ?, ?)',
        product_dataSushi)
    conn.commit()
    cursor.execute('INSERT INTO products (product_id, img, name, price) VALUES ((SELECT current_value FROM sequence WHERE id = 1),?, ?, ?)',product_dataSushi)
    conn.commit()
    cursor.execute('UPDATE sequence SET current_value = current_value + 1 WHERE id = 1')
    conn.commit()
    conn.close()

    await state.finish()
    await bot.send_photo(message.chat.id, photo=product_dataSushi[0],
                         caption=f"Товар {product_dataSushi[1]} с ценой {product_dataSushi[2]} руб. добавлен в базу данных 'sushi'")


# Обработка добавления в БД drinks
@dp.message_handler(commands=['add_drinks'])
async def add_product_drinks(message: types.Message):
    user_id = message.from_user.id

    # Проверка, что пользователь - администратор (вам нужно реализовать эту проверку в соответствии с вашими требованиями)
    is_admin = True  # Предположим, что пользователь с ID 123 является администратором
    if not is_admin:
        await message.answer("Вы не администратор. Эта команда доступна только администраторам.")
        return

    # Ожидание названия товара
    await message.answer("Введите название товара для Напитков:")
    await DrinksProductForm.name.set()

# Обработчик для ожидания названия товара
@dp.message_handler(state=DrinksProductForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as dataDrinks:
        dataDrinks['name'] = message.text

    # Переход к ожиданию цены
    await message.answer("Отправьте картинку товара для Напитков:")
    await DrinksProductForm.next()

# Обработчик для ожидания картинки товара
@dp.message_handler(content_types=['photo'], state=DrinksProductForm.img)
async def process_img(message: types.Message, state: FSMContext):
    async with state.proxy() as dataDrinks:
        dataDrinks['img'] = message.photo[-1].file_id

    # Переход к ожиданию цены
    await message.answer("Введите цену товара для Напитков:")
    await DrinksProductForm.next()

# Обработчик для ожидания цены
@dp.message_handler(lambda message: not message.text.isdigit(), state=DrinksProductForm.price)
async def process_price_invalid(message: types.Message):
    await message.answer("Пожалуйста, введите цену числом (например, 100).")

# Обработчик для цены товара и добавление в БД
@dp.message_handler(lambda message: message.text.isdigit(), state=DrinksProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as dataDrinks:
        dataDrinks['price'] = int(message.text)

    # Получаем данные из формы
    product_dataDrinks = dataDrinks['img'], dataDrinks['name'], dataDrinks['price']

    # Добавляем товар в базу данных
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO drinks (product_id, img, name, price) VALUES ((SELECT current_value FROM sequence WHERE id = 1),?, ?, ?)',
        product_dataDrinks)
    conn.commit()
    cursor.execute(
        'INSERT INTO products (product_id, img, name, price) VALUES ((SELECT current_value FROM sequence WHERE id = 1),?, ?, ?)',
        product_dataDrinks)
    conn.commit()
    cursor.execute('UPDATE sequence SET current_value = current_value + 1 WHERE id = 1')
    conn.commit()
    conn.close()

    await state.finish()
    await bot.send_photo(message.chat.id, photo=product_dataDrinks[0],
                         caption=f"Товар {product_dataDrinks[1]} с ценой {product_dataDrinks[2]} руб. добавлен в базу данных 'drinks'.")


# Обработка добавления в БД sous
@dp.message_handler(commands=['add_sous'])
async def add_product_sous(message: types.Message):
    user_id = message.from_user.id

    # Проверка, что пользователь - администратор (вам нужно реализовать эту проверку в соответствии с вашими требованиями)
    is_admin = True  # Предположим, что пользователь с ID 123 является администратором
    if not is_admin:
        await message.answer("Вы не администратор. Эта команда доступна только администраторам.")
        return

    # Ожидание названия товара
    await message.answer("Введите название товара для соусов:")
    await SousProductForm.name.set()

# Обработчик для ожидания названия товара
@dp.message_handler(state=SousProductForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as dataSous:
        dataSous['name'] = message.text

    # Переход к ожиданию цены
    await message.answer("Отправьте картинку товара для Соусов:")
    await SousProductForm.next()

# Обработчик для ожидания картинки товара
@dp.message_handler(content_types=['photo'], state=SousProductForm.img)
async def process_img(message: types.Message, state: FSMContext):
    async with state.proxy() as dataSous:
        dataSous['img'] = message.photo[-1].file_id

    # Переход к ожиданию цены
    await message.answer("Введите цену товара для Соусов:")
    await SousProductForm.next()

# Обработчик для ожидания цены
@dp.message_handler(lambda message: not message.text.isdigit(), state=SousProductForm.price)
async def process_price_invalid(message: types.Message):
    await message.answer("Пожалуйста, введите цену числом (например, 100).")

# Обработчик для цены товара и добавление в БД
@dp.message_handler(lambda message: message.text.isdigit(), state=SousProductForm.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as dataSous:
        dataSous['price'] = int(message.text)

    # Получаем данные из формы
    product_dataSous = dataSous['img'], dataSous['name'], dataSous['price']

    # Добавляем товар в базу данных
    conn = sqlite3.connect('store.sql')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO sous (product_id, img, name, price) VALUES ((SELECT current_value FROM sequence WHERE id = 1),?, ?, ?)',
        product_dataSous)
    conn.commit()
    cursor.execute(
        'INSERT INTO products (product_id, img, name, price) VALUES ((SELECT current_value FROM sequence WHERE id = 1),?, ?, ?)',
        product_dataSous)
    conn.commit()
    cursor.execute('UPDATE sequence SET current_value = current_value + 1 WHERE id = 1')
    conn.commit()
    conn.close()

    await state.finish()
    await bot.send_photo(message.chat.id, photo=product_dataSous[0],
                         caption=f"Товар {product_dataSous[1]} с ценой {product_dataSous[2]} руб. добавлен в базу данных 'sous'.")


if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
