import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from solana.rpc.api import Client
from solders.signature import Signature

TELEGRAM_TOKEN = "7570294416:AAHK0Utk--AEfXYyP1NLaxYeIJV6Gagd3Ps"
PAYMENT_ADDRESS = "8ecQdrWxKxnh1UzwRk1sFaWv7q8CeMJfWh1M732iZtba"
SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"

# Solana RPC endpoint (public, replace with private for production)
RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
solana_client = Client(RPC_ENDPOINT)

# Example API endpoints (placeholders for now)
RAYDIUM_API = "https://api.raydium.io/v2/pools"
METEORA_API = "https://api.meteora.ag/pools"
PUMPFUN_API = "https://api.pump.fun/pools"
MOONSHOT_API = "https://api.moonshot.io/pools"

# Bot states
BOOST_VOLUME_STATE = 'BOOST_VOLUME'
TOKEN_ADDRESS_STATE = 'TOKEN_ADDRESS'
PAYMENT_STATE = 'PAYMENT'
WALLET_MANAGEMENT_STATE = 'WALLET_MANAGEMENT'

# User data storage (in-memory for this example)
user_data = {}

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
    user_id = query.from_user.id
    
    if data == "volume_booster":
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
        user_data[user_id] = {'state': BOOST_VOLUME_STATE}
        
    elif data == "main":
        keyboard = [
            [InlineKeyboardButton("Volume Booster 📈", callback_data="volume_booster")],
            [InlineKeyboardButton("Wallets 💰", callback_data="wallets")],
            [InlineKeyboardButton("Support 💬", callback_data="support")]
        ]
        await query.edit_message_text(
            text="Select one of these Commands:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        if user_id in user_data:
            del user_data[user_id]
            
    elif data in ["wallets", "support"]:
        await query.edit_message_text("ℹ️ This feature is under construction!")
        
    elif data in ["raydium", "meteora", "pumpfun", "moonshot"]:
        user_data[user_id] = {
            'state': TOKEN_ADDRESS_STATE,
            'provider': data
        }
        await query.edit_message_text(
            text=f"Selected: {data.capitalize()} as Liquidity Pool Provider.\n"
                 "Please paste your Project Token Address:"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle text input from user
    """
    user_id = update.message.from_user.id
    text = update.message.text
    
    if user_id in user_data and user_data[user_id].get('state') == TOKEN_ADDRESS_STATE:
        if len(text) == 44 and text.isalnum():
            user_data[user_id]['token_address'] = text
            provider = user_data[user_id]['provider']
            
            keyboard = [
                [InlineKeyboardButton("Proceed to Payment 💸", callback_data="payment")],
                [InlineKeyboardButton("Wallet Options 💰", callback_data="wallets_menu")],
                [InlineKeyboardButton("🔙 Go Back", callback_data="volume_booster")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"Token address {text} set for {provider.capitalize()}.\nWhat's next?",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Invalid token address! Please provide a valid Solana token address (44 characters)."
            )
            
    elif user_id in user_data and user_data[user_id].get('state') == PAYMENT_STATE:
        # Handle transaction hash
        tx_signature = text
        await verify_payment(update, context, user_id, tx_signature)

async def payment_or_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle payment or wallet options after token address input
    """
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "payment":
        if user_id in user_data and 'token_address' in user_data[user_id]:
            provider = user_data[user_id]['provider']
            token_address = user_data[user_id]['token_address']
            user_data[user_id]['state'] = PAYMENT_STATE
            await query.edit_message_text(
                text=f"Payment for {provider.capitalize()} Volume Boost\n"
                     f"Token: {token_address}\n"
                     f"Please send 0.010 SOL to: {PAYMENT_ADDRESS}\n"
                     "Reply with the transaction signature after payment."
            )
        else:
            await query.edit_message_text("Error: No token address set!")
            
    elif data == "wallets_menu":
        await query.edit_message_text("ℹ️ Wallet options are under construction!")

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, tx_signature: str):
    """
    Verify the payment transaction and proceed to wallet management
    """
    try:
        # Wait for transaction propagation
        await asyncio.sleep(5)
        
        # Fetch transaction with base58 encoding for reliability
        tx_info = solana_client.get_transaction(Signature.from_string(tx_signature), encoding="base58")
        if not tx_info.value:
            await update.message.reply_text("❌ Transaction not found. It may still be processing. Please try again in a few seconds.")
            return
        
        if tx_info.value.transaction.meta.err:
            await update.message.reply_text("❌ Transaction failed according to the blockchain.")
            return
        
        # Extract transaction details
        tx = tx_info.value.transaction.transaction
        message = tx.message
        account_keys = [str(key) for key in message.account_keys]
        
        payment_valid = False
        amount_sent = 0
        
        # Check instructions for System Program transfer
        SYSTEM_PROGRAM_ID = "11111111111111111111111111111111"
        for instruction in message.instructions:
            program_id_index = instruction.program_id_index
            program_id = account_keys[program_id_index]
            
            if program_id == SYSTEM_PROGRAM_ID:
                if len(instruction.accounts) >= 2:
                    dest_index = instruction.accounts[1]  # Destination account
                    dest_pubkey = account_keys[dest_index]
                    
                    if dest_pubkey == PAYMENT_ADDRESS:
                        # Parse transfer instruction data (System Program transfer: 4 bytes instruction type, 8 bytes lamports)
                        if len(instruction.data) >= 12 and instruction.data[0:4] == bytes([2, 0, 0, 0]):  # Transfer instruction ID
                            lamports = int.from_bytes(instruction.data[4:12], byteorder='little')
                            amount_sent = lamports / 1_000_000_000  # Convert to SOL
                            if amount_sent >= 0.010:
                                payment_valid = True
                                break
        
        if payment_valid:
            user_data[user_id]['state'] = WALLET_MANAGEMENT_STATE
            user_data[user_id]['payment_amount'] = amount_sent
            await update.message.reply_text(
                f"✅ Payment verified! Received {amount_sent:.3f} SOL.\n"
                "Next step: Wallet management for volume boosting.\n"
                "Please wait while we prepare your boosting setup..."
            )
            await manage_wallets(update, context, user_id)
        else:
            # Detailed feedback
            if PAYMENT_ADDRESS in account_keys:
                pre_balances = tx_info.value.transaction.meta.pre_balances
                post_balances = tx_info.value.transaction.meta.post_balances
                payment_index = account_keys.index(PAYMENT_ADDRESS)
                amount_received = (post_balances[payment_index] - pre_balances[payment_index]) / 1_000_000_000
                await update.message.reply_text(
                    f"❌ Payment verification failed!\n"
                    f"Detected amount to {PAYMENT_ADDRESS}: {amount_received:.3f} SOL\n"
                    "Ensure you sent at least 0.010 SOL directly to the correct address."
                )
            else:
                await update.message.reply_text(
                    f"❌ Payment verification failed!\n"
                    f"No transfer to {PAYMENT_ADDRESS} found in this transaction."
                )
    except ValueError as ve:
        await update.message.reply_text(f"❌ Invalid transaction signature format: {str(ve)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error verifying transaction: {str(e)}")

async def manage_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    Placeholder for wallet management after payment verification
    """
    provider = user_data[user_id]['provider']
    token_address = user_data[user_id]['token_address']
    payment_amount = user_data[user_id]['payment_amount']
    
    await update.message.reply_text(
        f"Wallet Management for {provider.capitalize()} Volume Boost\n"
        f"Token: {token_address}\n"
        f"Payment: {payment_amount:.3f} SOL\n"
        "ℹ️ Wallet generation/import and volume boosting logic to be implemented here."
    )

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click, pattern="^(volume_booster|main|wallets|support|raydium|meteora|pumpfun|moonshot)$"))
    application.add_handler(CallbackQueryHandler(payment_or_wallets, pattern="^(payment|wallets_menu)$"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    application.run_polling()

if __name__ == "__main__":
    main()
