from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging
import os
import imageio
import sys
from multiprocessing import Pool
import subprocess
import psutil
import ffmpeg

TOKEN = ""

# Start command that explains the usage of the bot
def start(update, context):     

    update.message.reply_text("This is a distortion bot. Use /help to see all the commands")

# Help command that explains the usage of the bot
def help(update, context):

    update.message.reply_text("/gif - Reply with a picture and I'll create a distorted gif on it\n/audio - Reply an audio and I'll distort it")

# Distort function using imagemmagick
def distort(imageIn, imageOut, dims, pct, directory, user_id):

    # Using ImageMagick to create frames of the distorted image
    if imageOut in os.listdir(directory): return
    print(f"{pct}%: {imageIn} -> {imageOut}")
    os.system(f"convert toDistort{user_id}.jpg -liquid-rescale {pct}x{pct}%! -resize {dims[1]}x{dims[0]}! {imageOut}")

def vibrato(audioIn, audioOut, pct=12):
    print(f"{pct}%: {audioIn} -> {audioOut}")
    os.system(f"ffmpeg -i {audioIn} -filter_complex \"vibrato=f={pct}\" {audioOut}")

# Function to enable multithread on the distort function in order to make it faster
def enableMultithread(function, args):
    
    pool = Pool()
    pool.starmap(function, args)
    pool.close()
    pool.join()

def deleteDirs(directory, file1, file2, file3, user_id):

    # Deleting the created and downloaded files
    if directory:
        os.system(f"rm -rf {directory}")
    os.remove(f"{file1[:-4]}{user_id}{file1[len(file1) -  4::]}")
    os.remove(f"{file2[:-4]}{user_id}{file2[len(file2) -  4::]}")
    if file3:
        os.remove(f"{file3[:-4]}{user_id}{file3[len(file3) -  4::]}")

# Function to download the image from the user's replay
def downloadImage(update, context, pic, user_id):
    
     # First message to the bot
    if not update.message.reply_to_message.photo:
        update.message.reply_text("tHiS Is nOT aN iMAgE")
        return
    image = context.bot.get_file(file_id = update.message.reply_to_message.photo[-1])
    image.download(f"toDistort{user_id}.jpg")
    update.message.reply_text("yOuR pHoTO iS bEinG dIsTorRTeD")
    return image

def createMP4(update, context, directory, user_id):
    
    # Creating a MP4 file for the animation
    writer = imageio.get_writer(f"distorted{user_id}.mp4", fps=20)
    files = sorted(os.listdir(directory))

    # Appending the images similar to a senoid function, going up and down
    for file_name in files[::-1] + files:
        file_path = os.path.join(directory, file_name)
        writer.append_data(imageio.imread(file_path))
    
    writer.close()
    video = open(f"distorted{user_id}.mp4", "rb")
    return video


# Creating the gif
def getGif(update, context):

    user_id = update.message.from_user.id
    pic = update.message.photo
    downloadImage(update, context, pic, user_id)

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

    # Using the multithreaded distort
    enableMultithread(distort, args)

    video = createMP4(update, context, directory, user_id)

    context.bot.sendAnimation(animation = video, chat_id = update.message.chat_id)
    video.close()

    deleteDirs(directory, "toDistort.jpg", "distorted.mp4", None, user_id)


# Function to download the audio from the user's reply
def downloadAudio(update, context, audio, user_id):

    if not update.message.reply_to_message.voice:
        update.message.reply_text("tHiS Is nOT aN AUdIo")
        return

    audio  = context.bot.getFile(update.message.reply_to_message.voice)
    ogg = f"audio{user_id}.ogg"
    wav = f"audio{user_id}.wav"
    audio.download(ogg)

    stream = ffmpeg.input(ogg)
    stream = ffmpeg.output(stream, wav)
    stream = ffmpeg.overwrite_output(stream)
    return stream

def audio(update, context):

    user_id = update.message.from_user.id
    audio = update.message.audio
    audioIn = downloadAudio(update, context, audio, user_id)
    ffmpeg.run(audioIn)
    audioOut = f"audioDistorted{user_id}.wav"
    vibrato(f"audio{user_id}.wav", audioOut)
    voiceToSend = open(audioOut, "rb")
    context.bot.sendVoice(voice = voiceToSend, chat_id = update.message.chat_id)
    voiceToSend.close()

    deleteDirs(None, "audio.wav", "audioDistorted.wav", "audio.ogg", user_id)


def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("audio", audio))
    dp.add_handler(CommandHandler("gif", getGif))


    updater.start_polling()
    logging.info("=== Bot running! ===")
    updater.idle()
    logging.info("=== Bot shutting down! ===")

if __name__ == "__main__":
    main()
