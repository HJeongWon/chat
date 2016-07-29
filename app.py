
from gevent import monkey; monkey.patch_all()
from flask import (Flask, render_template, request, json, session,
    make_response,
    redirect,
    url_for,)

from gevent import queue
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
app.debug = True

class Room(object):

    
    count = 0
    def __init__(self):
        self.users = set()
        self.messages = []
        self.count = 0
    def backlog(self, size=25):
        return self.messages[-size:]

    def subscribe(self, user):
        if not user in self.users:
            self.users.add(user)
            self.count+=1;

    def add(self, message):
        for user in self.users:
            print (user)
            user.queue.put_nowait(message)
        self.messages.append(message)
    def delete(self,message):
        self.messages.remove(message)

class User(object):

    def __init__(self):
        self.queue = queue.Queue()
# create two rooms
rooms = {
    'sampleroom1': Room(),
    'sampleroom2': Room(),
}

    
    
i = 0

users = {}

@app.route('/')
def choose_name():
    return render_template('choose.html')

@app.route('/create/<uid>',methods=['GET','POST'])
def createRoom(uid):
    name = request.form['roomName']
    global rooms
    rooms[name] = Room()
    
    return  render_template('main.html',uid= uid,
        rooms=rooms.keys())
@app.route('/<uid>')
def main(uid):
    return render_template('main.html',
        uid=uid,
        rooms=rooms.keys()
    )

@app.route('/<room>/<uid>')
def join(room, uid):
    user = users.get(uid, None)
    if not user:
        users[uid] = user = User()
    active_room = rooms[room]
    # limit 4
    if active_room.count >4:
        return '''
        <script>
        alert("maxium 4");
        history.back(0);
        </script>
        '''
    active_room.subscribe(user)
    print ('subscribe', active_room, user)
 
    messages = active_room.backlog()

    return render_template('room.html',
        room=room, uid=uid, messages=messages)
 
@app.route("/put/<room>/<uid>", methods=["POST"])
def put(room, uid):
    user = users[uid]
    room = rooms[room]

    message = request.form['message']
  
    room.add(':'.join([uid, message]))

    return ''


#apply to reload myself
@app.route("/delete/<message>/<room>",methods = ["POST"])
def delete(message,room):
    
    room = rooms[room]
    room.delete(message)
    return '''
    <script>
   history.go(-1);
    </script>
    
    '''
    
    
    
@app.route("/poll/<uid>", methods=["POST"])
def poll(uid):
    try:
        msg = users[uid].queue.get(timeout=10)
    except queue.Empty:
        msg = []
    return json.dumps(msg)

if __name__ == "__main__":
    http = WSGIServer(('', 5000), app)
    http.serve_forever()
