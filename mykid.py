import requests
from flask import Flask, request, jsonify
import urllib.parse
import json
import datetime

app = Flask(__name__)

class User(object):
    def __init__(self, app):
        self.app = app
        self.token = None
        self.details = {}
        self.children = []
        self.plannings = []

    def set_token(self, token):
        self.token = token

    def get_token(self):
        return self.token

    def set_details(self, details):
        self.details = details

    def get_details(self):
        return self.details

    def set_children(self, data):
        for child in data["kids"]:
            self.children.append({
                "department": {
                    "name": child["avdeling"]["navn"],
                    "phone": child["avdeling"]["telefon"]
                },
                "birthday": child["birthday"],
                "id": child["id"],
                "img": child["img_src"],
                "name": "{} {}".format(child["fornavn"], child["etternavn"])
            })

    def get_children(self):
        return self.children

    def set_plannings(self, plannings):
        self.plannings = plannings

    def get_plannings(self):
        return self.plannings


class CustomError(Exception):
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

users = {}
LOGIN_API_URL = "https://m.mykid.no/api/authenticate"
GET_KIDS_API_URL = "https://m.mykid.no/api/dashboard/get_kids"
SHOW_DAY_API_URL = "https://m.mykid.no/api/week_events/day_data"
WEEK_EVENTS_API_URL = "https://m.mykid.no/api/week_events"
COOKIE = "mykid"

@app.route('/ping')
def ping():
    return 'Pong!'

@app.route('/api/login', methods=['POST'])
def login():
    cookie = request.cookies.get(COOKIE, {})
    user = get_user(cookie)
    if not (user):
        user = User(app)
        login_data = request.get_json()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8"
        }
        res = requests.post(LOGIN_API_URL, json=login_data, headers=headers)
        data = res.json()
        user_data = data["user"]
        user.set_details(user_data)
        user.set_token(user_data.get("token", None))
        users[user.get_token()] = user
    else:
        print("Already logged in")
    return jsonify({
        "user": user.get_details()
    })

@app.route("/api/children")
def children():
    cookie = request.cookies.get(COOKIE, {})
    user = get_user(cookie)
    if not (user):
        raise CustomError('Ingen bruker funnet, logg ut og inn igjen', status_code=400)
    children = user.get_children()
    if (len(children) == 0):
        if (cookie):
            headers = get_header_with_token(cookie)
            res = requests.get(GET_KIDS_API_URL, headers=headers)
            user.set_children(res.json())
            children = user.get_children()
        else:
            return jsonify({
                "status_code": 400,
                "message": "No cookie found, try logging out and back again"
            })
    return jsonify(children)

@app.route("/api/my_day")
def my_day():
    url = "{}/{}/{}".format(SHOW_DAY_API_URL, request.args.get("child_id"), request.args.get("date"))
    cookie = request.cookies.get(COOKIE, {})
    if (cookie):
        headers = get_header_with_token(cookie)
        res = requests.get(url, headers=headers)
        return jsonify(res.json())
    else:
        return {}

@app.route("/api/plannings")
def plannings():
    cookie = request.cookies.get(COOKIE, {})
    user = get_user(cookie)
    plannings = user.get_plannings()
    if len(plannings) == 0:
        current_date = datetime.datetime.strptime(request.args.get("date"), "%Y-%m-%d")
        if (cookie):
            headers = get_header_with_token(cookie)
            for i in range(26): # look 26 weeks ahead
                url = "{}/{}/{}".format(WEEK_EVENTS_API_URL, request.args.get("child_id"), str(current_date.date()))
                res = requests.get(url, headers=headers)
                days = res.json()
                if len(days.get("days", [])) > 0:
                    for day in days["days"]:
                        events = day.get("events", [])
                        if len(events) > 0:
                            for event in events:
                                if (event.get("navn", "").startswith("Planleggingsdag")):
                                    plannings.append(day["date"])
                current_date = current_date + datetime.timedelta(days=7)
    return jsonify({
        "planning_days": plannings
    })

@app.errorhandler(CustomError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def get_user(cookie):
    if not (cookie):
        return None
    decoded_cookie = urllib.parse.unquote(cookie)
    auth_user = json.loads(decoded_cookie)
    token = auth_user["token"]
    return users.get(token, None)

def get_header_with_token(cookie):
    decoded_cookie = urllib.parse.unquote(cookie)
    auth_user = json.loads(decoded_cookie)
    token = auth_user["token"]
    return {
        "X-Auth-Token": token
    }