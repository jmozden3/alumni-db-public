# Alumni Database

## Overview

This repository features an interactive web-based dashboard to explore an alumni database, built with **Streamlit**.

The dashboard features search and filter functionality for fields such as industry, graduation year, company, and location. It includes visualizations for industries, geography, and more.

### AI Assistant
The app includes an integrated AI-powered chat interface. You can ask questions like "Who works in Finance in NYC?" or "List all Scrum Halves" and get answers based on the database. This feature is available directly in the Directory tab.

## Implementation

1.  Clone repository or download files locally.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  **API Key Setup (Optional but recommended for AI features):**
    *   Create a `.env` file in the root directory.
    *   Add your OpenAI API key: `OPENAI_API_KEY=sk-...`
    *   *Note: If you don't set this, the app will ask for the key in the sidebar.*
4.  Run the application:
    ```bash
    streamlit run streamlit_app.py
    ```

## Considerations

-   **Data Source**: The app uses `alumni_data.csv`. Ensure your column names match the expected format (see the CSV file or code).
-   **Security**: A `.gitignore` file is included to ensure your `.env` file (containing your API key) is **not** pushed to GitHub.

## Other Resources

*Alumni Form Questions (Google Form)*
1. First Name
2. Last Name
3. Preferred Email
4. Graduation Year (####)
5. Current Company
6. Current Position / Title
7. Industry
8. Current Location
9. Are you open to being contacted by current students in the club for recruiting-related purposes, such as coffee chats or networking? 
10. Would you like to stay informed about the club's activities and updates throughout the year?
11. Favorite rugby position? (name)
12. Any other comments you would like to make? (Questions, suggestions, nostalgia, etc)
