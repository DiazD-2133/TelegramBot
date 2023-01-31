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

# global variable to store context
davinci_context = ""


# function to generate response from the OpenAI API
def generate_response(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    response = completions.choices[0].text
    return response


# async function to handle /start command and send a greeting message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hola! soy Davinci un bot creado por "
                                                                          "@ Deiker_DiazP, en que puedo ayudarte?")


# async function to handle /restart command and reset the context
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global davinci_context
    davinci_context = ""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Iniciado Nuevo contexto")


# async function to handle incoming messages and send response
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global davinci_context
    time = datetime.datetime.now()

    print(update.message.text)

    # add user's message to the context
    davinci_context += "Yo: " + update.message.text + " "

    # write user's message to file
    with open("user.txt", mode="a", encoding='utf-8') as user_infor:
        user_infor.writelines(f"{time.strftime('%x %X')} Yo: {update.message.text}\n")

    # generate response from OpenAI API
    bot_resp = generate_response(davinci_context)

    # write bot's response to file
    with open("user.txt", mode="a", encoding='utf-8') as user_infor:
        user_infor.writelines(f"{time.strftime('%x %X')} text-davinci-003: {bot_resp}\n")

    # add bot's response to the context
    davinci_context += "text-davinci-003: " + bot_resp + " "

    # clean up bot's response
    bot_resp = bot_resp.replace("text-davinci-003:", "")
    bot_resp = bot_resp.replace("Text-davinci-003:", "")

    # send the bot's response as a message
    await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_resp)


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
