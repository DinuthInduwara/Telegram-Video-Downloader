from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn, TimeRemainingColumn, TotalFileSizeColumn, TransferSpeedColumn, DownloadColumn
from telethon import TelegramClient
import asyncio
from os import path

import re

DOWNLOAD_FOLDER = "./downloads"

api_id = "7122114"
api_hash = "3ff382cb976bdf8aead9359f2c352ac1"
bot_token = "1988869232:AAEZl3nmyyz-NRRDD9mX3wpnYnM9EUBghjY"

# Dummy implementations for demonstration.
# In your program, these functions will be defined with your actual logic.

chat_id = 2294699723
client = TelegramClient('ChannelDownloadBot_V2', api_id, api_hash)


def gather_links():
    links = list()
    print("Enter Video Links: \n\t\t Enter `e` to exit..! ")

    while True:
        url = input()
        if url == "e" or url == "E":
            break
        links.append(url)

    return links


def sanitize_filename(filename):
    """Sanitizes filenames by removing invalid characters and trimming spaces."""
    filename = filename.replace(
        "\n", " ").strip()  # Remove newlines and trim spaces
    return re.sub(r'[\\/*?:"<>|]', '_', filename)


async def download_file(link, progress):
    """
    Download a file from the given Telegram link with a progress bar.
    """
    sp = link.split("/")
    channel = sp[3]  # Extract channel name
    message_id = int(sp[-1])  # Extract message ID

    # Fetch the message
    message = await client.get_messages(channel, ids=message_id)

    # Create a progress bar task
    task = progress.add_task(f"Downloading {message_id}", total=100)

    # Download the media with progress tracking
    async def progress_callback(done, total):
        # Set actual total size only once
        if total and progress.tasks[task].total == 100:
            progress.update(task, total=total)
        progress.update(task, completed=done)

    safe_filename = sanitize_filename(message.text)
    video_path = path.join(DOWNLOAD_FOLDER, f"{safe_filename}.mp4")

    await client.download_media(message, file=video_path, progress_callback=progress_callback)
    progress.update(task, completed=100)


async def main():
    """
    Entry point of the program.
    Wraps the main menu function in curses.wrapper to ensure proper initialization and cleanup.
    """
    links = gather_links()  # Collect links

    await client.start()

    # Get the number of concurrent downloads
    while True:
        try:
            threds = int(
                input("How many tasks to run at the same time? (1-4): "))
            if 1 <= threds <= 4:
                break
        except ValueError:
            pass
        print("Invalid input. Please enter a number between 1 and 4.")

    # Progress Bar Setup
    with Progress(
        SpinnerColumn(),
        "{task.description}",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        BarColumn(bar_width=50),
        " ",
        TextColumn("[bold]{task.percentage:>3.0f}%", justify="right"),
        " ",
    ) as progress:
        # Create a list of tasks
        tasks = [download_file(link, progress) for link in links]

        # Run tasks with concurrency limit
        semaphore = asyncio.Semaphore(threds)

        async def limited_task(task):
            async with semaphore:
                await task

        await asyncio.gather(*(limited_task(task) for task in tasks))

    print("All downloads completed!")

if __name__ == "__main__":
    asyncio.run(main())
