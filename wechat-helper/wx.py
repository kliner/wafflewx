from wxpy import *
from flask import Flask, request
from jinja2 import Template
import pickle
import os.path

IMG_PATH = '/Users/kliner/github/wechat-helper/wechat-helper/static/qr.png'
app = Flask(__name__, static_url_path='')
global bot
global saved_user_to_name

def load_json():
    return pickle.load(open('saved_user_to_name.pkl', 'rb'))

bot = 0
saved_user_to_name = load_json() if os.path.exists('saved_user_to_name.pkl') else {}

def save_json():
    print('save', saved_user_to_name)
    pickle.dump(saved_user_to_name, open('saved_user_to_name.pkl', 'wb'))

def sort_friends(friends):
    friends = sorted(friends, key=lambda friend: friend.name) # sort according to remark
    friends = sorted(friends, key=lambda friend: friend.remark_name) # sort according to remark
    return friends

list_template = Template(
            '''
            <form action="/s" method="post">
                <input name="k" value=""> &nbsp;
                <input type="submit" value="Search">
            </form>

            <form action="/confirm" method="post">
                {% for f in friends %}
                <input type="checkbox" name="{{ f.name }}" value="true">{{ f.name }} - {{ f.remark_name }} 
                <input name="{{ f.name }}_name" value="{{ saved_user_to_name[f.name] if f.name in saved_user_to_name else '' }}"> <br>
                {% endfor %}
                <textarea name="text">你好，{}，这是一条测试信息</textarea><br>
                <input type="submit" value="Submit">
            </form>
            ''')

@app.route("/s", methods=['GET', 'POST'])
def search():
    key = request.form.get('k')
    friends = bot.friends()
    friends = list(filter(lambda friend: key in friend.name or key in friend.remark_name, friends))
    friends = sort_friends(friends)

    return list_template.render(friends=friends, saved_user_to_name=saved_user_to_name)

@app.route("/")
def home():
    global bot
    home_template = Template( 
            '''
            <script src="https://ajax.aspnetcdn.com/ajax/jQuery/jquery-3.3.1.min.js"></script>
            {% if bot and bot != 1 %}
            <p>Welcome, {{ bot.self.name }} </p>
            <a href='/logout'>logout</a> <br>
            <form action="/s" method="post">
                <input name="k" value=""> &nbsp;
                <input type="submit" value="Search">
            </form>
            {% else %}
            <script>$.ajax("/login")</script>
            <a href='/qr'>login</a> &nbsp; 
            {% endif %}
            ''')
    return home_template.render(bot=bot)


@app.route("/my")
def my():
    friends = bot.friends()
    friends = list(friends)
    friends = sort_friends(friends)

    return list_template.render(friends=friends, saved_user_to_name=saved_user_to_name)

@app.route('/qr')
def qr():
    return '''<img src='qr.png'>'''

@app.route("/login")
def login():
    global bot
    if bot == 0: 
        bot = 1
        bot = Bot(qr_path=IMG_PATH)
        return 'success'
    else:
        return 'logout first'

@app.route("/logout")
def logout():
    global bot
    if bot and bot != 1: bot.logout()
    bot = 0
    return 'success'

@app.route("/confirm", methods=['POST'])
def confirm():
    print(request.form)
    text = request.form.get('text')
    user_to_name = {}
    for key in request.form:
        if key != 'text':
            value = request.form.get(key)
            if value == 'true':
                user_to_name[key] = request.form.get(key + '_name')

    print(user_to_name)

    # join_dct
    for user in user_to_name:
        saved_user_to_name[user] = user_to_name[user]
    save_json()

    user_to_msg = {}
    logs = []
    for key in user_to_name:
        name = user_to_name[key]
        friend = bot.friends().search(key)[0]
        final_msg = (text.replace('{}', name))
        log = ' '.join(('send', final_msg, 'to', friend.name, '-', friend.remark_name))
        user_to_msg[key] = final_msg
        print(log)
        logs += [log]


    template = Template(
            '''
            {% for log in logs %}
            {{ log }} <br>
            {% endfor %}

            <form action="send" method="post">
                {% for u in dct %}
                <input type="hidden" name="{{ u }}" value="{{ dct[u] }}">
                {% endfor %}
                <input type="submit" value="Submit">
            </form>
            '''
            )
    return template.render(dct=user_to_msg, logs=logs)

@app.route("/send", methods=['POST'])
def send():
    print(request.form)
    user_to_msg = {}
    for key in request.form:
        value = request.form.get(key)
        my_friend = bot.friends().search(key)[0]
        print(my_friend, key, value)
        my_friend.send(value)
    return "success"

