# Cahoots

Learn more about the developer: www.linkedin.com/in/maheskett

Cahoots is a full-stack, data visualization app that provides valuable insights into users calendars. It automatically tags Google Calendar events and generates data on how users and their coworkers spend their time. Cahoots also analyzes the level of collaboration within companies through an interactive D3 diagram. Users can filter by date range and calendars to see how much time any group of people within their company spend working together.

# Table of Contents
* [Tech stack](#technologies)
* [Features](#features)
* [Installation](#install)
* [Version 2.0](#future)

## <a name="technologies"></a>Technologies
- Python, OAuth 2.0, Google Calendar & People APIs, Flask, Jinja2, Datetime
- Javascript, jQuery, AJAX, D3, Chart.js, Underscore.js, Moment.js
- PostgreSQL, SQLAlchemy, HTML5, CSS, Bootstrap

## <a name="features"></a>Features

![alt text](static/imgs/hp.png)

Users sign in with Google. This is handled through OAuth 2.0, which authenticates the user and authorizes the app to view the user's Google calendar. For more information, please see [Google's OAuth documentation](https://developers.google.com/api-client-library/python/guide/aaa_oauth).

####Dashboard

After login, the user is directed to the dashboard page where they can choose the calendars they want to look at, along with the chart type and date range.

![alt text](static/imgs/chord.png)

####Analyze Collaboration

![alt text](static/imgs/chord-2.png)

####Analyze Individual's Time

![alt text](static/imgs/doughnut.png)

## <a name="install"></a>Installation