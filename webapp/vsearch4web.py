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
   return 'Jesteś zalogowany.'

@app.route('/logout')
def do_logout() -> str:
   session.pop('logged_in')
   return 'NIE jesteś zalogowany.'


@app.route('/search4', methods=['POST'])
def do_search() -> 'html':
   """Wydobywa przekazane dane; przeprowadza wyszukiwanie; zwraca wyniki."""
   
   @copy_current_request_context
   def log_request(req: 'flask_request', res: str) -> None:
      """Loguje szczegóły żądania sieciowego oraz wyniki."""  
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
   title = 'Oto Twoje wyniki:'
   results = str(search4letters(phrase, letters))
   try:
      t = Thread(target=log_request, args=(request, results))
      t.start()
   except Exception as err:
      print('***** Logowowanie nie powiodło się, błąd: ', str(err))
   return render_template('results.html',
                          the_title=title,
                          the_phrase=phrase,
                          the_letters=letters,
                          the_results=results,)

@app.route('/')
@app.route('/entry')
def entry_page() -> 'html':
   """Wyświetla formularz HMTL tej aplikacji WWW."""
   return render_template('entry.html',
                          the_title='Witamy na stronie internetowej search4letters!')

@app.route('/viewlog')
@check_logged_in
def view_the_log() -> 'html':
   """Wyświetla zawartość pliku logu w postaci tabeli HTML"""
   try:
      with UseDatabase(app.config['dbconfig']) as cursor:
         _SQL = """ select phrase, letters, ip, browser_string,
               results from log"""
         cursor.execute(_SQL)
         contents = cursor.fetchall()
      titles = ('Fraza', 'Litery', 'Adres klienta',
                'Agent użytkownika', 'Wyniki')
      return render_template('viewlog.html',
                             the_title='Widok logu',
                             the_row_titles=titles,
                             the_data=contents,)
   except ConnectionError as err:
      print('Problem z łączaniem z bazą danych, błąd: ', str(err))
   except CredentialsError as err:
      print('Problem z ID użytkownika lub hasłem, błąd: ', str(err))
   except SQLError as err:
      print('Nie poprawne zapytanie, błąd: ', str(err))
   except Exception as err:
      print('Błąd: ', str(err))
   return 'ERROR'   

app.secret_key = 'NigdyNieZgadnieszMojegoTajnegoKlucza'

if __name__ == '__main__':
   app.run(debug=True)
