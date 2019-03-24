# importing my files
from app import app, mysql, blockchain, node_identifier
from forms import RegisterForm, ArticleForm
# end of importing my files
# importing remote modules
from flask import render_template, jsonify, request, flash, redirect, url_for, session, logging
from passlib.hash import sha256_crypt
from functools import wraps
# end of importing of remote modules


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'alert')
            return redirect(url_for('login'))
    return wrap


def mineBlock():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    minedBlock = {
        'message': "Congrats you mined and attached block",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return minedBlock


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/mine')
def mine():
    flash("You can start mining new block by clicking button above.", 'secondary')
    return render_template('mine.html')


@app.route('/startmining', methods=['POST'])
def start_mining():
    minedblock = mineBlock()
    flash(str(minedblock['message'])+" "+str(minedblock['index'])+'. Proof that allowns everyone to confirm your work :' +
          str(minedblock['proof'])+'. Previous hash: ' + str(minedblock['previous_hash']), 'success')
    return redirect(url_for('mine'))


@app.route('/explorer')
def explorer():
    explore = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return render_template('explorer.html', explored=explore)


@app.route('/tx')
def transaction():
    return render_template('transaction.html')


@app.route('/donate')
def donate():
    return render_template('donate.html')


@app.route('/news')
def news():
        # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('news.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('news.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        # Create cursor
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password) values(%s,%s,%s,%s)",
                    (name, email, username, password))
        # commit to DB
        mysql.connection.commit()
        # close conection
        cur.close()

        flash("You are now registered and can log in ", 'success')

        redirect(url_for('index'))
        return render_template('register.html', form=form)
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Ger form fields
        username = request.form['username']
        password_candidate = request.form['password']
        # create cursor
        cur = mysql.connection.cursor()
        # get user by username
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s",  [username])

        if result > 0:
            # get stored hash
            data = cur.fetchone()
            password = data['password']

            # compare passwords
            if sha256_crypt.verify(password_candidate, password):
                # everything went fine
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Password does not match.'
                return render_template('login.html', error=error)
            # close conection
            cur.close()

        else:
            error = 'Username not found.'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # create cursor
        cur = mysql.connection.cursor()

        # execute
        cur.execute('INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)',
                    (title, body, session['username']))
        # commit to DB
        mysql.connection.commit()
        # close
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute(
            "UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))
        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now loged out', 'success')
    return redirect(url_for('login'))

# Delete Article


@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()


@app.route('/article/<string:id>')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    cur.execute("SELECT * FROM articles Where ID=%s", [id])

    article = cur.fetchone()
    return render_template('article.html', article=article)
