# Alumni Database

## Overview

This repository's python code (app.py) is an interactive web-based dashboard built with Python and Plotly Dash to explore an alumni database. The dashboard features search and filter functionality for fields such as industry, graduation year, company, and location. It also includes visualizations for most popular industries, grads by city, and more. The app supports iterative data updates via linked Google Sheets or Excel files. 

This is a perfect beginner application for any organizations looking to work with their alumni information in an accessible and interactive way. I was originally inspired to do this for my grad school's rugby team and thought it could be applied to any group. 

This is far from a finished product so feel free to develop or adjust in any way you see fit. I will continue to update this repo as I update my own app. 

## Implementation

1. Clone repository or download files locally
2. pip install -r requirements.txt in your environment
3. Run application app.py
4. Deploy app (I used pythonanywhere but you can use whatever you feel most comfortable with)

## Considerations

- To get the data I used a google form and downloaded the results as a .csv. Ensure your column names match up with the names of the columns in the code, or adjust them to your preference. See 'Other Resources' for the questions used, or view the .csv file.
- Change the photo in the assets folder and change the asset path code to adjust your picture in the application

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
