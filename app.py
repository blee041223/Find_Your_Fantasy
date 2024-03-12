from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3 as sql
import requests

app = Flask(__name__)

DATABASE = 'reviews.db'

def create_database():
    conn = sql.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    comment TEXT NOT NULL
                )
                """)
    
    conn.commit()
    conn.close()

def generate_data():
    conn = sql.connect(DATABASE)
    cur = conn.cursor()

    for i in range(1, 6):
        cur.execute("""INSERT INTO reviews (title, author, rating, comment) VALUES (?, ?, ?, ?)""",
                    (f"Title {i}", f"Author {i}", f"Rating {i}", f"Comment {i}"))
        
    conn.commit()
    conn.close()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sql.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

supported_moods = ['Happy', 'Sad', 'Angry', 'Boring', 'Joy', 'happy', 'sad', 'angry', 'boring', 'joy']

@app.route('/')
def index():
    return render_template('index.html', moods=supported_moods)

@app.route('/recommendations', methods=['Get', 'POST'])
def recommendations():
    selected_mood = request.form['mood']

    emotion_list = {
        'Happy': ['Pleasure', 'Pride', 'AweAwe', 'pleasure', 'pride', 'aweAwe', 'Fantastic', 'fantastic'],
        'Sad': ['Lonely', 'Unhappy', 'Hopeless', 'Gloomy', 'Miserable', 'lonely', 'unhappy', 'hopeless', 'gloomy', 'miserable'],
        'Angry': ['Annoyed', 'Frustrated', 'Bitter', 'Mad', 'Insulted', 'annoyed', 'frustrated', 'bitter', 'mad', 'insulted', 'mad'],
        'Boring': ['Worried', 'Stressed', 'Nervous', 'worried', 'stressed', 'nervous'],
        'Joy': ['Amusement', 'Excitement', 'Ecstasy', 'amusement', 'excitement', 'ecstasy']
    }
    
    if selected_mood not in supported_moods:

        for emotion in emotion_list.keys():
            for word in emotion_list[emotion]: 
                if(word == selected_mood): 
                    return render_template('error.html', message = emotion)

        return render_template('error2.html')
    
    categories = {
        'Happy': ['romance', 'humor', 'adventure'],
        'Sad': ['tragedy', 'drama', 'emotional'],
        'Angry': ['thriller', 'suspense', 'revenge'],
        'Boring': ['mystery', 'horror', 'psychological'],
        'Joy': ['inspirational', 'self-help', 'uplifting'], 
        'happy': ['romance', 'humor', 'adventure'], 
        'sad': ['tragedy', 'drama', 'emotional'],
        'angry': ['thriller', 'suspense', 'revenge'],
        'boring': ['mystery', 'horror', 'psychological'],
        'joy': ['inspirational', 'self-help', 'uplifting'],
    }

    recommended_books = []
    for category in categories[selected_mood]:
        url = f'https://www.googleapis.com/books/v1/volumes?q=subject:{category}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            books = data.get('items', [])
            recommended_books.extend(books)

    formatted_recommendations = []
    for book in recommended_books:
        title = book['volumeInfo']['title']
        authors = book['volumeInfo'].get('authors', ['Unknown Author'])
        description = book['volumeInfo'].get('description', 'No description available')
        cover_image_url = book['volumeInfo']['imageLinks']['thumbnail'] if 'imageLinks' in book['volumeInfo'] else ''
        purchase_link = book['saleInfo'].get('buyLink', '#')
        formatted_recommendations.append({
            'title': title,
            'authors': ', '.join(authors),
            'description': description,
            'cover_image_url': cover_image_url,
            'purchase_link': purchase_link
        })

    return render_template('recommendations.html', mood=selected_mood, recommendations=formatted_recommendations)

@app.route('/input_review')
def input_review():
    return render_template('input_review.html')

@app.route('/submit_review', methods=['GET', 'POST'])
def submit_review():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        rating = request.form['rating']
        comment = request.form['comment']

        print(title)
        print(author)
        print(rating)
        print(comment)

        db = get_db()
        db.execute('INSERT INTO reviews (title, author, rating, comment) VALUES (?, ?, ?, ?)',
                [title, author, rating, comment])
        db.commit()

    return redirect(url_for('reviews'))

@app.route('/reviews')
def reviews():
    db = get_db()
    cursor = db.execute('SELECT * FROM reviews')
    reviews = cursor.fetchall()
    return render_template('reviews.html', reviews=reviews)

if __name__ == '__main__':
    create_database()
    # generate_data()
    app.run(debug=True)
