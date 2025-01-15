#importing the necessary libraries
# import os
import pandas as pd
import re
from geopy.geocoders import Nominatim
# from jupyter_dash import JupyterDash
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
# import dash_auth
# from flask import Flask
# from dotenv import load_dotenv

###this is used for password protection inside the application itself
###since I can pw protect through python anywhere deployment, I will not use this for now

# # Load environment variables from .env file
# load_dotenv()

# # Read password from environment variable
# PASSWORD = os.getenv('DASH_PASSWORD')

# # Ensure the environment variable is set
# if not PASSWORD:
#     raise ValueError("The DASH_PASSWORD environment variable must be set")

# # Username and password pairs (using a fixed username)
# VALID_USERNAME_PASSWORD_PAIRS = {
#     'user': PASSWORD
# }

# # Initialize the Flask server
# server = Flask(__name__)
# server.secret_key = os.urandom(24)  # Set a secret key

# # Initialize the Dash app
# app = Dash(__name__, server=server, suppress_callback_exceptions=True)
# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )

#data cleansing and preparation
file_path = "Rugby Alumni Database Form (Responses).xlsx"
df = pd.read_excel(file_path)
df = df.dropna(how='all')
df['Current Company'].fillna("N/A",inplace=True)

#rename the columns
df.rename(columns={
    "Preferred Email": "Email",
    "Graduation Year (####)": "Graduation Year",
    "Current Company": "Company",
    "Current Position / Title": "Position",
    "Are you open to being contacted by current students in the club for recruiting-related purposes, such as coffee chats or networking? ": "Open to Contact",
    "Would you like to stay informed about the CBS Rugby Football Club's activities and updates throughout the year?": "Receive Updates",
    "Favorite rugby position? (name)": "Favorite Position",
    "Any other comments you would like to make? (Questions, suggestions, nostalgia, etc)": "Comments"
}, inplace=True)

#only someone that answered yes to open to contact will be included in the table. 
contactable_alumni = df[df["Open to Contact"] == "Yes"]

#Cleaning the graduation year to ensure only numeric characters in the data
df["Graduation Year"] = pd.to_numeric(df["Graduation Year"], errors='coerce')
df["Graduation Year"] = df["Graduation Year"].apply(lambda x:re.search(r"\d{4}",str(x)).group() if pd.notnull(x) else x)

# adding latitude and longitude columns just in case I want to use that data later 
geolocator = Nominatim(user_agent="rugby_alumni_locator")

# removing duplicate entries
# drop duplicates based on specific columns (e.g., email)
df = df.drop_duplicates(subset=["Email"])

# Standardize text columns to title case
# Do not standardize location to title case
text_columns = ["Industry", "Favorite Position"]
for col in text_columns:
    df[col] = df[col].str.title()

# Clean up leading/trailing spaces in relevant columns
df["Email"] = df["Email"].str.strip()
df["Current Location"] = df["Current Location"].str.strip()
df["Industry"] = df["Industry"].str.strip()
df["Position"] = df["Position"].str.strip()

df["Graduation Year"] = pd.to_numeric(df["Graduation Year"], errors='coerce')

from dash import callback_context
ctx = callback_context

# I am defining mapping for common location variations
# This is based off the first 50 entries in the data provided
# This code was mostly AI generated and I am updating as I see fit
# More locations may need to be mapped as the data gets updated
location_mapping = {
    "NYC": "New York, NY",
    "New York City": "New York, NY",
    "New York": "New York, NY",
    "NY": "New York, NY",
    "NYC/Northern NJ": "New York, NY",
    "Northern NJ": "Newark, NJ",
    "Jersey City, New Jersey, USA": "Jersey City, NJ",
    "Montreal, Canada": "Montreal, QC",
    "Boston, MA - Austin, TX": "Boston, MA",  # Prioritized one location
    "Boston": "Boston, MA",
    "Philadelphia": "Philadelphia, PA",
    "Baltimore": "Baltimore, MD",
    "Washington, DC": "Washington, DC",
    "Morristown NJ": "Morristown, NJ",
    "Springfield MA": "Springfield, MA",
    "Central NY State": "Syracuse, NY",  # Example: Replaced with a central city
    "Houston": "Houston, TX",
    "Seattle": "Seattle, WA",
    "Seattle, WA": "Seattle, WA",  # Keep consistent formatting
    "Jakarta, Indonesia ": "Jakarta, Indonesia",  # Remove trailing spaces
    "Basel Switzerland ": "Basel, Switzerland",  # Fix spacing issues
    "Buenos Aires, Argentina": "Buenos Aires, Argentina",  # Already clean
    "London": "London, UK",
    "Toronto": "Toronto, ON",
    "New York, NY (near Union Square 3d/wk)": "New York, NY",
    "NYC Metro (Connecticut)": "New York, NY", #this guy works in NYC
    "JBeaufort SC": "Beaufort, SC"
    # Add more mappings as needed here...
}

