#THIS VERSION FORCES ERROR WHEN OPENING THE LOG

from flask import Flask, render_template, request, escape, session, copy_current_request_context
from vsearch import search4letters
from threading import Thread

from checker import check_logged_in
from DBcm import UseDatabase, ConnectionError, CredentialsError, SQLError

app = Flask(__name__)

app.config['dbconfig'] = { 'host': '127.0.0.1',
                           'user': 'youruser',
                           'password': 'yourpassword',
                           'database': 'yourDB', }

@app.route('/login')
def do_login() -> str:
   session['logged_in'] = True
   return 'You are logged in.'

@app.route('/logout')
def do_logout() -> str:
   session.pop('logged_in')
   return 'You are NOT logged in.'


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
   """Uses given data to search, returns result"""
   
   @copy_current_request_context
   def log_request(req: 'flask_request', res: str) -> None:
      """Saving given query and results in log."""  
      with UseDatabase(app.config['dbconfig']) as cursor:   
         _SQL = """insert into log
                  (phrase, letters, ip, browser_string, results)
                  values
                  (%s, %s, %s, %s, %s)"""
         cursor.execute(_SQL, (req.form['phrase'],
                               req.form['letters'],
                               req.remote_addr,
                               req.user_agent.browser,
                               res, ))
      
   phrase = request.form['phrase']
   letters = request.form['letters']
   title = 'Those are your results:'
   results = str(search4letters(phrase, letters))
   try:
      t = Thread(target=log_request, args=(request, results))
      t.start()
   except Exception as err:
      print('***** Login failed, error: ', str(err))
   return render_template('results.html',
                          the_title=title,
                          the_phrase=phrase,
                          the_letters=letters,
                          the_results=results,)

@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
   """Prints HTML formula"""
   return render_template('entry.html',
                          the_title='Welcome on website: search4letters!')

@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
   """Prints the log in HTML table"""
   try:
      with UseDatabase(app.config['dbconfig']) as cursor:
         _SQL = """ select phrase, letters, ip, browser_string,
               results from log"""
         cursor.execute(_SQL)
         contents = cursor.fetchall()
      titles = ('Phrase', 'Letters', 'IP',
                'User agent', 'Results')
      return render_template('viewlog.html',
                             the_title='Log view',
                             the_row_titles=titles,
                             the_data=contents,)
   except ConnectionError as err:
      print('Error with connecting to database, error: ', str(err))
   except CredentialsError as err:
      print('Wrong ID or password, error: ', str(err))
   except SQLError as err:
      print('Query Error: ', str(err))
   except Exception as err:
      print('Error: ', str(err))
   return 'ERROR'   

app.secret_key = 'SuperSecretKey'

if __name__ == '__main__':
   app.run(debug=True)
