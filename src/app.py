from flask import Flask, render_template, request
from prometheus_flask_exporter import PrometheusMetrics
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import feedparser
import requests
import logging
from logging.handlers import RotatingFileHandler
import sys
import pika
import os
import json
from app_database import db, CompetitorNews

app = Flask(__name__)

# Create a PrometheusMetrics instance and associate it with Flask
# When run this Flask application and access the /metrics endpoint, we'll see 
# Prometheus-formatted metrics related to HTTP requests, response times, and 
# other default metrics provided by prometheus_flask_exporter.
metrics = PrometheusMetrics(app)

# Define the database model that is used to store the data
current_directory = os.path.abspath(os.path.dirname(__file__))
database_file_path = os.path.join(current_directory, 'CompetitorNews.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + database_file_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy extension with Flask application instance 
db.init_app(app)
with app.app_context():
        db.create_all()

# Configure logging
def configure_logging():
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
    my_logger = logging.getLogger(__name__)
    my_logger.setLevel(logging.INFO)
    
    # Log to file with rotating file handler
    file_handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(log_formatter)
    my_logger.addHandler(file_handler)
    
    # Log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    my_logger.addHandler(console_handler)
    
    return my_logger

my_logger = configure_logging()

def title_truncate(title):
    parts = title.rsplit('-', 1)
    truncated_title = parts[0].strip() if len(parts) > 1 else title.strip()
    return truncated_title

# Evaluate the relevance of the news based on the presence of certain keywords
def news_evaluator(title):
    keywords = {'engine','diesel','battery','truck','bus','new','hydrogen','power'}
    title_lower = title.lower()
    matched_keywords = sum(1 for keyword in keywords if keyword in title_lower)
    relevance_scores = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 6: 4}
    relevance_score = relevance_scores.get(matched_keywords, 5)
    return relevance_score 

# Fetche news articles from Google News based on a given key, processes them, and then stores them in a database
def fetch_store_news(key):
    GOOGLE_NEWS_URL = 'https://news.google.com'
    BASE_URL = f"{GOOGLE_NEWS_URL}/rss"
    TIME_RANGE = '%20when%3A7d&hl=en-US&gl=US&ceid=US:en'
    MAX_RESULT = 10

    if not key:
        return []

    key = "%20".join(key.split())
    query = f'/search?q={key}'
    url = f"{BASE_URL}{query}{TIME_RANGE}"
    items = []
    try:
        feed_data = feedparser.parse(url)
        for news in feed_data.entries[:MAX_RESULT]:
            if not news:
                continue
            url = news.get('link')
            if not url.startswith('https://news.google.com'):
                url = requests.head(url).headers.get('location', url)
            title = news.get("title", "")
            item = {
                'title': title_truncate(title),
                'grade': news_evaluator(title),
                'url': url,
                'publisher': news.get("source", {}).get("title", ""),
                'published_date': news.get("published", "")
            }
            items.append(item)
            data_entry = CompetitorNews.query.filter_by(OEM=key).first()
            if data_entry:
                data_entry.news = item
            else:
                new_data = CompetitorNews(OEM=key, news=item)
                db.session.add(new_data)
        db.session.commit()
        return {index: item for index, item in enumerate(items)}
    except Exception as e:
        my_logger.exception("Error fetching news for %s: %s", key, str(e))
        return []

def setup_rabbitmq():
    # RabbitMQ connection parameters
    RABBITMQ_HOST = os.environ.get('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.environ.get('RABBITMQ_PORT', '5672'))
    rabbitmq_url = os.getenv('RABBITMQ_URL','amqps://jcqgoike:1c6nP86bqZZIj32sEShAnBN0YrO7tR7m@shark.rmq.cloudamqp.com/jcqgoike')
    EXCHANGE_NAME = 'my_exchange'
    # Create a connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_url))
    # Create a channel from the connection
    channel = connection.channel()
    # Declare an exchange
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct')
    # Declare a queue
    channel.queue_declare(queue='my_queue')
    # Bind the queue to the exchange
    channel.queue_bind(exchange=EXCHANGE_NAME, queue='my_queue', routing_key='my_routing_key')
    
    return connection, channel

connection, channel = setup_rabbitmq()

def teardown_rabbitmq():
    try:
        if connection and connection.is_open:
            connection.close()
            print("RabbitMQ connection closed.")
    except Exception as e:
        print("Error closing RabbitMQ connection:", str(e))

@app.route('/')
def index():
    return render_template("index.html",msg='')

@app.route('/user', methods =['GET','POST'])
def user():
    try: 
        if request.method == 'POST':
            user_input = request.form.get("user_input",'')
            if not user_input.strip():
                return render_template("index.html",msg="Please input valid value.")
            news_data = fetch_store_news(user_input)
            connection, channel = setup_rabbitmq()
            if news_data:
                channel.basic_publish(exchange='my_exchange',routing_key='my_queue', body=json.dumps(news_data))
                my_logger.info(f"{user_input} news data published to RabbitMQ.")
                return render_template('user.html',items=news_data)
            else:
                logger.warning(f"No {user_input} news data found.")  
                return render_template("index.html",msg="No news data found")
        else:
            return render_template('index.html',msg='')
    except Exception as e:
        my_logger.exception("An error occurred: %s", str(e))
        return render_template('index.html',msg="An error occurred")

@app.teardown_appcontext
def teardown_rabbitmq(exception=None):
    try:
        if connection and connection.is_open:
            connection.close()
            my_logger.info("RabbitMQ connection closed.")
    except Exception as e:
        my_logger.exception("Error closing RabbitMQ connection: %s", str(e))



