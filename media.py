import os
import sys
import imageio
import ffmpeg

# Function to delete files and directories
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
    # Getting original image
    image = context.bot.get_file(file_id = update.message.reply_to_message.photo[-1])
    image.download(f"toDistort{user_id}.jpg")
    update.message.reply_text("yOuR pHoTO iS bEinG dIsTorRTeD")
    return image

# Function to download the audio from the user's reply
def downloadAudio(update, context, audio, user_id):
    if not update.message.reply_to_message.voice:
        update.message.reply_text("tHiS Is nOT aN AUdIo")
        return
    # Getting the original audio
    audio  = context.bot.getFile(update.message.reply_to_message.voice)
    ogg = f"audio{user_id}.ogg"
    wav = f"audio{user_id}.wav"
    audio.download(ogg)
    stream = ffmpeg.input(ogg)
    stream = ffmpeg.output(stream, wav)
    stream = ffmpeg.overwrite_output(stream)
    return stream


# Distort function using imagemmagick
def distort(imageIn, imageOut, dims, pct, directory, user_id):
    # Using ImageMagick to create frames of the distorted image
    if imageOut in os.listdir(directory): return
    print(f"{pct}%: {imageIn} -> {imageOut}")
    os.system(f"convert toDistort{user_id}.jpg -liquid-rescale {pct}x{pct}%! -resize {dims[1]}x{dims[0]}! {imageOut}")

# Vibrato function using ffmpeg
def vibrato(audioIn, audioOut, pct=12):
    print(f"{pct}%: {audioIn} -> {audioOut}")
    os.system(f"ffmpeg -i {audioIn} -filter_complex \"vibrato=f={pct}\" {audioOut}")

# BassBoost function using ffmpeg
def bassBoost(audioIn, audioOut):
    os.system(f"ffmpeg -i {audioIn} -af \"superequalizer=1b=20:2b=20:3b=20:4b=20:5b=20:6b=20:7b=20:8b=20:9b=20:10b=20:11b=20:12b=20:13b=20:14b=20:15b=20:16b=20:17b=20:18b=20,volume=10\" {audioOut}")

# Function to create a GIF with tihe distorted images
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