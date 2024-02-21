# Competitor News Web Application

This is a Flask-based web application for scraping competitor news from Google News and evaluating their relevance. It also provides a simple interface for users to input a keyword related to a vehicle manufacturer and fetch the latest news articles.

## Installation

To run this application locally, follow these steps:

1. Navigate to the project directory:
   ```
   cd competitor-news
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3.  Run docker-compose.

    ```shell
    docker-compose up -d
    ```

4. Run test: 
   ```
   python test.py
   ```

5. Start the Flask server:
   ```
   python app.py
   ```

## Usage

Once the application is running, you can access it in your web browser at [http://localhost:5000](http://localhost:5000). You will see a simple interface where you can input a keyword related to a vehicle manufacturer, such as "Toyota" or "Ford", and submit the form to fetch the latest news articles related to that keyword.

## Features

- Fetches news articles from Google News based on user input.
- Evaluates the relevance of news articles based on predefined keywords.
- Stores fetched news articles in a SQLite database.
- Exposes Prometheus-formatted metrics for monitoring HTTP requests and response times.

## Dependencies

- Flask
- SQLAlchemy
- feedparser
- requests
- prometheus-flask-exporter
- pika (RabbitMQ client)