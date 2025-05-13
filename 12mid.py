import asyncio
import datetime
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn, TimeRemainingColumn, DownloadColumn, TransferSpeedColumn
from telethon import TelegramClient
from os import path
import re

DOWNLOAD_FOLDER = "./downloads"
api_id = "7122114"
api_hash = "3ff382cb976bdf8aead9359f2c352ac1"
bot_token = "1988869232:AAEZl3nmyyz-NRRDD9mX3wpnYnM9EUBghjY"
chat_id = 2294699723
client = TelegramClient('ChannelDownloadBot_V2', api_id, api_hash)

def gather_links():
    links = []
    print("Enter Video Links: \n\t\t Enter `e` to exit..! ")
    while True:
        url = input()
        if url.lower() == "e":
            break
        links.append(url)
    return links

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename.replace("\n", " ").strip())

async def download_file(link, progress):
    sp = link.split("/")
    channel = sp[3]
    message_id = int(sp[-1])
    message = await client.get_messages(channel, ids=message_id)
    task = progress.add_task(f"Downloading {message_id}", total=100)

    async def progress_callback(done, total):
        if total and progress.tasks[task].total == 100:
            progress.update(task, total=total)
        progress.update(task, completed=done)
    
    safe_filename = sanitize_filename(message.text)
    video_path = path.join(DOWNLOAD_FOLDER, f"{safe_filename}.mp4")
    await client.download_media(message, file=video_path, progress_callback=progress_callback)
    progress.update(task, completed=100)

async def main():
    links = gather_links()
    await client.start()
    
    while True:
        choice = input("Start download now (N) or at midnight (12)? ").strip()
        if choice == "12":
            now = datetime.datetime.now()
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            delay = (midnight - now).total_seconds()
            print(f"Waiting until midnight to start downloads ({int(delay)} seconds left)...")
            while (midnight - datetime.datetime.now()).total_seconds() > 0:
                await asyncio.sleep(1)
            break
        elif choice.lower() == "n":
            break
        print("Invalid input. Please enter 'N' to start now or '12' for midnight.")
    
    while True:
        try:
            threads = int(input("How many tasks to run at the same time? (1-4): "))
            if 1 <= threads <= 4:
                break
        except ValueError:
            pass
        print("Invalid input. Please enter a number between 1 and 4.")
    
    with Progress(
        SpinnerColumn(), "{task.description}", TimeElapsedColumn(), TimeRemainingColumn(),
        DownloadColumn(), TransferSpeedColumn(), BarColumn(bar_width=50),
        " ", TextColumn("[bold]{task.percentage:>3.0f}%", justify="right"), " ",
    ) as progress:
        semaphore = asyncio.Semaphore(threads)
        async def limited_task(task):
            async with semaphore:
                await task
        await asyncio.gather(*(limited_task(download_file(link, progress)) for link in links))
    print("All downloads completed!")

if __name__ == "__main__":
    asyncio.run(main())
