# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 18:33:13 2024

@author: Taufik Sutanto
"""
from googleapiclient.discovery import build
import pandas as pd
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from tqdm import tqdm

# Replace this with your API key
API_KEY = "AIzaSyDuWvLWU_WS"
# Replace with the channel handle or identifier (e.g., '@cbarchiveid')
channel_identifier = "@cbarchiveid"

# Function to get channel ID using handle or username
def get_channel_id(channel_identifier):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    response = youtube.search().list(
        part="snippet",
        q=channel_identifier,
        type="channel",
        maxResults=1
    ).execute()

    if not response["items"]:
        print(f"Channel identifier '{channel_identifier}' not found.")
        return None

    return response["items"][0]["id"]["channelId"]

# Function to get channel uploads playlist ID
def get_uploads_playlist_id(channel_id):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    if not response["items"]:
        print(f"Channel ID '{channel_id}' not found.")
        return None

    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

# Function to retrieve all videos in a playlist
def get_videos_from_playlist(playlist_id):
    youtube = build("youtube", "v3", developerKey=API_KEY)
    videos = []
    next_page_token = None
    iteration_ = 0
    while True:
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()
        
        print("\n Iteration ~ {} \n".format(iteration_), flush=True)
        iteration_ += 1
        for item in tqdm(response["items"]):
            video_id = item["snippet"]["resourceId"]["videoId"]
            title = item["snippet"]["title"]
            description = item["snippet"].get("description", "")
            published_at = item["snippet"].get("publishedAt", "")

            # Fetch additional video details
            video_response = youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            view_count = video_response["items"][0]["statistics"].get("viewCount", "0")

            # Fetch video transcription
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([entry['text'] for entry in transcript])
            except (TranscriptsDisabled, NoTranscriptFound):
                transcript_text = "Transcript not available"

            videos.append({
                "Published At": published_at,
                "Video URL": video_url,
                "Title": title,
                "Description": description,
                "View Count": view_count,
                "Video ID": video_id,
                "Transcript": transcript_text
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos

if __name__ == "__main__":

    # Get channel ID from handle or username
    channel_id = get_channel_id(channel_identifier)

    if channel_id:
        uploads_playlist_id = get_uploads_playlist_id(channel_id)

        if uploads_playlist_id:
            videos = get_videos_from_playlist(uploads_playlist_id)

            print("\nSaving the data to CSV ... ", flush=True)
            # Convert to a pandas DataFrame
            df = pd.DataFrame(videos)

            # Save to a CSV file
            output_file = "channel_videos.csv"
            df.to_csv(output_file, index=False, encoding="utf-8-sig")

            print(f"Data saved to {output_file}")
            print(df.head())
        else:
            print("Could not retrieve uploads playlist ID for the channel.")
    else:
        print("Could not retrieve channel ID for the identifier.")
