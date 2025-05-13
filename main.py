import socket
import re
from os import path, makedirs
import asyncio
from telethon import TelegramClient
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, BarColumn, TextColumn, TimeRemainingColumn, TotalFileSizeColumn, TransferSpeedColumn, DownloadColumn


DOWNLOAD_FOLDER = "./downloads"
api_id = "7122114"
api_hash = "3ff382cb976bdf8aead9359f2c352ac1"
bot_token = "1988869232:AAEZl3nmyyz-NRRDD9mX3wpnYnM9EUBghjY"
chat_id = 2294699723
client = TelegramClient('ChannelDownloadBot_V2', api_id, api_hash)


def gather_links():
    links = []
    print("Enter Video Links: (enter 'e' to finish)")
    while True:
        url = input().strip()
        if url.lower() == 'e':
            break
        links.append(url)
    return links


def sanitize_filename(filename: str) -> str:
    filename = filename.replace("\n", " ").strip()
    return re.sub(r'[\\/*?:"<>|]', '_', filename)


def check_internet(host="8.8.8.8", port=53, timeout=3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False


async def download_file(link: str, progress: Progress):
    sp = link.split('/')
    channel = sp[3]
    message_id = int(sp[-1])
    message = await client.get_messages(channel, ids=message_id)
    safe_filename = sanitize_filename(message.text)
    video_path = path.join(DOWNLOAD_FOLDER, f"{safe_filename}.mp4")

    # Ensure download folder exists
    if not path.exists(DOWNLOAD_FOLDER):
        makedirs(DOWNLOAD_FOLDER)

    # Determine starting offset from existing file
    offset = path.getsize(video_path) if path.exists(video_path) else 0
    file_size = message.video.size or message.file.size
    task = progress.add_task(
        f"Downloading {message_id}", total=file_size, completed=offset)

    # Stream download in chunks, resuming from offset
    while offset < file_size:
        try:
            async for chunk in client.iter_download(
                message.document or message.video,
                offset=offset,
                chunk_size=1024 * 64,
                file_size=file_size
            ):
                # Write chunk
                mode = 'r+b' if path.exists(video_path) else 'wb'
                with open(video_path, mode) as f:
                    f.seek(offset)
                    f.write(chunk)
                offset += len(chunk)
                progress.update(task, completed=offset)
            break

        except (asyncio.TimeoutError, ConnectionError):
            print(
                f"\nDownload interrupted at {offset} bytes. Checking connection...")
            while not check_internet():
                print("No internet. Sleeping for 5 seconds...")
                await asyncio.sleep(5)
            print("Internet restored. Resuming...")
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def main():
    links = gather_links()
    await client.start()

    while True:
        try:
            threads = int(input("Concurrent downloads (1-4): "))
            if 1 <= threads <= 4:
                break
        except ValueError:
            pass
        print("Enter a number between 1 and 4.")

    with Progress(
        SpinnerColumn(),
        "{task.description}",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        BarColumn(bar_width=50),
        TextColumn("[bold]{task.percentage:>3.0f}%")
    ) as progress:
        semaphore = asyncio.Semaphore(threads)
        tasks = []
        for link in links:
            async def sem_task(l):
                async with semaphore:
                    await download_file(l, progress)
            tasks.append(sem_task(link))

        await asyncio.gather(*tasks)

    print("All downloads completed!")

if __name__ == "__main__":
    asyncio.run(main())
