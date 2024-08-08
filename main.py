import random
import string
import json
import threading
import time
import validators
from flask import Flask, render_template, redirect, url_for, request, flash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flashing messages
short_urls = {}
EXPIRY_TIME = 60  # 1 minute

# Load existing short URLs from file if it exists
try:
    with open("urls.json", "r") as f:
        short_urls = json.load(f)
except FileNotFoundError:
    short_urls = {}

def generate_short_url(length=6):
    chars = string.ascii_letters + string.digits
    short_url = "".join(random.choice(chars) for _ in range(length))
    return short_url

def clean_urls():
    while True:
        time.sleep(EXPIRY_TIME)
        short_urls.clear()
        with open("urls.json", "w") as f:
            json.dump(short_urls, f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form['long_url']
        if not long_url.strip():
            flash("URL field cannot be empty")
            return redirect(url_for('index'))
        
        # Validate the URL
        if not validators.url(long_url):
            flash("Invalid URL format")
            return redirect(url_for('index'))

        short_url = generate_short_url()
        while short_url in short_urls:
            short_url = generate_short_url()
        short_urls[short_url] = {'url': long_url, 'timestamp': time.time()}
        with open("urls.json", "w") as f:
            json.dump(short_urls, f)
        return redirect(url_for('index'))

    return render_template("index.html", short_urls={key: value for key, value in short_urls.items()})

@app.route("/<short_url>")
def redirect_url(short_url):
    entry = short_urls.get(short_url)
    if entry:
        return redirect(entry['url'])
    else:
        return "URL Not Found", 404

@app.route("/delete/<short_url>", methods=["POST"])
def delete_url(short_url):
    if short_url in short_urls:
        del short_urls[short_url]
        with open("urls.json", "w") as f:
            json.dump(short_urls, f)
        flash("URL deleted successfully")
    else:
        flash("URL not found")
    return redirect(url_for('index'))

if __name__ == "__main__":
    clean_thread = threading.Thread(target=clean_urls, daemon=True)
    clean_thread.start()
    app.run(host='0.0.0.0', port=80, debug=True)
