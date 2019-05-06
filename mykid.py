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

user = User(app)
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

@app.route("/api/children")
def children():
    children = user.get_children()
    if (len(children) == 0):
        cookie = request.cookies.get(COOKIE, {})
        if (cookie):
            headers = get_header_with_token(cookie)
            res = requests.get(GET_KIDS_API_URL, headers=headers)
            user.set_children(res.json())
            children = user.get_children()
        else:
            return {}
    return jsonify(children)

@app.route("/api/my_day")
def my_day():
    # date = datetime.date.today()
    # date = "2019-04-25"
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
  plannings = user.get_plannings()
  if len(plannings) == 0:
      current_date = datetime.datetime.strptime(request.args.get("date"), "%Y-%m-%d")
      cookie = request.cookies.get(COOKIE, {})
      if (cookie):
        headers = get_header_with_token(cookie)
        for i in range(20): # look 20 weeks ahead
          current_date = current_date + datetime.timedelta(days=7)
          url = "{}/{}/{}".format(WEEK_EVENTS_API_URL, request.args.get("child_id"), str(current_date.date()))
          res = requests.get(url, headers=headers)
          days = res.json()
          if len(days.get("days", [])) > 0:
            for day in days["days"]:
              events = day.get("events", [])
              if len(events) > 0:
                for event in events:
                  if (event.get("navn", "").startswith("Planleggingsdag")):
                    print("Found planning day")
                    print(day["date"])
                    plannings.append(day["date"])
  return jsonify({
    "planning_days": plannings
  })

def get_header_with_token(cookie):
    decoded_cookie = urllib.parse.unquote(cookie)
    auth_user = json.loads(decoded_cookie)
    token = auth_user["token"]
    return {
        "X-Auth-Token": token
    }