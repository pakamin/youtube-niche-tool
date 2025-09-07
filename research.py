import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

# ==============================
# Setup YouTube API
# ==============================
st.set_page_config(page_title="YouTube Niche Research Tool", layout="wide")
API_KEY = st.secrets["API_KEY"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

# ==============================
# Functions
# ==============================
def search_youtube(keyword, max_results=10, published_after=None):
    """Search videos for a given keyword"""
    try:
        request = youtube.search().list(
            q=keyword,
            part="id,snippet",
            type="video",
            maxResults=max_results,
            order="relevance",
            publishedAfter=published_after
        )
        return request.execute()
    except HttpError as e:
        st.error(f"❌ YouTube API Error for '{keyword}': {e}")
        return None

def get_video_stats(video_ids):
    """Fetch statistics for a list of video IDs"""
    try:
        request = youtube.videos().list(
            part="statistics,contentDetails,snippet",
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
            part="statistics,snippet",
            id=",".join(channel_ids)
        )
        return request.execute()
    except HttpError as e:
        st.error(f"❌ Channel stats error: {e}")
        return None

def niche_research(keywords, max_results=10, min_subs=0, max_subs=1000, min_views=10000, max_views=None):
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
            likes = int(vstat["statistics"].get("likeCount", 0))
            comments = int(vstat["statistics"].get("commentCount", 0))
            publish_date = vstat["snippet"].get("publishedAt", "")

            # Filters
            if subs >= min_subs and subs <= max_subs and views >= min_views:
                if max_views and views > max_views:
                    continue
                all_results.append({
                    "Keyword": keyword,
                    "Title": title,
                    "Description": description,
                    "URL": video_url,
                    "Views": views,
                    "Subscribers": subs,
                    "Likes": likes,
                    "Comments": comments,
                    "Publish Date": publish_date,
                    "Channel Name": cstat["snippet"].get("title", "N/A"),
                    "Channel URL": f"https://www.youtube.com/channel/{cstat['id']}"
                })
    return all_results

# ==============================
# Streamlit UI
# ==============================
st.title("📊 YouTube Niche Research Tool")

# User inputs
keywords_input = st.text_area("Enter niche keywords (comma separated):")
max_results = st.number_input("Max Results per keyword", min_value=1, max_value=50, value=10)
min_subs = st.number_input("Min Subscribers", min_value=0, value=0)
max_subs = st.number_input("Max Subscribers", min_value=0, value=1000)
min_views = st.number_input("Min Views", min_value=0, value=10000)
max_views = st.number_input("Max Views (optional, 0 for no limit)", min_value=0, value=0)

# Adjust max_views
if max_views == 0:
    max_views = None

if st.button("Run Research"):
    if not keywords_input.strip():
        st.warning("⚠️ Please enter at least one keyword.")
    else:
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        st.info("⏳ Running niche research... please wait.")

        results = niche_research(keywords, max_results=max_results, min_subs=min_subs, max_subs=max_subs, min_views=min_views, max_views=max_views)
        df = pd.DataFrame(results)

        if df.empty:
            st.warning("No results found with the given filters. Try adjusting filters.")
        else:
            st.success(f"✅ Found {len(df)} results!")
            st.dataframe(df)

            # CSV & Excel export
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "youtube_niche_results.csv", "text/csv")

            excel_file = pd.ExcelWriter("youtube_niche_results.xlsx", engine="xlsxwriter")
            df.to_excel(excel_file, index=False, sheet_name="Results")
            excel_file.save()
            st.download_button("📥 Download Excel", open("youtube_niche_results.xlsx", "rb").read(), "youtube_niche_results.xlsx", "application/vnd.ms-excel")

            # ==============================
            # Visualization
            # ==============================
            st.subheader("📈 Top 10 Videos by Views")
            top_videos = df.sort_values(by="Views", ascending=False).head(10)
            st.bar_chart(top_videos[["Title", "Views"]].set_index("Title"))

            st.subheader("📈 Top 10 Channels by Subscribers")
            top_channels = df.groupby("Channel Name")["Subscribers"].max().sort_values(ascending=False).head(10)
            st.bar_chart(top_channels)
