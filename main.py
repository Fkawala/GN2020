from flask import Flask, render_template, copy_current_request_context, request
from flask_socketio import SocketIO
from json import dumps
import click
from click_shell import shell
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app, async_mode="threading")
clients = []

@app.route('/')
def sessions():
    return render_template('session.html')

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('client_connected')
def handle_client_connected_event(username, methods=['GET', 'POST']):
    clients.append({'client_session': request.sid,
                    'client_username': username,
                    'client_ip': request.access_route})
    print(clients)

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('my-app> Message de AI' + json["message"])
    socketio.emit('my response', json, callback=messageReceived)

@shell(prompt='my-app > ', intro='Starting my app...')
def my_app():
    pass

@my_app.command()
@click.argument('query')
def search(query):
    with app.test_request_context('/'):
        socketio.emit('my response', {"user_name": "joueur gn", "message": query}, callback=messageReceived)

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='error.log',level=logging.DEBUG)
    threading.Thread(target=socketio.run, args=(app,)).start()
    my_app()
