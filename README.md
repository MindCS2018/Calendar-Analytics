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

After login, the user is directed to the dashboard page where they choose the calendars to analyze, along with the chart type and date range. Clicking any of the buttons sends an AJAX request to the server, which then queries the database and returns the appropriate data structure to render the chart.

![alt text](static/imgs/chord.png)

####Team View

In this D3 chord diagram, the nodes represent the members of the team and the arcs represent the total amount of time any two coworkers spend working together. Hovering over the arcs displays a tooltip with information about the total number of hours spent together, the total percentage of each person's time, and the total percentage of the team's time.

![alt text](static/imgs/chord-2.png)

####Individual View

![alt text](static/imgs/doughnut.png)

## <a name="install"></a>Installation