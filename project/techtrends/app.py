import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

total_conn = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    try:
        connection = sqlite3.connect('file:database.db?mode=rw',uri=True)
        connection.row_factory = sqlite3.Row
        global total_conn
        total_conn = total_conn + 1
        return connection
    except sqlite3.OperationalError as e:
        app.logger.debug(e.args[0])
        return ''

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get total posts
def get_post_count():
    connection = get_db_connection()
    count = connection.execute('SELECT COUNT(id) FROM posts').fetchone()[0]
    connection.close()
    return count

# Check posts table exists
def check_db():
    conn = get_db_connection()
    if conn == '':
        return 'error'
    else:
        try:
            conn.execute('SELECT * FROM posts')
            return 'success'
        except sqlite3.OperationalError as e:
            app.logger.debug(str(e.args[0]))
            return 'error'

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

@app.route('/metrics')
def metrics():
    response = jsonify(
        db_connection_count=str(total_conn),
        post_count=str(get_post_count())
    )
    return response

# Health endpoint
@app.route('/healthz')
def healthz():
    response = ''
    code = ''
    check = check_db()
    if check == 'error':
        response = jsonify(
            result='ERROR - unhealthy'
        )
        code = 500

    elif check == 'success':
        response = jsonify(
            result='OK - healthy'
        )
        code = 200
    
    return response, code

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('Article is not found!')
      return render_template('404.html'), 404
    else:
      title = str(post[2])
      app.logger.info('Article "'+title+'" is retrieved.')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug('The About Us page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info('Article "'+title+'" is created.')
            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
