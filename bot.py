import asyncio
import random
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ====== НАСТРОЙКИ ======
BOT_TOKEN = "8568900269:AAHsv_z5JCFo8rEMI9FHgxWFQPfoFz128K4"
ADMIN_ID = 8265341848
SUPPORT = "@symskooy"

DB = "orders.db"

# Курс для отображения (ты сказал 42 грн)
USDT_RATE_UAH = 42.0


# ====== ТОВАРЫ (UAH на кнопках, оплата по ссылке @send в USDT) ======
# Здесь мы привязываем товар -> (название, цена грн, ссылка на чек)
PRODUCTS = {
    # S@nos
    "snos_site": ("S@nos — Сайт", 45, "t.me/send?start=IVcqaNJ462tP"),      # 1.1 USDT
    "snos_code": ("S@nos — Код на Python", 126, "t.me/send?start=IVQfkEjD8Rbi"),  # 3 USDT
    "snos_bot":  ("S@nos — Бот (навсегда)", 210, "t.me/send?start=IVgiUI9iYSTG"), # 5 USDT

    # Боты/коды на заказ
    "order_bot": ("Бот (на заказ)", 67, "t.me/send?start=IVAM79Xz7z8O"),     # 1.6 USDT
    "order_code": ("Коды на Python (на заказ)", 50, "t.me/send?start=IVjuLHHcWCei"), # 1.2 USDT

    # Аккаунты (цены в грн)
    "acc_usa": ("Аккаунт Америка (+1)", 45, "t.me/send?start=IVAM79Xz7z8O"),     # 1.6 USDT
    "acc_india": ("Аккаунт Индия", 35, "t.me/send?start=IVVYy6Np5oGM"),          # 1.0 USDT
    "acc_vene": ("Аккаунт Венесуэла", 40, "t.me/send?start=IVcqaNJ462tP"),       # 1.1 USDT
    "acc_canada": ("Аккаунт Канада", 50, "t.me/send?start=IVjuLHHcWCei"),        # 1.2 USDT
    "acc_ukraine": ("Аккаунт Украина", 400, "t.me/send?start=IVUuzNcsSPO7"),     # 9.55 USDT
}

# Отдельно текст для "аккаунты на заказ"
ACCOUNTS_CUSTOM_TEXT = (
    "🧾 Аккаунты на заказ\n\n"
    f"Заказать можно, написав {SUPPORT}\n"
)


# ====== БД ======
def db_connect():
    return sqlite3.connect(DB)