# Apply the mapping to standardize locations
df["Current Location"] = df["Current Location"].replace(location_mapping)

# Clean up trailing spaces or inconsistent formatting (fallback for unmapped locations)
df["Current Location"] = df["Current Location"].str.strip()

#running this to get latitude and longitudinal coordinates of location
#might come in handy for later but not used in base code as of 01-12-2025
# def get_lat_lon(location):
#     try:
#         loc = geolocator.geocode(location)
#         if loc:
#             return loc.latitude, loc.longitude
#         else:
#             return None, None
#     except Exception as e:
#         print(f"Error geocoding {location}: {e}")
#         return None, None

# # Creating new columns for latitude and longitude
# df["Latitude"],df["Longitude"] = zip(*df["Current Location"].apply(get_lat_lon))

# This is the code for the Dash app

# Initialize Dash app
app = Dash(__name__, suppress_callback_exceptions=True)

# Define layout with tabs
app.layout = html.Div([
    dcc.Tabs(id="tabs", value="tab-1", children=[
        dcc.Tab(label="Dashboard", value="tab-1"),
        dcc.Tab(label="Insights (Beta)", value="tab-2")
    ]),
    html.Div(id="tab-content")  # Dynamically updated content
])

# Callback to render tab content
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_tab_content(tab):
    if tab == "tab-1":
        return render_tab_1()
    elif tab == "tab-2":
        return render_tab_2()
        
def render_tab_1():
        # Dropdown options for filters
        industries = [{"label": industry, "value": industry} for industry in sorted(df["Industry"].dropna().unique())]
        locations = [{"label": loc, "value": loc} for loc in sorted(df["Current Location"].dropna().unique())]
        years = [int(year) for year in sorted(df["Graduation Year"].dropna().unique())]

        # Pre-populate table with all rows where Open to Contact = Yes
        pre_populated_data = df[df["Open to Contact"] == "Yes"].copy()
        pre_populated_data["Email"] = pre_populated_data["Email"].apply(
            lambda x: f"[{x}](mailto:{x})" if pd.notnull(x) else ""
        )

        return html.Div([
            html.Div([
                html.Div([
                    # Left Logo
                    html.Img(
                        src="/assets/cbs_rugby_logo.jpg",
                        style={"height": "100px", "margin-right": "20px"}
                    ),
            
                    # Header Text
                    html.H1(
                        "Alumni Database",
                        style={
                            "color": "#012169",  # Dark blue color
                            "font-weight": "bold",
                            "text-align": "center",
                            "margin": "0 20px"  # Add spacing around the text
                        }
                    ),
            
                    # Right Logo
                    html.Img(
                        src="/assets/cbs_rugby_logo.jpg",
                        style={"height": "100px", "margin-left": "20px"}
                    ),
                ], style={
                    "display": "flex",  # Use flexbox for layout
                    "align-items": "center",  # Vertically center items
                    "justify-content": "center"  # Horizontally center everything
                })
            ]),

            # Reset button
            html.Button(
                "Reset All Filters",
                id="reset-filters",
                n_clicks=0,
                style={
                    "background-color": "#009EFF",
                    "color": "#FFFFFF",
                    "border": "none",
                    "padding": "10px 20px",
                    "cursor": "pointer",
                    "margin-bottom": "10px"
                }
            ),

            # Search bar filter
            dcc.Input(
                id="search-bar",
                type="text",
                placeholder="Search by name, company, or position...",
                value="",  # Default value
                style={"width": "100%", "margin-bottom": "10px"}
            ),

            # Industry dropdown filter
            dcc.Dropdown(
                id="industry-filter",
                options=industries,
                placeholder="Filter by Industry",
                multi=True,
                value=[],  # Default value
                style={"margin-bottom": "10px"}
            ),

            # Location dropdown filter
            dcc.Dropdown(
                id="location-filter",
                options=locations,
                placeholder="Filter by Location",
                multi=True,
                value=[],  # Default value
                style={"margin-bottom": "10px"}
            ),

            # Graduation year range slider filter
            dcc.RangeSlider(
                id="year-filter",
                min=min(years),
                max=max(years),
                step=1,
                marks={year: str(year) for year in years},
                value=[min(years), max(years)],  # Default range
                tooltip={"placement": "bottom", "always_visible": True},
            ),

            # Pre-populated table
            dash_table.DataTable(
                id="alumni-table",
                columns=[
                    {"name": "First Name", "id": "First Name"},
                    {"name": "Last Name", "id": "Last Name"},
                    {"name": "Email", "id": "Email", "presentation": "markdown"},
                    {"name": "Company", "id": "Company"},
                    {"name": "Industry", "id": "Industry"},
                    {"name": "Current Location", "id": "Current Location"},
                    {"name": "Position", "id": "Position"},
                    {"name": "Graduation Year", "id": "Graduation Year"}
                ],
                data=pre_populated_data.to_dict("records"),
                page_size=50,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left'}
            ),

            # Download button and component
             html.Button(
                "Download All Data",
                id="download-button",
                n_clicks=0,
                style={
                    "background-color": "#009EFF",
                    "color": "#FFFFFF",
                    "border": None,
                    'padding': '10px'
                }
            ),
            dcc.Download(id="download-dataframe")
        ])

