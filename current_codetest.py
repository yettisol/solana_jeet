import os 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = "TELEGRAM_TOKEN"

# Example API endpoints
RAYDIUM_API = "https://api.raydium.io/v2/pools"
METEORA_API = "https://api.meteora.ag/pools" # Example API endpoint

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Volume Booster 📈", callback_data="volume_booster")],
        [InlineKeyboardButton("Wallets 💰", callback_data="wallets")],
        [InlineKeyboardButton("Support 💬", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select one of these Commands:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "volume_booster":
        # Create 5 boost buttons + back button
        keyboard = [
            [InlineKeyboardButton("Raydium 💫", callback_data="raydium")],
            [InlineKeyboardButton("Meteora ☄️", callback_data="meteora")],
            [InlineKeyboardButton("PumpFun 💊", callback_data="pumpfun")],
            [InlineKeyboardButton("Moonshot 🌚", callback_data="moonshot")],
            [InlineKeyboardButton("Support 💬", callback_data="support")],
            [InlineKeyboardButton("🔙 Go Back", callback_data="main")]
        ]
        await query.edit_message_text(
            text="Select Your Liquidity Pool Provider:",
            reply_markup=InlineKeyboardMarkup(keyboard)
)      
         
    elif data == "main":
        # Return to main menu
        keyboard = [
            [InlineKeyboardButton("Volume Booster", callback_data="volume_booster")],
            [InlineKeyboardButton("Wallets", callback_data="wallets")],
            [InlineKeyboardButton("Support", callback_data="support")]
        ]
        await query.edit_message_text(
            text="Main Menu:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    # Add handling for other buttons (to be implemented)
    elif data in ["wallets", "support"]:
        await query.edit_message_text("ℹ️ This feature is under construction!")
    
    elif data.startswith("boost"):
        boost_level = data[5:]  # Extract the number from boostX
        await query.edit_message_text(f"✅ Volume boosted by {boost_level}0%!")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()

if os.name == "main":
    main()
