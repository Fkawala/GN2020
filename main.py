import time
import random
import string
import click
import threading
import os
import pickle
import tqdm

from collections import ChainMap
from more_itertools import chunked
from flask import Flask, render_template, copy_current_request_context, request
from flask_socketio import SocketIO
from click_shell import shell
from pyfiglet import Figlet


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = '1833GX-L'
app.config['JSON_AS_ASCII'] = False
socketio = SocketIO(app, async_mode="threading")
clients = []
last_action = {"timestamp": time.time()}
slots = {
    "endommagé":
        {'LAX-1', 'PAX-22', 'OAX-30', 'LAX-4', 'LAX-51',
         'LAX-6', 'LAX-07', 'LAX-81', 'LAX-99'},
    "détruit": {'LAX-10'},
    "occupé": set(),
    "disponible": {'LAX-11', 'LAX-0', 'LAX-7', 'KAX-2', 'LAX-15'}}
slots_status = dict(ChainMap(*[{slot: status for slot in slots} for (status, slots) in slots.items()]))
cryo = {}
station_name = "station 1833GX-L"
prompt = f'{station_name} > '
ai_id = 'T22XF'
battery = {"type": "batterie", "niveau": 100, "niveau_max": 100}
help = f"La commande \033[91m\033[1m%s\033[0m ne peut pas être exécutée" + \
       f" par {station_name}. Tapez \033[91m\033[1mhelp\033[0m pour obtenir" + \
       f" la liste des commandes disponibles sur {station_name}."

def load_slots(path=""):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None

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

    for line in random_lines(1800, 60):
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
    os.system(f"/home/pi/cryo_cd.sh {nb_seconds}s")

@socketio.on('cmd')
def start_cryo(json, methods=['GET', 'POST']):
    command = json["command"]
    os.system(command)

@socketio.on('power')
def power(json, methods=['GET', 'POST']):
    battery["niveau"] += int(json["power_qty"])

@socketio.on('slots')
def update_slots(json, methods=['GET', 'POST']):
    name = json["slot_name"].strip()
    action = json["action"].encode('latin-1').decode('utf-8').strip().lower()

    try:
        slots[slots_status[name]].remove(name)
        slots[action].add(name)
        slots_status.update(dict(ChainMap(*[{slot: status for slot in slots} for (status, slots) in slots.items()])))
        with open(".slots", "wb") as f:
            pickle.dump(slots, f)
    except Exception:
        click.secho(
            f"Le changement d'état pour la source {name} " + \
            f"à échoué. Contactez l'IA {ai_id}",
            fg='red', bg='white', blink=True)
        click.echo(prompt, nl=False)

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    msg = f'\n{prompt}Nouveau message de IA-{ai_id}: \033[1m{json["message"]}\033[0m'
    click.secho(msg, bg="blue", fg="black", nl=True)
    click.echo(prompt, nl=False)
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
@click.option('--priorite', default=10, help='Vitesse de calcul', type= click.IntRange(min=0, max=20))
@click.option('--source', prompt='état à des sources vérifier',
              help='détruit, disponible, endommagé, occupé, disponible')
def etat_installations(priorite, source):
    if click.confirm('Confirmez l\'évaluation des installations'):
        battery["niveau"] -= .5
        with click.progressbar(range(20 - priorite)) as bar:
            for _ in bar:
                time.sleep(.3 * random.random())

        if source not in slots:
            click.secho(
                f"{source} n'est pas valide",
                blink=False,
                bold=True,
                fg='red')
        else:
            msg = "\n ".join(slots[source])
            click.secho(f"Les installations:\n {msg} \nsont '{source}'", fg='green')


@my_app.command()
@click.option('--quantite', default=1, help='Taux de proteines.')
def cryogen_proteines(quantite):
    battery["niveau"] -= .2
    cryo["proteines"] = quantite
    click.secho(f"Le taux de proteines lors du cryogen est réglé à '{quantite}'", fg='green')

@my_app.command()
@click.option('--vitesse', help='Vitesse de synchronisation du cortex en hertz.', type= click.INT)
def cryogen_cortex(vitesse):
    battery["niveau"] -= .2
    cryo["vitesse_synchro_cortex"] = vitesse
    fg = "red" if (vitesse < 1337) else "green"
    click.secho(f"La vitesse de synchronisation du cortex réglé à '{vitesse}'", fg=fg)


@my_app.command()
def status_cryo():
    battery["niveau"] -= .4
    msg = "vide"
    if len(cryo):
        msg = "\n".join([f"(*) {k} est réglé à {v}" for k,v in cryo.items()])
    click.secho(f"Le réglage du cryo process est:\n{msg}", fg='green')


@my_app.command()
def status_energie():
    if click.confirm('Confirmez l\'évaluation de l\'énergie restante'):
        battery["niveau"] -= .2
        msg = f"L'énergie est connecté sur {battery['type']}"
        click.echo(msg)
        tqdm.tqdm(total=battery["niveau_max"], initial=battery["niveau"])

@my_app.command()
@click.option('--priorite', default=10, help='Vitesse d\'installation', type= click.IntRange(min=0, max=20))
@click.option('--emplacemeent', prompt='emplacement de la sources à installer',
              help='LAX-000')
def installer_source_energie():
    battery["niveau"] -= 30
    with click.progressbar(range(20 - priorite)) as bar:
        for _ in bar:
            time.sleep(.3 * random.random())

    if emplacement in slots["disponible"]:
        battery["type"] = emplacemeent
        click.secho(f"La source {emplacemeent} est installée'", fg='green')
        battery["niveau"] += min(30, 150 * random.random())
        battery["niveau_max"] += max(battery["niveau"], battery["niveau_max"])
    else:
        click.secho(f"L'emplacement {emplacemeent} n'est pas disponible'", bg='red', fg="black", bold=True, blink=True)



if __name__ == '__main__':
    import logging
    saved_slots = load_slots(".slots")
    if saved_slots is not None:
        slots = saved_slots
        slots_status = dict(ChainMap(*[{slot: status for slot in slots} for (status, slots) in slots.items()]))
    logging.basicConfig(filename='.error.log', level=logging.DEBUG)
    threading.Thread(target=socketio.run, kwargs={"app":app, "host": "0.0.0.0"}).start()
    time.sleep(1)
    my_app.shell.nocommand = help
    my_app()
    # my_app.nocommand = "La commande %s n'existe pas."
