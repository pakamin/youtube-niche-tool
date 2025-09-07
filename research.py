import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ Get your API key from Streamlit Secrets (don’t write it in GitHub!)
API_KEY = st.secrets["API_KEY"]

API_KEY = st.secrets["API_KEY"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

# ==============================
# Functions
# ==============================
def search_youtube(keyword, max_results=10):
    """Search videos for a given keyword"""
    try:
        request = youtube.search().list(
            q=keyword,
            part="id,snippet",
            type="video",
            maxResults=max_results
        )
        return request.execute()
    except HttpError as e:
        st.error(f"❌ YouTube API Error for '{keyword}': {e}")
        return None


def get_video_stats(video_ids):
    """Fetch statistics for a list of video IDs"""
    try:
        request = youtube.videos().list(
            part="statistics",
            id=",".join(video_ids)
        )
        return request.execute()
    except HttpError as e:
        st.error(f"❌ Video stats error: {e}")
        return None


def get_channel_stats(channel_ids):
    """Fetch statistics for a list of channel IDs"""
    try:
        request = youtube.channels().list(
            part="statistics",
            id=",".join(channel_ids)
        )
        return request.execute()
    except HttpError as e:
        st.error(f"❌ Channel stats error: {e}")
        return None


def niche_research(keywords, max_results=10, max_subs=1000, min_views=10000):
    """Run niche research and return filtered results"""
    all_results = []

    for keyword in keywords:
        search_response = search_youtube(keyword, max_results=max_results)
        if not search_response or "items" not in search_response:
            continue

        videos = search_response["items"]
        video_ids = [v["id"]["videoId"] for v in videos]
        channel_ids = [v["snippet"]["channelId"] for v in videos]

        video_stats = get_video_stats(video_ids)
        channel_stats = get_channel_stats(channel_ids)

        if not video_stats or not channel_stats:
            continue

        for video, vstat, cstat in zip(videos, video_stats.get("items", []), channel_stats.get("items", [])):
            title = video["snippet"].get("title", "N/A")
            description = video["snippet"].get("description", "")[:200]
            video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
            views = int(vstat["statistics"].get("viewCount", 0))
            subs = int(cstat["statistics"].get("subscriberCount", 0))

            # ✅ Apply filters
            if subs <= max_subs and views >= min_views:
                all_results.append({
                    "Keyword": keyword,
                    "Title": title,
                    "Description": description,
                    "URL": video_url,
                    "Views": views,
                    "Subscribers": subs
                })

    return all_results

# ==============================
# Streamlit UI
# ==============================
st.title("📊 YouTube Niche Research Tool")

keywords_input = st.text_area("Enter niche keywords (comma separated):")
max_results = st.number_input("Max Results per keyword", min_value=1, max_value=50, value=10)
max_subs = st.number_input("Max Subscribers (filter)", min_value=0, value=1000)
min_views = st.number_input("Min Views (filter)", min_value=0, value=10000)

if st.button("Run Research"):
    if not keywords_input.strip():
        st.warning("⚠️ Please enter at least one keyword.")
    else:
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        st.info("⏳ Running niche research... please wait.")

        results = niche_research(keywords, max_results=max_results, max_subs=max_subs, min_views=min_views)
        df = pd.DataFrame(results)

        if df.empty:
            st.warning("No results found with the given filters.")
        else:
            st.success(f"✅ Found {len(df)} results!")
            st.dataframe(df)

            # CSV export
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Results", csv, "youtube_niche_results.csv", "text/csv")
