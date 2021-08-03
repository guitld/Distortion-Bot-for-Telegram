from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging
import os
import imageio
from multiprocessing import Pool
import subprocess
import ffmpeg
import media as md

TOKEN = ""

# Function to enable multithread on the distort function in order to make it faster
def enableMultithread(function, args):
    pool = Pool()
    pool.starmap(function, args)
    pool.close()
    pool.join()

# Start command that explains the usage of the bot
def start(update, context):     
    update.message.reply_text("This is a distortion bot. Use /help to see all the commands")

# Help command that explains the usage of the bot
def help(update, context):
    update.message.reply_text("/gif - Reply with a picture and I'll create a distorted gif on it\n/vibrato - Reply an audio and I'll add vibrato to it\n/bass - Reply an audio and I'll bass boost it")

# Creating the gif
def getGif(update, context):
    # Receiving the original image
    user_id = update.message.from_user.id
    pic = update.message.photo
    md.downloadImage(update, context, pic, user_id)

    # Getting the image dimmensions and setting up a list for the 60 arguments of distort function
    dims = imageio.imread(open(f"toDistort{user_id}.jpg", "rb")).shape
    args = []

    # Setting a directory for the frames
    directory = f"{user_id}"
    os.mkdir(directory)

    # Appending arguments to a list
    for pct in range(40, 100+1):
        photo = f"toDistort{user_id}.jpg"
        imageOut = os.path.join(directory, f"out{pct:03d}.jpg")
        args.append((photo, imageOut, dims, pct, directory, user_id))

    # Using the multithreaded distort and creating MP4
    enableMultithread(md.distort, args)
    video = md.createMP4(update, context, directory, user_id)
    context.bot.sendAnimation(animation = video, chat_id = update.message.chat_id)
    video.close()
    md.deleteDirs(directory, "toDistort.jpg", "distorted.mp4", None, user_id)

# Function to add vibrato effect to audio
def vibratoAudio(update, context):
    # Receiving the audio
    user_id = update.message.from_user.id
    audio = update.message.audio
    audioIn = md.downloadAudio(update, context, audio, user_id)
    ffmpeg.run(audioIn)

    # Adding the effect
    audioOut = f"audioDistorted{user_id}.wav"
    md.vibrato(f"audio{user_id}.wav", audioOut)
    voiceToSend = open(audioOut, "rb")

    # Sending the distorted audio
    context.bot.sendVoice(voice = voiceToSend, chat_id = update.message.chat_id)
    voiceToSend.close()
    md.deleteDirs(None, "audio.wav", "audioDistorted.wav", "audio.ogg", user_id)

# Function to add bass boost effect to audio
def bassBoostAudio(update, context):
    # Receiving the audio
    user_id = update.message.from_user.id
    audio = update.message.audio
    audioIn = md.downloadAudio(update, context, audio, user_id)
    ffmpeg.run(audioIn)

    # Adding the effect
    audioOut = f"audioDistorted{user_id}.wav"
    md.bassBoost(f"audio{user_id}.wav", audioOut)
    voiceToSend = open(audioOut, "rb")

    # Sending the distorted audio
    context.bot.sendVoice(voice = voiceToSend, chat_id = update.message.chat_id)
    voiceToSend.close()
    md.deleteDirs(None, "audio.wav", "audioDistorted.wav", "audio.ogg", user_id)

def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("vibrato", vibratoAudio))
    dp.add_handler(CommandHandler("gif", getGif))
    dp.add_handler(CommandHandler("bass", bassBoostAudio))


    updater.start_polling()
    logging.info("=== Bot running! ===")
    updater.idle()
    logging.info("=== Bot shutting down! ===")

if __name__ == "__main__":
    main()