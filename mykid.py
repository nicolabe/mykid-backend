import requests
from flask import Flask, request, jsonify
from myhtmlparser import MyHTMLParser
import urllib.parse
import json

app = Flask(__name__)

class User(object):
    def __init__(self, app):
        self.app = app
        self.token = None
        self.details = {}
        self.children = []

    def set_token(self, token):
        self.token = token

    def get_token(self):
        return self.token

    def set_details(self, details):
        self.details = details

    def get_details(self):
        return self.details

    def set_children(self, data):
        self.children = parse_children(data)

    def get_children(self):
        return self.children

    def parse_children(self, data):
        children = []
        for child in data:
            children.append({
                "avdeling_navn": child["avdeling"]["navn"],
                "avdeling_nummer": child["avdeling"]["telefon"],
                "bursdag": child["birthday"],
                "id": child["id"],
                "img": child["img_src"],
                "navn": "{} {}".format(child["fornavn"], child["etternavn"])
            })
        return children


user = User(app)
LOGIN_API_URL = "https://m.mykid.no/api/authenticate"
GET_KIDS_API_URL = "https://m.mykid.no/api/dashboard/get_kids"
SHOW_DAY_API_URL = "https://m.mykid.no/api/week_events/day_data/110916/"
COOKIE = "mykid"

@app.route('/ping')
def ping():
    return 'Pong!'

@app.route('/api/login', methods=['POST'])
def login():
    if (user.get_token() == None):
        login_data = request.get_json()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8"
        }
        res = requests.post(LOGIN_API_URL, json=login_data, headers=headers)
        data = res.json()
        print(res.json())
        user_data = data["user"]
        user.set_details(user_data)
        user.set_token(user_data.get("token", None))
    else:
        print("Already logged in")

    return jsonify({
        "user": user.get_details()
    })

@app.route("/api/children", methods=['GET'])
def children():
    children = user.get_children()
    if (len(children) != 0):
        cookie = request.cookies.get(COOKIE, {})
        if (cookie):
            decoded_cookie = urllib.parse.unquote(cookie)
            user = json.loads(decoded_cookie)
            token = user["token"]
            headers = {
                "X-Auth-Token": token
            }
            res = requests.get(GET_KIDS_API_URL, headers=headers)
            return jsonify(res.json())
        else:
            return {}
    else:
        return jsonify(children)

@app.route("/api/my_day")
def my_day():
    # s = user.get_session()
    # date = "2019-03-19"
    # res = s.get(show_day_url + date)
    # print(res.text)
    # parser = MyHTMLParser(res.text)
    # data = parser.get_day()
    data = {}
    return jsonify(data)
