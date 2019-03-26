import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

class User(object):
    def __init__(self, app):
        self.app = app
        self.session = None

    def set_session(self, session):
        self.session = session

    def get_session(self):
        return self.session

user = User(app)
login_url = "https://mykid.no/forside/forside/my_brukere_logginn"
show_day_url = "https://mykid.no/_ajax/dagenmin/show_myday"

@app.route('/ping')
def ping():
    return 'Pong!'

@app.route('/api/login', methods=['POST'])
def login():
    if (user.get_session() != None):
        login_data = request.get_json()
        s = requests.session()
        user.set_session(s)
        s.post(login_url, login_data)

    return jsonify({
        "message": "Logget inn"
    })

@app.route("/api/my_day")
def my_day():
    data = {
        "date": "2019-03-21 00:00:00"
    }
    print("after")
    s = user.get_session()
    print(s)
    res = s.post(show_day_url, data)
    print(res.text)
    return res.text