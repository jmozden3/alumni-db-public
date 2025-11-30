import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Alumni Database",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Data Loading & Cleaning (Ported from app.py) ---
@st.cache_data
def load_data():
    file_path = "alumni_data.csv"
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        st.error("alumni_data.csv not found. Please ensure the file is in the root directory.")
        return pd.DataFrame()

    df = df.dropna(how='all')
    df['Current Company'] = df['Current Company'].fillna("N/A")

    # Rename columns
    df.rename(columns={
        "Preferred Email": "Email",
        "Graduation Year (####)": "Graduation Year",
        "Current Company": "Company",
        "Current Position / Title": "Position",
        "Are you open to being contacted by current students in the club for recruiting-related purposes, such as coffee chats or networking? ": "Open to Contact",
        "Would you like to stay informed about the club's activities and updates throughout the year?": "Receive Updates",
        "Favorite rugby position? (name)": "Favorite Position",
        "Any other comments you would like to make? (Questions, suggestions, nostalgia, etc)": "Comments"
    }, inplace=True)

    # Cleaning graduation year
    df["Graduation Year"] = pd.to_numeric(df["Graduation Year"], errors='coerce')
    # Apply regex to extract year if possible (from original code)
    df["Graduation Year"] = df["Graduation Year"].apply(lambda x: re.search(r"\d{4}", str(x)).group() if pd.notnull(x) else x)
    df["Graduation Year"] = pd.to_numeric(df["Graduation Year"], errors='coerce')

    # Remove duplicates
    df = df.drop_duplicates(subset=["Email"])

    # Standardize text
    text_columns = ["Industry", "Favorite Position"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.title()

    # Strip whitespace
    string_cols = ["Email", "Current Location", "Industry", "Position"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Location Mapping
    location_mapping = {
        "NYC": "New York, NY",
        "New York City": "New York, NY",
        "New York": "New York, NY",
        "NY": "New York, NY",
        "NYC/Northern NJ": "New York, NY",
        "Northern NJ": "Newark, NJ",
        "Jersey City, New Jersey, USA": "Jersey City, NJ",
        "Montreal, Canada": "Montreal, QC"
    }
    df["Current Location"] = df["Current Location"].replace(location_mapping)
    df["Current Location"] = df["Current Location"].str.strip()

    # Create Name column for easier display
    df["Name"] = df["First Name"] + " " + df["Last Name"]

    return df

df = load_data()

if df.empty:
    st.stop()

# --- Layout ---

st.title("🎓 Alumni Database")

# Tabs
tab1, tab2 = st.tabs(["Directory", "Insights"])
tab1, tab2, tab3 = st.tabs(["Directory", "Insights", "AI Assistant"])

# --- TAB 1: Directory ---
with tab1:
    st.header("Alumni Directory")

    # --- AI Assistant Expander ---
    with st.expander("💬 Ask the AI Assistant about the alumni data"):
        st.write("Ask questions about the alumni data! (e.g., 'Who works in Finance in NYC?', 'List all Scrum Halves')")

        # API Key Handling
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.text_input("Enter OpenAI API Key", type="password")

        if not api_key:
            st.warning("Please enter an OpenAI API key to use the AI features.")
        else:
            # Chat Interface
            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if prompt := st.chat_input("Ask a question..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    message_placeholder = st.empty()

                    try:
                        from openai import OpenAI
                        client = OpenAI(api_key=api_key)

                        # Prepare context
                        # For a small dataset, we can pass the CSV content directly or a summary.
                        # Since it's small (~50 rows based on plan), we can pass the CSV.
                        csv_string = df.to_csv(index=False)

                        system_prompt = f"""
                        You are a helpful assistant for an alumni database.
                        Here is the data in CSV format:

                        {csv_string}

                        Answer the user's question based ONLY on this data.
                        If the answer is a list of people, format it nicely.
                        If you can't find the answer, say so.
                        """

                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo", # or gpt-4o
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ]
                        )

                        answer = response.choices[0].message.content
                        message_placeholder.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # Sidebar Filters (only applied to this view mostly, but sidebar is global)
    # We can put filters in the sidebar or in an expander. Sidebar is cleaner.
    st.sidebar.header("Filters")

    # Search Filter
    search_term = st.sidebar.text_input("Search (Name, Company, Position)", "")

    # Industry Filter
    all_industries = sorted(df["Industry"].dropna().unique())
    selected_industries = st.sidebar.multiselect("Industry", all_industries)

    # Location Filter
    all_locations = sorted(df["Current Location"].dropna().unique())
    selected_locations = st.sidebar.multiselect("Location", all_locations)

    # Year Filter
    min_year = int(df["Graduation Year"].min()) if not df["Graduation Year"].isnull().all() else 2000
    max_year = int(df["Graduation Year"].max()) if not df["Graduation Year"].isnull().all() else 2025

    # Ensure min < max
    if min_year >= max_year:
        min_year = max_year - 1

    selected_years = st.sidebar.slider("Graduation Year", min_year, max_year, (min_year, max_year))

    # Apply Filters
    filtered_df = df[df["Open to Contact"] == "Yes"].copy() # Only show contactable alumni in table

    # Search
    if search_term:
        s = search_term.lower()
        filtered_df = filtered_df[
            filtered_df["Name"].str.lower().str.contains(s) |
            filtered_df["Company"].str.lower().str.contains(s) |
            filtered_df["Position"].str.lower().str.contains(s)
        ]

    # Industry
    if selected_industries:
        filtered_df = filtered_df[filtered_df["Industry"].isin(selected_industries)]

    # Location
    if selected_locations:
        filtered_df = filtered_df[filtered_df["Current Location"].isin(selected_locations)]

    # Year
    filtered_df = filtered_df[
        (filtered_df["Graduation Year"] >= selected_years[0]) &
        (filtered_df["Graduation Year"] <= selected_years[1])
    ]

    # Display Count
    st.markdown(f"**Showing {len(filtered_df)} alumni**")

    # Display Table
    # Configure columns
    display_cols = ["Name", "Email", "Graduation Year", "Company", "Position", "Industry", "Current Location"]

    st.dataframe(
        filtered_df[display_cols],
        column_config={
            "Email": st.column_config.LinkColumn("Email", display_text=r"(.*)"),
            "Graduation Year": st.column_config.NumberColumn("Year", format="%d"),
        },
        use_container_width=True,
        hide_index=True
    )

    # Download Button
    # Prepare data for download
    csv = filtered_df[display_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name='alumni_data_filtered.csv',
        mime='text/csv',
    )


# --- TAB 2: Insights ---
with tab2:
    st.header("Dashboard Insights")

    # Metrics
    col1, col2, col3 = st.columns(3)

    # Top Industries
    industry_counts = df["Industry"].value_counts()
    top_industry = industry_counts.index[0] if not industry_counts.empty else "N/A"

    # Most Popular Position
    position_counts = df["Favorite Position"].value_counts()
    top_position = position_counts.index[0] if not position_counts.empty else "N/A"

    col1.metric("Total Alumni", len(df))
    col2.metric("Top Industry", top_industry)
    col3.metric("Top Rugby Position", top_position)

    st.divider()

    # Charts
    c1, c2 = st.columns(2)

    with c1:
        # Industry Bar Chart
        ind_counts_df = industry_counts.reset_index()
        ind_counts_df.columns = ["Industry", "Count"]
        fig_ind = px.bar(
            ind_counts_df.head(10),
            x="Industry",
            y="Count",
            title="Top 10 Industries",
            color="Count",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig_ind)

    with c2:
        # Map
        # Extract state for USA map
        df["State"] = df["Current Location"].str.extract(r'([A-Z]{2})$')
        state_counts = df["State"].value_counts().reset_index()
        state_counts.columns = ["State", "Count"]

        fig_map = px.choropleth(
            state_counts,
            locations="State",
            locationmode="USA-states",
            color="Count",
            color_continuous_scale="Blues",
            scope="usa",
            title="Alumni Distribution by State"
        )
        st.plotly_chart(fig_map)

    # Graduation Year Dist
    grad_counts = df["Graduation Year"].value_counts().sort_index().reset_index()
    grad_counts.columns = ["Year", "Count"]
    fig_year = px.bar(
        grad_counts,
        x="Year",
        y="Count",
        title="Graduation Year Distribution",
        color="Count",
        color_continuous_scale="Blues"
    )
    st.plotly_chart(fig_year)

# --- TAB 3: AI Assistant ---
with tab3:
    st.header("🤖 AI Assistant")
    st.write("Ask questions about the alumni data! (e.g., 'Who works in Finance in NYC?', 'List all Scrum Halves')")

    # API Key Handling
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter OpenAI API Key", type="password")

    if not api_key:
        st.warning("Please enter an OpenAI API key to use the AI features.")
    else:
        # Chat Interface
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask a question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()

                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)

                    # Prepare context
                    # For a small dataset, we can pass the CSV content directly or a summary.
                    # Since it's small (~50 rows based on plan), we can pass the CSV.
                    csv_string = df.to_csv(index=False)

                    system_prompt = f"""
                    You are a helpful assistant for an alumni database.
                    Here is the data in CSV format:

                    {csv_string}

                    Answer the user's question based ONLY on this data.
                    If the answer is a list of people, format it nicely.
                    If you can't find the answer, say so.
                    """

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo", # or gpt-4o
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ]
                    )

                    answer = response.choices[0].message.content
                    message_placeholder.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except Exception as e:
                    st.error(f"Error: {str(e)}")