# Callback to reset all filters
@app.callback(
    [
        Output("search-bar", 'value'),
        Output("industry-filter", 'value'),
        Output("location-filter", 'value'),
        Output("year-filter", 'value')
    ],
    Input("reset-filters", 'n_clicks')
)

def reset_filters(n_clicks):
    if n_clicks > 0:
        return "", [], [], [min(df["Graduation Year"]), max(df["Graduation Year"])]
    return "", [], [], [min(df["Graduation Year"]), max(df["Graduation Year"])]  # Default return

# Callback to dynamically update the table based on filters
@app.callback(
    Output("alumni-table", 'data'),
    [
        Input("search-bar", 'value'),
        Input("industry-filter", 'value'),
        Input("location-filter", 'value'),
        Input("year-filter", 'value')
    ]
)

def consolidated_update_table(search_text, selected_industries, selected_locations, selected_years):
    # Initialize DataFrame with default filter: "Open to Contact" == "Yes"
    filtered_df = df[df["Open to Contact"] == "Yes"].copy()

    # Check for filter changes using callback_context
    ctx = callback_context
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Handle search bar input
    if triggered_input == "search-bar" or search_text:
        search_text = search_text.lower() if search_text else ""
        filtered_df = filtered_df[
            filtered_df["First Name"].str.lower().str.contains(search_text) |
            filtered_df["Last Name"].str.lower().str.contains(search_text) |
            filtered_df["Company"].str.lower().str.contains(search_text) |
            filtered_df["Position"].str.lower().str.contains(search_text)
        ]

    # Apply industry filter
    if selected_industries:
        filtered_df = filtered_df[filtered_df["Industry"].isin(selected_industries)]

    # Apply location filter
    if selected_locations:
        filtered_df = filtered_df[filtered_df["Current Location"].isin(selected_locations)]

    # Apply graduation year filter
    if selected_years:
        start_year, end_year = selected_years
        filtered_df = filtered_df[
            (filtered_df["Graduation Year"] >= start_year) & 
            (filtered_df["Graduation Year"] <= end_year)
        ]

    # Update mailto link
    filtered_df["Email"] = filtered_df["Email"].apply(lambda x: f"[{x}](mailto:{x})" if pd.notnull(x) else "")

    return filtered_df.to_dict('records')

# Callback to download unfiltered data (filtered by Open to Contact = Yes)
@app.callback(
    Output("download-dataframe", 'data'),
    Input("download-button", 'n_clicks')
)
def download_data(n_clicks):
    if n_clicks > 0:
        # Filter rows where Open to Contact = Yes
        filtered_df = df[df["Open to Contact"] == "Yes"]

        # Select only the columns displayed in the Dash table
        filtered_df = filtered_df[[
            "First Name", "Last Name", "Email", "Graduation Year",
            "Company", "Position", "Industry", "Current Location"
        ]]

        # Concatenate First Name and Last Name into a single "Name" column
        filtered_df["Name"] = filtered_df["First Name"] + " " + filtered_df["Last Name"]

        # Reorder columns to match the table layout
        filtered_df = filtered_df[[
            "Name", "Email", "Graduation Year", "Company",
            "Position", "Industry", "Current Location"
        ]]

        # Return the filtered DataFrame as an Excel file
        return dcc.send_data_frame(filtered_df.to_excel, filename="Rugby_Alumni_Data.xlsx", index=False)

        pass 