def init_db():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            user_id INTEGER,
            username TEXT,
            product_key TEXT,
            product_name TEXT,
            price_uah REAL,
            pay_link TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_order(order_id: str, user_id: int, username: str, product_key: str):
    name, price_uah, pay_link = PRODUCTS[product_key]
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (order_id, user_id, username, product_key, product_name, price_uah, pay_link, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_id, user_id, username, product_key, name, float(price_uah), pay_link,
        "WAITING_CONFIRM", datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()


def get_order(order_id: str):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT order_id, user_id, username, product_key, product_name, price_uah, pay_link, status
        FROM orders WHERE order_id=?
    """, (order_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_status(order_id: str, status: str):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=? WHERE order_id=?", (status, order_id))
    conn.commit()
    conn.close()


# ====== БОТ ======
bot = Bot(BOT_TOKEN)
dp = Dispatcher()


def kb_main():
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Покупка", callback_data="shop")
    kb.button(text="ℹ️ Информация", callback_data="info")
    kb.adjust(1)
    return kb.as_markup()


def kb_shop():
    kb = InlineKeyboardBuilder()
    kb.button(text="🧩 S@nos", callback_data="menu_snos")
    kb.button(text="🤖 Боты/коды (на заказ)", callback_data="menu_order")
    kb.button(text="👤 Покупка аккаунта", callback_data="menu_acc")
    kb.button(text="🧾 Аккаунты на заказ", callback_data="acc_custom")
    kb.button(text="⬅️ Назад", callback_data="back_main")
    kb.adjust(1)
    return kb.as_markup()


def kb_snos():
    kb = InlineKeyboardBuilder()
    kb.button(text="S@nos сайт — 45 грн", callback_data="buy:snos_site")
    kb.button(text="Код на Python — 126 грн", callback_data="buy:snos_code")
    kb.button(text="Бот (навсегда) — 210 грн", callback_data="buy:snos_bot")
    kb.button(text="⬅️ Назад", callback_data="shop")
    kb.adjust(1)
    return kb.as_markup()


def kb_order():
    kb = InlineKeyboardBuilder()
    kb.button(text="Бот (на заказ) — 67 грн", callback_data="buy:order_bot")
    kb.button(text="Коды на Python — 50 грн", callback_data="buy:order_code")
    kb.button(text="⬅️ Назад", callback_data="shop")
    kb.adjust(1)
    return kb.as_markup()


def kb_accounts():
    kb = InlineKeyboardBuilder()
    kb.button(text="Америка (+1) — 45 грн", callback_data="buy:acc_usa")
    kb.button(text="Индия — 35 грн", callback_data="buy:acc_india")
    kb.button(text="Венесуэла — 40 грн", callback_data="buy:acc_vene")
    kb.button(text="Канада — 50 грн", callback_data="buy:acc_canada")
    kb.button(text="Украина — 400 грн", callback_data="buy:acc_ukraine")
    kb.button(text="⬅️ Назад", callback_data="shop")
    kb.adjust(1)
    return kb.as_markup()


def kb_pay(order_id: str, pay_link: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Оплатить (USDT)", url=f"https://{pay_link}" if pay_link.startswith("t.me/") else pay_link)
    kb.button(text="✅ Я оплатил (отправить на проверку)", callback_data=f"confirm:{order_id}")
    kb.button(text="⬅️ Назад", callback_data="shop")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(CommandStart())
async def start(m: Message):
    await m.answer(
        "👋 Привет! Выбирай, что хочешь купить.\n"
        "Цены указаны в грн, оплата — в USDT по чеку.",
        reply_markup=kb_main()
    )


@dp.callback_query(F.data == "back_main")
async def back_main(cb: CallbackQuery):
    await cb.message.edit_text(
        "👋 Привет! Выбирай, что хочешь купить.\n"
        "Цены указаны в грн, оплата — в USDT по чеку.",
        reply_markup=kb_main()
    )


@dp.callback_query(F.data == "info")
async def info(cb: CallbackQuery):
    await cb.message.edit_text(
        "ℹ️ Информация\n\n"
        "Оплата: USDT через Crypto Bot (чек).\n"
        f"После оплаты нажмите «Я оплатил», затем ожидайте сообщение.\n\n"
        f"Поддержка: {SUPPORT}",
        reply_markup=kb_main()
    )


@dp.callback_query(F.data == "shop")
async def shop(cb: CallbackQuery):
    await cb.message.edit_text("🛒 Выбери раздел:", reply_markup=kb_shop())


@dp.callback_query(F.data == "menu_snos")
async def menu_snos(cb: CallbackQuery):
    await cb.message.edit_text("🧩 S@nos — выбери товар:", reply_markup=kb_snos())


@dp.callback_query(F.data == "menu_order")
async def menu_order(cb: CallbackQuery):
    await cb.message.edit_text("🤖 Боты/коды (на заказ) — выбери:", reply_markup=kb_order())


@dp.callback_query(F.data == "menu_acc")
async def menu_acc(cb: CallbackQuery):
    await cb.message.edit_text("👤 Покупка аккаунта — выбери страну:", reply_markup=kb_accounts())


@dp.callback_query(F.data == "acc_custom")
async def acc_custom(cb: CallbackQuery):
    await cb.message.edit_text(ACCOUNTS_CUSTOM_TEXT, reply_markup=kb_shop())


@dp.callback_query(F.data.startswith("buy:"))
async def buy(cb: CallbackQuery):
    product_key = cb.data.split(":", 1)[1]
    if product_key not in PRODUCTS:
        await cb.answer("Товар не найден", show_alert=True)
        return

    order_id = str(random.randint(10000, 99999))
    username = cb.from_user.username or "no_username"

    create_order(order_id, cb.from_user.id, username, product_key)

    name, price_uah, pay_link = PRODUCTS[product_key]
    approx_usdt = float(price_uah) / USDT_RATE_UAH

    # Попытка уведомить админа (если админ не нажал /start — будет ошибка, но бот не упадёт)
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 Новый заказ создан (ещё не подтверждён)\n"
            f"Заказ: #{order_id}\n"
            f"Товар: {name}\n"
            f"Цена: {price_uah} грн (~{approx_usdt:.2f} USDT)\n"
            f"Пользователь: @{username} (id {cb.from_user.id})\n"
            f"Ссылка на оплату: https://{pay_link}" if pay_link.startswith("t.me/") else pay_link
        )
    except Exception as e:
        print(f"ADMIN NOTIFY ERROR: {repr(e)}")

    await cb.message.edit_text(
        f"🧾 Заказ создан\n\n"
        f"Номер заказа: #{order_id}\n"
        f"Товар: {name}\n"
        f"Цена: {price_uah} грн\n"
        f"Оплата: USDT (по чеку)\n\n"
        f"Нажми «Оплатить», потом «Я оплатил».",
        reply_markup=kb_pay(order_id, pay_link)
    )


@dp.callback_query(F.data.startswith("confirm:"))
async def confirm(cb: CallbackQuery):
    order_id = cb.data.split(":", 1)[1]
    row = get_order(order_id)
    if not row:
        await cb.answer("Заказ не найден", show_alert=True)
        return

    _order_id, user_id, username, product_key, product_name, price_uah, pay_link, status = row

    set_status(order_id, "SENT_TO_ADMIN")

    # Сообщение пользователю
    await cb.message.edit_text(
        "✅ Запрос на проверку отправлен!\n\n"
        f"Заказ: #{order_id}\n"
        f"Товар: {product_name}\n"
        f"Цена: {int(price_uah)} грн\n\n"
        f"Ожидайте сообщение от владельца.\n"
        f"Если не ответят в течение 6 часов — напишите в поддержку {SUPPORT}.",
        reply_markup=kb_main()
    )

    # Сообщение админу
    try:
        await bot.send_message(
            ADMIN_ID,
            f"✅ Клиент отправил на проверку оплату\n"
            f"Заказ: #{order_id}\n"
            f"Товар: {product_name}\n"
            f"Цена: {int(price_uah)} грн\n"
            f"Пользователь: @{username} (id {user_id})\n\n"
            f"Попроси у клиента скрин оплаты. Контакт поддержки: {SUPPORT}"
        )
    except Exception as e:
        print(f"ADMIN NOTIFY ERROR: {repr(e)}")


async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
