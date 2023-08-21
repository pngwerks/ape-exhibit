import os
import random
import requests
import json
import shutil
import tkinter as tkint
from PIL import Image, ImageTk
from glob import glob
from time import sleep
from threading import Thread

# Configuration options
SLIDESHOW_DELAY = 8  # Default delay between image transitions in seconds
CLEANUP_THRESHOLD = 50  # Number of images to keep before cleanup
APE_RES=947
WIDTH=APE_RES
HEIGHT=APE_RES

# Directory to store images
TMP_DIR = "/tmp"

# Fetch BAYC metadata, then image and cache locally
def fetch_and_save_image(indices):

    ape_type = indices[0]
    tokenId = indices[1]

    # BAYC type, metadata from IPFS    
    if ape_type == 0:
        url = f"https://ipfs.io/ipfs/QmeSjSinHpPnmXmspMjwiXyN6zS4E9zccariGR3jxcaWtq/{tokenId}"
    # MAYC type, metadata from API
    else:
        url = f"https://boredapeyachtclub.com/api/mutants/{tokenId}"
    
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        ipfs_url = response.json().get('image')
        image_CID = ipfs_url.strip('ipfs://')
        image_response = requests.get(f"https://ipfs.io/ipfs/{image_CID}", stream=True)
        if image_response.status_code == 200:
            image_path = os.path.join(TMP_DIR, f"{ape_type}_{tokenId}.png")
            with open(image_path, "wb") as f:
                image_response.raw.decode_content = True
                shutil.copyfileobj(image_response.raw, f)
    else:
        # Mutant index did not exist!
        rerolled = get_random_ape()
        fetch_and_save_image(rerolled)

    return tokenId

# Keep cache directory from filling up
def cleanup():
    image_files = glob(os.path.join(TMP_DIR, "*.png"))
    # If over threshold, remove some each round
    if len(image_files) > CLEANUP_THRESHOLD:
        oldest_images = sorted(image_files, key=os.path.getctime)[:CLEANUP_THRESHOLD]

        for old in oldest_images[0:24]:
            os.remove(old)

def get_random_ape():
    rando = random.randint(1,10)
    if rando <= 6: # 60% chance of Bored Ape
        ape_type = 0
        rand_ape_index = random.randint(0, 9999)
    else: # 40% chance of Mutant Ape
        ape_type = 1
        rand_ape_index = random.randint(0, 30007)
    return [ape_type, rand_ape_index]

# Produce the show continuously, geenerating random indices, fetching and rolling cache directory forward.
def slideshow(canvas, label):
    while True:
        indices = get_random_ape()
        fetchedId = fetch_and_save_image(indices)

        # Get the latest image file
        image_files = glob(os.path.join(TMP_DIR, "*.png"))
        if image_files:
            latest_image_file = max(image_files, key=os.path.getctime)

        # Parse the filename for apetype before underscore
        ape_type_index = os.path.basename(latest_image_file).split("_")[0]
        match int(ape_type_index):
            case 0:
                ape_type = "Bored"
            case 1:
                ape_type = "Mutant"

        if fetchedId > 29999:
            ape_type = "Mega Mutant"

        # Prepare canvas
        img = Image.open(latest_image_file)
        img = img.resize((APE_RES, APE_RES), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        canvas.create_image(WIDTH/2, HEIGHT/2, anchor="center", image=img)
        canvas.create_text(15,20,text=f"{ape_type} Ape #{fetchedId}", font="Helvetica 26",anchor=tkint.NW)

        canvas.update()

        # Run cleanup
        cleanup()

        sleep(SLIDESHOW_DELAY)

def main():
    root = tkint.Tk()
    root.title("Ape Exhibit")
    root.option_add('*tearoff', False)

    # Menu bar with Settings top-level
    menubar = tkint.Menu(root)
    settings_menu = tkint.Menu(menubar, tearoff=False)
    menubar.add_cascade(label="Settings", menu=settings_menu)

    root.config(menu=menubar)

    # Options Menu
    options_menu = tkint.Menu(settings_menu, tearoff=False)
    settings_menu.add_cascade(label="Set Delay", menu=options_menu)

    delay_options = [5, 8, 10, 15]
    delay_current = tkint.IntVar()
    delay_current.set(SLIDESHOW_DELAY) # Default from global

    # Create command for each delay option value
    for d in delay_options:
        options_menu.add_command(label=str(d), command=delay_chosen(d))

    canvas = tkint.Canvas(
        root,
        height=HEIGHT,
        width=WIDTH,
        bd=0,
        highlightthickness=0,
        relief='ridge'
    )
    canvas.pack()

    root.resizable(width=True, height=True)
    root.geometry(f"{WIDTH}x{HEIGHT}")

    label = tkint.Label(root)
    label.pack()

    # Start the slideshow in a separate thread
    slideshow_thread = Thread(target=slideshow, args=[canvas, label])
    slideshow_thread.daemon = True
    slideshow_thread.start()

    # Run the main event loop
    root.mainloop()

def delay_chosen(delay):
    return lambda: set_delay(delay)

def set_delay(delay):
    globals().update({'SLIDESHOW_DELAY': delay})
    print("Delay changed %d", delay)


if __name__ == '__main__':
    main()