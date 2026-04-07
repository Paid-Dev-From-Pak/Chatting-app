from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit
import json, os

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "secret")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

USERS = "users.json"
MESSAGES = "messages.json"
online = {}

def load(f):
    if not os.path.exists(f): return []
    return json.load(open(f))

def save(f,d):
    json.dump(d,open(f,"w"),indent=2)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        u=request.form["username"]
        users=load(USERS)
        if any(x["name"]==u for x in users):
            return "Username exists"
        users.append({"name":u,"contacts":[]})
        save(USERS,users)
        return redirect("/")
    return render_template("register.html")

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]
        users=load(USERS)
        if not any(x["name"]==u for x in users):
            return "User not found"
        session["user"]=u
        return redirect("/chat")
    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session: return redirect("/")
    return render_template("chat.html", user=session["user"])

@app.route("/get_contacts")
def get_contacts():
    users=load(USERS)
    user=next(x for x in users if x["name"]==session["user"])
    return jsonify(user["contacts"])

@app.route("/add_contact", methods=["POST"])
def add_contact():
    data=request.json
    users=load(USERS)
    user=next(x for x in users if x["name"]==session["user"])
    if data["name"] not in user["contacts"]:
        user["contacts"].append(data["name"])
    save(USERS,users)
    return jsonify({"ok":True})

@app.route("/remove_contact", methods=["POST"])
def remove_contact():
    data=request.json
    users=load(USERS)
    user=next(x for x in users if x["name"]==session["user"])
    if data["name"] in user["contacts"]:
        user["contacts"].remove(data["name"])
    save(USERS,users)
    return jsonify({"ok":True})

@app.route("/get_messages/<user2>")
def get_messages(user2):
    user1=session["user"]
    messages=load(MESSAGES)
    filtered=[
        m for m in messages
        if (m["from"]==user1 and m["to"]==user2) or
           (m["from"]==user2 and m["to"]==user1)
    ]
    return jsonify(filtered)

@socketio.on("register_user")
def reg(u):
    online[u]=request.sid

@socketio.on("msg")
def msg(d):
    messages=load(MESSAGES)
    messages.append(d)
    save(MESSAGES,messages)
    if d["to"] in online:
        emit("msg", d, to=online[d["to"]])
    emit("msg", d, to=request.sid)

@socketio.on("typing")
def typing(d):
    if d["to"] in online:
        emit("typing", d, to=online[d["to"]])

if __name__=="__main__":
    socketio.run(app, debug=True)