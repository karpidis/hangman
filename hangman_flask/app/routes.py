from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    # Logic to start a new game
    return redirect(url_for('index'))

@app.route('/guess', methods=['POST'])
def make_guess():
    guess = request.form['guess']
    # Logic to process the guess
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)