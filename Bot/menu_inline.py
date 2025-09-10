# АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: InlineKeyboardMarkup
# Используется как fallback, если ReplyKeyboardMarkup не работает

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Inline-меню как альтернатива ReplyKeyboardMarkup
INLINE_MAIN_MENU = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🪙 ТОП-майнеры", callback_data="menu_top"),
        InlineKeyboardButton(text="📈 Аналитика", callback_data="menu_analytics")
    ],
    [
        InlineKeyboardButton(text="💸 Профит в рублях", callback_data="menu_rub"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu_settings")
    ],
    [
        InlineKeyboardButton(text="🛠️ Гайд", callback_data="menu_guide"),
        InlineKeyboardButton(text="ℹ️ О боте", callback_data="menu_about")
    ],
    [
        InlineKeyboardButton(text="🤝 Партнёрка", callback_data="menu_partner"),
        InlineKeyboardButton(text="❓ FAQ", callback_data="menu_faq")
    ]
])

# Хендлеры для inline-кнопок
"""
@dp.callback_query(F.data == "menu_top")
async def inline_menu_top(callback):
    await callback.message.edit_text(
        "Переходим к ТОП-майнерам...",
        reply_markup=INLINE_MAIN_MENU
    )
    await menu_top_miners(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_analytics") 
async def inline_menu_analytics(callback):
    await menu_analytics(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_rub")
async def inline_menu_rub(callback):
    await menu_profit_rub(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_settings")
async def inline_menu_settings(callback):
    await menu_settings(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_guide")
async def inline_menu_guide(callback):
    await menu_guide(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_about")
async def inline_menu_about(callback):
    await menu_about(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_partner")
async def inline_menu_partner(callback):
    await menu_partner(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "menu_faq")
async def inline_menu_faq(callback):
    await menu_faq(callback.message)
    await callback.answer()
""" 