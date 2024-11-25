import os
import sqlite3
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()
API_KEY = os.getenv("API_KEY")

def get_channel_videos(channel_id, num_videos):
    youtube = build('youtube', 'v3', developerKey=API_KEY)
    print(f"Created youtube client: {youtube}")
    channel_response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    print(f"Response: {channel_response}")

    uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    print(f"Upolads Playlist ID: {uploads_playlist_id}")

    print("Getting videos from uploads playlist...")
    videos = []
    next_page_token = None
    while True:
        playlist_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in playlist_response['items']:
            video_id = item['snippet']['resourceId']['videoId']
            video_title = item['snippet']['title']
            video = {'id': video_id, 'title': video_title}
            print(f"Video found: {video}")
            videos.append(video)

        next_page_token = playlist_response.get('nextPageToken')
        if not next_page_token:
            break

    print("Fetching view counts for each video...")
    for video in videos:
        stats_response = youtube.videos().list(
            part="statistics",
            id=video['id']
        ).execute()
        video['views'] = int(stats_response['items'][0]['statistics']['viewCount'])
        print(f"Video {video['id']} has {video['views']} views.")

    sorted_videos = sorted(videos, key=lambda x: x['views'])
    return sorted_videos[:num_videos]


videos = get_channel_videos("UCPqsUjggkyJdIcvzEYL-s2A", 10)

print(f"Videos:\n{videos}")


class Video:
    def __init__(self, video_id: str, title: str, view_count: int):
        self._id = video_id
        self._title = title
        self._view_count = view_count

    @property
    def id(self):
        return self._id
    
    @property
    def title(self):
        return self._title
    @title.setter
    def title(self, value):
        self._title = value

    @property
    def view_count(self):
        return self._view_count
    @view_count.setter
    def view_count(self, value):
        self._view_count = value


class Channel:
    def __init__(self, channel_id: str, name: str):
        self._id = channel_id
        self._name = name
        self._videos = []

    @property
    def id(self):
        return self._id
    
    @property
    def name(self):
        return self._name
    
    @property
    def videos(self):
        return self._videos
    
    def add_video(self, video: Video):
        self._videos.append(video)

    # def update(self):
    #     # this will request info
    #     # make new videos if required
    #     # otherwise update
    #     pass


class Database:
    def __init__(self, db_name="youtube.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execure("""
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY
                name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY
                title TEXT,
                view_count INTEGER,
                channel_id TEXT,
                FOREIGN KEY (channel_id) REFERENCES channels(id)
            )
        """)
        self.conn.commit()

    def add_channel(self, channel):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO channels (id, name)
            VALUES (?, ?)
        """, (channel.id, channel.name))
        self.conn.commit()

    def add_video(self, video, channel_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO videos (id, title, view_count, channel_id)
            VALUES (?, ?, ?, ?)
        """, (video.id, video.title, video.view_count, channel_id))
        self.conn.commit()

    def get_videos_by_channel(self, channel_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, title, view_count FROM videos
            WHERE channel_id = ?
        """, (channel_id,))
        rows = cursor.fetchall()
        return [Video(row[0], row[1], row[2]) for row in rows]
    