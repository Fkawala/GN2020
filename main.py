import time
import random
import string
import click
import threading
import os

from more_itertools import chunked
from flask import Flask, render_template, copy_current_request_context, request
from flask_socketio import SocketIO
from click_shell import shell
from pyfiglet import Figlet


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = '1833GX-L'
socketio = SocketIO(app, async_mode="threading")
clients = []
station_name = "station 1833GX-L"
prompt = f'{station_name} > '
ai_id = 'T22XF'
battery = 100
help = f"La commande \033[91m\033[1m%s\033[0m ne peut pas être exécutée" + \
       f" par {station_name}. Tapez \033[91m\033[1mhelp\033[0m pour obtenir" + \
       f" la liste des commandes disponibles sur {station_name}."


def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

def random_lines(length, text_width=120):
    random_text = random.choices(string.ascii_letters, k=length)
    return (''.join(t) for t in chunked(random_text, text_width))

def intro():
    click.secho(
        "Initialisation des sources d\'entropie",
        blink=False,
        bold=True,
        fg='red')

    for line in random_lines(120, 60):
        click.secho(line, fg='blue')
        time.sleep(.2 * random.random())

    click.secho(
        "Initialisation des sources d\'entropie terminée",
        blink=True,
        bold=True,
        fg='green')

    f = Figlet(font='slant')
    click.echo(f.renderText(station_name))

@app.route('/')
def sessions():
    return render_template('session.html')

@socketio.on('client_connected')
def handle_client_connected_event(username, methods=['GET', 'POST']):
    clients.append({'client_session': request.sid,
                    'client_username': username,
                    'client_ip': request.access_route})

@socketio.on('cryo')
def start_cryo(json, methods=['GET', 'POST']):
    nb_seconds = int(json["nb_seconds"])
    os.system(f"./cryo_cd.sh {nb_seconds}s")

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    msg = f'\n{prompt}Nouveau message de IA-{ai_id}: \033[1m{json["message"]}\033[0m'
    click.secho(msg, bg="blue", fg="black", nl=True)
    click.echo(prompt, nl=False)
    # my_app.shell.cmdloop()
    socketio.emit('my response', json, callback=messageReceived)

@shell(prompt=prompt, intro='Connexion à l\'ordinateur central de la station 1833GX-L ...')
def my_app():
    intro()

@my_app.command(context_settings={"ignore_unknown_options": True})
@click.argument('question', nargs=-1, type=click.STRING)
# @click.argument('query')
def ia(question):
    content = {
        "user_name": "joueur",
        "message": " ".join(question)
    }
    with app.test_request_context('/'):
        socketio.emit('my response', content, callback=messageReceived)

@my_app.command()
@click.pass_context
def etat_installations(ctx):
    pass

@my_app.command()
def cryogen(x):
    pass

@my_app.command()
def status_source_energie(x):
    pass

if __name__ == '__main__':
    import logging
    logging.basicConfig(filename='.error.log',level=logging.ERROR)
    threading.Thread(target=socketio.run, args=(app,)).start()
    time.sleep(1)
    my_app.shell.nocommand = help
    my_app()
    # my_app.nocommand = "La commande %s n'existe pas."
