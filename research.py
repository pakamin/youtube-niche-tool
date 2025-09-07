import os
import googleapiclient.discovery
import pandas as pd

# Replace with your YouTube Data API Key
API_KEY = "AIzaSyCLEvbICsSMhEdBGHYqF9KaPpLrJrFVjsw"

# Initialize API
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

def search_youtube(keyword, max_results=20):
    request = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        maxResults=max_results
    )
    return request.execute()

def get_video_stats(video_ids):
    request = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids)
    )
    return request.execute()

def get_channel_stats(channel_ids):
    request = youtube.channels().list(
        part="statistics",
        id=",".join(channel_ids)
    )
    return request.execute()

def niche_research(keywords, max_results=20, max_subs=1000, min_views=10000):
    all_results = []

    for keyword in keywords:
        print(f"\n🔍 Searching for: {keyword}")
        search_response = search_youtube(keyword, max_results=max_results)

        video_ids = [item["id"]["videoId"] for item in search_response["items"]]
        channel_ids = [item["snippet"]["channelId"] for item in search_response["items"]]

        video_stats = get_video_stats(video_ids)
        channel_stats = get_channel_stats(channel_ids)

        for video, channel in zip(video_stats["items"], channel_stats["items"]):
            video_title = video["snippet"]["title"]
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            views = int(video["statistics"].get("viewCount", 0))
            subs = int(channel["statistics"].get("subscriberCount", 0))

            if subs < max_subs and views > min_views:
                all_results.append({
                    "Keyword": keyword,
                    "Video Title": video_title,
                    "Video URL": video_url,
                    "Views": views,
                    "Subscribers": subs
                })

    # Sort results by subscribers ascending
    df = pd.DataFrame(all_results)
    df = df.sort_values(by="Subscribers", ascending=True).reset_index(drop=True)
    return df


if __name__ == "__main__":
    # Example usage
    keywords = ["pet care", "car restoration", "fitness tips"]
    results = niche_research(keywords, max_results=15, max_subs=1000, min_views=10000)

    if not results.empty:
        print("\n✅ Final Results:\n")
        print(results)
        results.to_csv("youtube_niche_research.csv", index=False)
        print("\n📂 Results saved to youtube_niche_research.csv")
    else:
        print("⚠️ No results found with given filters.")

