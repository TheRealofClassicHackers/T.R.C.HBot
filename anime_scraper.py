import os
import requests
from bs4 import BeautifulSoup

DOWNLOADS_DIR = "downloads/anime"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def get_episode_links(anime_page_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(anime_page_url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    # For example, Gogoanime episode list structure
    episodes = []
    links = soup.select('div#episode_page > ul > li > a')
    for link in links:
        ep_url = link.get('href')
        ep_num = link.text.strip()
        if ep_url:
            episodes.append((ep_num, "https://gogoanime.vc" + ep_url))
    return episodes

def get_video_source(episode_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    r = requests.get(episode_url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Video iframe src example
    iframe = soup.find('iframe')
    if iframe:
        embed_url = iframe.get('src')
        return embed_url
    return None

def download_anime_episode(anime_name):
    # Search or map anime_name to anime page URL (requires implemented search)
    # Simplified: hardcoded example for Gogoanime
    anime_page = f"https://gogoanime.vc/category/{anime_name.replace(' ', '-').lower()}"
    
    episodes = get_episode_links(anime_page)
    if not episodes:
        raise Exception("No episodes found.")
    ep_num, ep_url = episodes[-1]  # Get latest episode

    video_link = get_video_source(ep_url)
    if not video_link:
        raise Exception("Video source not found.")

    # Download video or stream video
    video_name = f"{anime_name}_episode_{ep_num}.mp4"
    video_path = os.path.join(DOWNLOADS_DIR, video_name)

    # Attempt direct download, else return video link
    try:
        download_file(video_link, video_path)
        return video_path
    except Exception as e:
        # Could not download, return URL so user can open manually
        return video_link
