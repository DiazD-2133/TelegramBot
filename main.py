import os
import logging
import openai
from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes
import datetime

# set up basic logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# dictionary to store user context
telegram_users = {}
# dictionary to store user role and message
user_management = {"role": "user", "content": ""}
# dictionary to store assistant role and message
messages = [{"role": "system", "content": "You are a helpful assistant."}]
# dictionary to store assistant role and message
assistant_management = {"role": "assistant", "content": ""}


# function to generate response from the OpenAI API
def generate_response(prompt):
    # set up OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # generate response from OpenAI API
    completions = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.8,
    )

    response = completions.choices[0]["message"]
    return response


# async function to handle /start command and send a greeting message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global telegram_users, user_management, messages
    # set initial context for user
    telegram_users[update.message.chat_id] = [messages, user_management]
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hola! soy Davinci un bot creado por "
                                                                          "@Deiker_DiazP, en que puedo ayudarte?")


# async function to handle /restart command and reset the context
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global messages

    # reset context for user
    telegram_users[update.message.chat_id][0] = [{"role": "system", "content": "You are a helpful assistant."}]
    # reset user's message
    telegram_users[update.message.chat_id][1]["content"] = ""

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Iniciado nuevo contexto")


# async function to handle incoming messages and send response
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global telegram_users, messages, user_management, assistant_management
    time = datetime.datetime.now()

    print(f"{time.strftime('%x %X')} [{update.message.chat_id}]: {update.message.text}")

    try:
        # store user's message in context
        telegram_users[update.message.chat_id][1]["content"] = update.message.text
    except KeyError:
        # set initial context for user if not found
        telegram_users[update.message.chat_id] = [messages, user_management]
        telegram_users[update.message.chat_id][1]["content"] = update.message.text

    # append user's message to context
    telegram_users[update.message.chat_id][0].append(telegram_users[update.message.chat_id][1])

    # write user's message to file
    with open("user.txt", mode="a", encoding='utf-8') as user_infor:
        user_infor.writelines(f"{update.message.chat_id}: {update.message.text}\n")

    # generate response from OpenAI API
    bot_resp = generate_response(telegram_users[update.message.chat_id][0])

    # write bot's response to file
    with open("user.txt", mode="a", encoding='utf-8') as user_infor:
        user_infor.writelines(f"text-davinci-003: {bot_resp['content']}\n")

    assistant_management["content"] = bot_resp['content']
    # append response to context
    telegram_users[update.message.chat_id][0].append(assistant_management)
    print(telegram_users[update.message.chat_id][0])

    # reset user's input after generating a response
    telegram_users[update.message.chat_id][1]["content"] = ""

    # send the bot's response as a message
    await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_resp["content"])


# main function
if __name__ == '__main__':
    # create a new application using the Bot API key
    application = ApplicationBuilder().token(os.getenv("BOT_API_KEY")).build()

    # create a handler for the start command
    start_handler = CommandHandler('start', start)

    # create a handler for the restart command
    restart_handler = CommandHandler('reset', restart)

    # create a handler for incoming text messages
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)

    # add the handlers to the application
    application.add_handler(start_handler)
    application.add_handler(restart_handler)
    application.add_handler(echo_handler)

    # run the bot in polling mode
    application.run_polling()