def render_tab_2():
    # Calculate Top 3 Industries
    industry_counts = df["Industry"].value_counts().head(3)
    top_3_industries_list = [
        html.Li(f"{industry}: {count}", style={"color": "#012169"}) 
        for industry, count in industry_counts.items()
    ]

    # Calculate Total Alumni
    total_alumni = len(df)

    # Calculate Most Popular Position
    most_popular_position = df["Favorite Position"].mode()[0] if not df["Favorite Position"].isnull().all() else "N/A"

    # Aggregate data by state for U.S. map
    df["State"] = df["Current Location"].str.extract(r'([A-Z]{2})$')  # Extract state abbreviation (e.g., "NY", "CA")
    state_counts = df["State"].value_counts().reset_index()
    state_counts.columns = ["State", "Count"]

    # Create U.S. choropleth map
    us_choropleth_fig = px.choropleth(
        state_counts,
        locations="State",
        locationmode="USA-states",
        color="Count",
        color_continuous_scale="Blues",
        scope="usa",
        title="Alumni Distribution by State"
    )

    # Aggregate data by industry for bar chart
    industry_counts = df["Industry"].value_counts().reset_index()
    industry_counts.columns = ["Industry", "Count"]

    # Create Industry Bar Chart
    industry_bar_chart_fig = px.bar(
        industry_counts,
        x="Industry",
        y="Count",
        title="Alumni by Industry",
        labels={"Industry": "Industry", "Count": "Number of Alumni"},
        color="Count",  # Color bars based on count
        color_continuous_scale="blues"  # Use blue color scale for consistency
    )

    # Aggregate data by graduation year for bar chart
    grad_year_counts = df["Graduation Year"].value_counts().sort_index().reset_index()
    grad_year_counts.columns = ["Graduation Year", "Count"]

    # Create Graduation Year Distribution Bar Chart
    grad_year_bar_chart_fig = px.bar(
        grad_year_counts,
        x="Graduation Year",
        y="Count",
        title="Alumni Distribution by Graduation Year",
        labels={"Graduation Year": "Graduation Year", "Count": "Number of Alumni"},
        color="Count",  # Color bars based on count
        color_continuous_scale="blues"  # Use blue color scale for consistency
    )

    return html.Div([
        # Header with logos and title
        html.Div([
            html.Div([
                # Left Logo
                html.Img(
                    src="/assets/cbs_rugby_logo.jpg",
                    style={"height": "100px", "margin-right": "20px"}
                ),
                # Header Text
                html.H1(
                    "Alumni Database",
                    style={
                        "color": "#012169",  # Dark blue color
                        "font-weight": "bold",
                        "text-align": "center",
                        "margin": "0 20px"
                    }
                ),
                # Right Logo
                html.Img(
                    src="/assets/cbs_rugby_logo.jpg",
                    style={"height": "100px", "margin-left": "20px"}
                ),
            ], style={
                "display": "flex", 
                "align-items": "center", 
                "justify-content": "center"
            })
        ]),

        # Cards at the top of Tab 2
        html.Div([
            # Top 3 Industries Card
            html.Div([
                html.H4("Top 3 Industries", style={"color": "#012169","font-size":"24px"}),
                html.Ul(top_3_industries_list, style={"list-style-type": "none", "padding": 0,"font-size":"20px"})
            ], style={
                'background-color': '#6CACE4',
                'padding': '20px',
                'border-radius': '10px',
                'width': '30%',
                'text-align': 'center',
                'margin-right': '10px'
            }),

            # Total Alumni Card
            html.Div([
                html.H4("Total Alumni", style={"color": "#012169","font-size":"24px"}),
                html.P(f"{total_alumni}", style={"color": "#012169","font-size":"20px"})
            ], style={
                'background-color': '#6CACE4',
                'padding': '20px',
                'border-radius': '10px',
                'width': '30%',
                'text-align': 'center',
                'margin-right': '10px'
            }),

            # Most Popular Position Card
            html.Div([
                html.H4("Most Popular Position", style={"color": "#012169","font-size":"24px"}),
                html.P(most_popular_position, style={"color": "#012169","font-size":"20px"})
            ], style={
                'background-color': '#6CACE4',
                'padding': '20px',
                'border-radius': '10px',
                'width': '30%',
                'text-align': 'center'
            }),
        ], style={
            'display': 'flex',
            'justify-content': 'space-between',
            'margin-top': '20px'
        }),

        # Geolocation Graphs (U.S. map and Industry bar chart side by side)
        html.Div([
            dcc.Graph(figure=us_choropleth_fig, style={"flex-grow": 1, "margin-right": "10px", "height": "600px"}),  
            dcc.Graph(figure=industry_bar_chart_fig, style={"flex-grow": 1, "height": "600px"})  
        ], style={
            'display': 'flex',
            'justify-content': 'space-between',
            'margin-top': '20px'
        }),

        # Graduation Year Distribution Bar Chart (below other graphs)
        dcc.Graph(
            figure=grad_year_bar_chart_fig,
            style={"margin-top": "40px", "height": "400px",'border-radius': '10px' }  # Adjust height as needed
        )
    ])

if __name__ == "__main__":
    app.run(debug=True) #user port 8051 if you want to add password protection in the app itself