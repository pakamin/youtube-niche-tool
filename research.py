import streamlit as st
import pandas as pd
import googleapiclient.discovery

# Load API key from Streamlit secrets
API_KEY = st.secrets["YOUTUBE_API_KEY"]

# Initialize YouTube API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

def search_youtube(keyword, max_results=10):
    try:
        request = youtube.search().list(
            q=keyword,
            part="snippet",
            type="video",
            maxResults=max_results
        )
        return request.execute()
    except googleapiclient.errors.HttpError as e:
        error_message = e.content.decode("utf-8") if hasattr(e, "content") else str(e)
        st.error(f"❌ YouTube API Error for '{keyword}': {error_message}")
        return {"items": []}
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")
        return {"items": []}

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

def niche_research(keywords, max_results=10, max_subs=1000, min_views=10000):
    output = []
    for keyword in keywords:
        try:
            search_response = search_youtube(keyword, max_results=max_results)
            
            for item in search_response.get("items", []):
                video_id = item["id"]["videoId"]
                channel_id = item["snippet"]["channelId"]

                video_stats = youtube.videos().list(
                    part="statistics",
                    id=video_id
                ).execute()

                channel_stats = youtube.channels().list(
                    part="statistics",
                    id=channel_id
                ).execute()

                for video, channel in zip(video_stats.get("items", []), channel_stats.get("items", [])):
                    subs = int(channel["statistics"].get("subscriberCount", 0))
                    views = int(video["statistics"].get("viewCount", 0))

                    if subs < max_subs and views > min_views:
                        output.append({
                            "Keyword": keyword,
                            "Video URL": f"https://www.youtube.com/watch?v={video_id}",
                            "Subscribers": subs,
                            "Views": views
                        })

        except Exception as e:
            st.error(f"❌ Error processing keyword '{keyword}': {e}")

    return output


# -------------------- STREAMLIT UI --------------------
st.title("📊 YouTube Niche Research Tool")

keywords_input = st.text_area("Enter niche keywords (comma separated):", "pet care, car restoration, fitness tips")
max_subs = st.number_input("Maximum Subscribers", min_value=0, value=1000, step=100)
min_views = st.number_input("Minimum Views", min_value=0, value=10000, step=1000)
max_results = st.slider("Max results per keyword", 5, 50, 15)

if st.button("Run Research"):
    keywords = [k.strip() for k in keywords_input.split(",")]
    results = niche_research(keywords, max_results=max_results, max_subs=max_subs, min_views=min_views)

    if not results.empty:
        st.success("✅ Results Found")
        st.dataframe(results)

        # Download button
        csv = results.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="youtube_niche_research.csv", mime="text/csv")
    else:
        st.warning("⚠️ No results found with given filters.")


