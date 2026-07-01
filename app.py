import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Spotify Listening Trends Explorer", layout="wide")

st.title("Spotify Listening Trends Explorer")
st.caption("Explore music habits with built-in sample data or your own Spotify CSV upload.")

SAMPLE_DATA = pd.DataFrame(
    {
        "track_name": ["Golden Hour", "Midnight Drive", "Sunrise", "Rainy Day", "Afterglow", "Blue Sky"],
        "artist_name": ["Ava", "Neon Wave", "Ava", "Loft", "Neon Wave", "Loft"],
        "timestamp": pd.to_datetime([
            "2026-01-01 08:00", "2026-01-03 22:00", "2026-02-02 07:30",
            "2026-02-14 19:15", "2026-03-01 21:10", "2026-03-18 09:05"
        ]),
        "danceability": [0.72, 0.61, 0.81, 0.42, 0.68, 0.55],
        "energy": [0.74, 0.85, 0.69, 0.38, 0.79, 0.47],
        "valence": [0.76, 0.34, 0.88, 0.28, 0.63, 0.49],
        "tempo": [118, 132, 126, 84, 140, 98],
    }
)

@st.cache_data
def load_data(file):
    return pd.read_csv(file)

def detect_text_cols(df):
    return [c for c in df.columns if df[c].dtype == "object"]

def detect_datetime_cols(df):
    return [c for c in df.columns if "date" in c.lower() or "time" in c.lower() or "timestamp" in c.lower()]

def detect_audio_cols(df):
    candidates = ["danceability", "energy", "valence", "tempo", "acousticness", "instrumentalness", "loudness"]
    return [c for c in candidates if c in df.columns]

uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
use_sample = st.toggle("Use sample Spotify-like data", value=True, help="Turn this on to use a built-in demo dataset.")

if uploaded is not None:
    df = load_data(uploaded)
    st.success(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
elif use_sample:
    df = SAMPLE_DATA.copy()
    st.info("Using sample Spotify-like data. Upload a CSV anytime to replace it.")
else:
    st.info("Enable sample data or upload a CSV file to begin.")
    st.stop()

if df.empty:
    st.error("The dataset is empty.")
    st.stop()

st.subheader("Dashboard Overview")
total_rows = len(df)
total_cols = len(df.columns)
missing_values = int(df.isna().sum().sum())

col1, col2, col3 = st.columns(3)
col1.metric("Rows", total_rows)
col2.metric("Columns", total_cols)
col3.metric("Missing Values", missing_values)

st.subheader("Data Preview")
st.dataframe(df.head(10), use_container_width=True)

numeric_cols = list(df.select_dtypes(include="number").columns)
cols = list(df.columns)
text_cols = detect_text_cols(df)
datetime_cols = detect_datetime_cols(df)
audio_cols = detect_audio_cols(df)

tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Audio Features", "Recommendations", "Data Details"])

with tab1:
    st.write("Visualize how your listening habits change over time or across categories.")
    chart_type = st.selectbox("Choose a chart", ["Bar Chart", "Line Chart", "Scatter Plot"])

    if chart_type == "Bar Chart":
        x_col = st.selectbox("Category column", text_cols if text_cols else cols, key="bar_x")
        if numeric_cols:
            y_col = st.selectbox("Value column", numeric_cols, key="bar_y")
            agg_df = df.groupby(x_col, dropna=False)[y_col].sum().reset_index().sort_values(y_col, ascending=False)
            fig = px.bar(agg_df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        else:
            counts = df[x_col].astype(str).value_counts().reset_index()
            counts.columns = [x_col, "Count"]
            fig = px.bar(counts, x=x_col, y="Count", title=f"Count of {x_col}")
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Line Chart":
        if datetime_cols:
            x_col = st.selectbox("Time column", datetime_cols, key="line_x")
            y_col = st.selectbox("Value column", numeric_cols if numeric_cols else cols, key="line_y")
            temp = df.copy()
            temp[x_col] = pd.to_datetime(temp[x_col], errors="coerce")
            temp = temp.dropna(subset=[x_col]).sort_values(x_col)
            if not temp.empty:
                temp["Month"] = temp[x_col].dt.to_period("M").dt.to_timestamp()
                monthly = temp.groupby("Month")[y_col].sum().reset_index()
                fig = px.line(monthly, x="Month", y=y_col, title=f"{y_col} by Month")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No valid dates were found in the selected column.")
        else:
            x_col = st.selectbox("X axis", cols, key="line_x_fallback")
            y_col = st.selectbox("Y axis", numeric_cols if numeric_cols else cols, key="line_y_fallback")
            temp = df.sort_values(x_col)
            fig = px.line(temp, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            st.plotly_chart(fig, use_container_width=True)

    else:
        if len(numeric_cols) >= 2:
            x_col = st.selectbox("X numeric", numeric_cols, key="scatter_x")
            y_col = st.selectbox("Y numeric", numeric_cols, key="scatter_y")
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Scatter plots need at least two numeric columns.")

with tab2:
    st.write("Audio features help describe how music sounds and feels.")
    if audio_cols:
        feature_means = df[audio_cols].apply(pd.to_numeric, errors="coerce").mean().reset_index()
        feature_means.columns = ["Feature", "Average Value"]
        fig = px.bar(feature_means, x="Feature", y="Average Value", title="Average Audio Features")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(feature_means, use_container_width=True)
    else:
        st.info("No standard Spotify audio feature columns were found in this dataset.")

with tab3:
    st.write("This section gives a simple recommendation based on the average audio profile.")
    if {"energy", "valence"}.issubset(df.columns):
        avg = df[["energy", "valence"]].apply(pd.to_numeric, errors="coerce").mean()
        energy = avg.get("energy", None)
        valence = avg.get("valence", None)

        if pd.notna(energy) and pd.notna(valence):
            if energy >= 0.65 and valence >= 0.6:
                mood = "Upbeat and happy"
                rec_text = "You seem to enjoy energetic, positive music. Try upbeat pop, dance, or feel-good playlists."
            elif energy >= 0.65 and valence < 0.6:
                mood = "Intense and powerful"
                rec_text = "You may prefer high-energy tracks with a more dramatic or serious tone."
            elif energy < 0.65 and valence >= 0.6:
                mood = "Relaxed but positive"
                rec_text = "You may like mellow songs that still feel bright, warm, and optimistic."
            else:
                mood = "Calm and reflective"
                rec_text = "You may prefer softer, slower, or more reflective music."

            st.success(f"Recommended listening mood: {mood}")
            st.write(rec_text)
            st.write(f"Average energy: {round(float(energy), 3)} | Average valence: {round(float(valence), 3)}")
        else:
            st.info("Energy and valence columns exist, but they do not contain clean numeric values.")
    else:
        st.info("Add energy and valence columns to enable this recommendation section.")

with tab4:
    with st.expander("View the first 20 rows of your dataset"):
        st.dataframe(df.head(20), use_container_width=True)
    with st.expander("View column names and data types"):
        st.write(df.dtypes)
    with st.expander("Dataset notes"):
        st.write(f"Detected text columns: {text_cols}")
        st.write(f"Detected date/time columns: {datetime_cols}")
        st.write(f"Detected audio feature columns: {audio_cols}")

st.subheader("AI Insight Prompt")
question = st.text_input("Ask a question about your Spotify data")
st.info("This textbox is ready for a GenAI integration. You can send a compact dataset summary and the user question to an LLM.")

if st.button("Generate Summary Template"):
    note = "The dataset contains listening history that can be summarized by artist, track, time, and audio features."
    if question:
        note += f" User question: {question}"
    st.write(note)