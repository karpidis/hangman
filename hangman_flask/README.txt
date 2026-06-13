HANGMAN FLASK APP
=================

SETUP
-----
1. Extract this zip into your Projects folder
2. Copy your db/ folder (from the terminal version) into hangman_web/
3. Copy your background image into:  static/images/bg.png
4. Install Flask:  pip install flask
5. Run:  python app.py
6. Open browser at:  http://127.0.0.1:5000

FOLDER STRUCTURE
----------------
hangman_web/
  app.py                 <- main Flask app
  requirements.txt
  README.txt
  templates/
    index.html           <- language + name selection screen
    game.html            <- game screen
  static/
    css/
      game.css           <- all styling
    images/
      bg.png             <- PUT YOUR BACKGROUND IMAGE HERE
  db/                    <- COPY YOUR db/ FOLDER HERE
