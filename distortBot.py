from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import logging
import os
import imageio
import sys
from multiprocessing import Pool
import subprocess
import psutil

TOKEN = ""
GET_GIF = 0

# Start command that explains the usage of the bot
def start(update, context):     

    update.message.reply_text("This is a distortion bot. Use /gif and wait for a reply.")

# Help command that explains the usage of the bot
def help(update, context):

    update.message.reply_text("Use /gif and wait for a reply. I'll create a distorted GIF of it")

# Distort function using imagemmagick
def distort(imageIn, imageOut, dims, pct, directory, user_id):

    # Using ImageMagick to create frames of the distorted image
    if imageOut in os.listdir(directory): return
    print(f"{pct}%: {imageIn} -> {imageOut}")
    os.system(f"magick toDistort{user_id}.jpg -liquid-rescale {pct}x{pct}%! -resize {dims[1]}x{dims[0]}! {imageOut}")

# mutex = Lock()

# Gif command to reply and return to GET_GIF
def gif(update, context):

    update.message.reply_text("Send me a pic :)")

    return GET_GIF

# Function to enable multithread on the distort function in order to make it faster
def enableMultithread(function, args):
    
    pool = Pool()
    pool.starmap(function, args)
    pool.close()
    pool.join()

def downloadImages(update, context, pic, user_id):
    
     # First message to the bot
    if pic:
        imageIn = update.message.photo[-1].file_id
        image = context.bot.get_file(file_id = imageIn)
        image.download(f"toDistort{user_id}.jpg")
        update.message.reply_text("We are processing your image. Wait for it!")
        return image
    # If is not the user's first message to the bot
    else: 
        update.message.reply_text("Send me a pic :)")
        if update.message.photo:
            update.message.reply_text("We are processing your image. Wait for it!")

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

def deleteDirs(directory, file1, file2, user_id):

    # Deleting the created and downloaded files
    os.system(f"rm -rf {directory}")
    os.remove(f"{file1[:-4]}{user_id}{file1[len(file1) -  4::]}")
    os.remove(f"{file2[:-4]}{user_id}{file2[len(file2) -  4::]}")

# Creating the gif
def getGif(update, context):

    user_id = update.message.from_user.id
    pic = update.message.photo

    downloadImages(update, context, pic, user_id)

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

    deleteDirs(directory, "toDistort.jpg", "distorted.mp4", user_id)

def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(ConversationHandler(
        entry_points = [CommandHandler("gif", gif)],
        states = {
            GET_GIF: [MessageHandler(Filters.all, getGif)]
        },
        fallbacks = []
    ))

    updater.start_polling()
    logging.info("=== Bot running! ===")
    updater.idle()
    logging.info("=== Bot shutting down! ===")

if __name__ == "__main__":
    main()