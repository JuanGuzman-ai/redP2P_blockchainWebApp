import datetime
import json

import requests
from flask import render_template, redirect, request, url_for

from app import app

# Variable para el nodo
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
# Almacenamos todas publicaciones del nofo
posts = []

# Obtenemos los datos del end poitn de la cadena/nodo, analizamos los datos y los guardamos localmente
def fetch_posts():
    get_chain_address = "{0}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content.decode("utf-8"))
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)
        global posts
        posts = sorted(content, key=lambda k: k["timestamp"], reverse=True)
    return redirect('/') 

# Creamos un nuevo punto final para vincular la función a la URL
@app.route("/")
def index():
    fetch_posts()
    return render_template("index.html", \
        title="Blockchain Proyecto",\
        subtitle = "Envio de cadenas", \
        node_address = CONNECTED_NODE_ADDRESS, \
        posts = posts,\
        readable_time = timestamp_to_string)
    app.logger(fetch_posts())

# Creamos un nuevo endpoint y se vincula la función a la URL
@app.route("/submit", methods=["POST"])
# Endpoint para crear la nueva transacción
def submit_textarea():
    author = request.form["author"]
    ciudad = request.form["ciudad"]
    post_content = request.form["content"]

    post_object = {
        "author": author,
        "ciudad": ciudad,
        "content": post_content,
    }

    # Subimos la nueva transacción
    new_tx_address = "{0}/new_transaction".format(CONNECTED_NODE_ADDRESS)
    requests.post(new_tx_address, json=post_object, headers={"Content-type" : "application/json"})
    return redirect("/")


# Convertimos el timestamp a string
def timestamp_to_string(unix_time):
    return datetime.datetime.fromtimestamp(unix_time).strftime("%H:%M")
