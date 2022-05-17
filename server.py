from hashlib import sha512
import json
import time

from flask import Flask, request, redirect
import requests

# Una clase que representa un bloque, que almacena uno o más datos, en la cadena de bloques inmutable
class Block:
    # Uno o más datos (autor, contenido de la publicación y marca de tiempo) se almacenarán en un bloque
    # Los bloques que contienen los datos se generan con frecuencia y se agregan a la cadena de bloques. Estos bloques tienen una identificación única.
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = 0

    # Una función que crea el hash del contenido del bloque
    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha512(block_string.encode()).hexdigest()

# Una clase que representa una lista inmutable de objetos Block están encadenados por hashes, una Blockchain.
class Blockchain:
    # Dificcultad del PoW (Proof-of-Work) de trabajo
    difficulty = 2
    # Uno o más bloques se almacenarán y encadenarán en Blockchain, comenzando por el bloque genisi
    def __init__(self):
        self.unconfirmed_transactions = [] # Estos son datos que aún no se han agregado a Blockchain.
        self.chain = [] # La lista inmutable que representa la Blockchain real
        self.create_genesis_block()

    # Genera bloque de génesis y lo agrega a Blockchain
    # El bloque tiene índice o, anterior_hash de 0 y un hash válido
    def create_genesis_block(self):
        genesis_block = Block(0, [], time.time(), "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    # El bloque verificado se puede agregar a la cadena, agregarlo y devolver True o False
    def add_block(self, block, proof):
        previous_hash = self.last_block.hash
        # Verifique que el campo prvious_hash del bloque que se agregará apunte al hash del último bloque
        # y que el PoW que se proporciona es correcto
        if (previous_hash !=block.previous_hash or not self.is_valid_proof(block, proof)):
            return False
        # Agregar nuevo bloque a la cadena después de la verificación
        block.hash = proof
        self.chain.append(block)
        return True


    # Sirve como interfaz para agregar las transacciones a la cadena de bloques agregándolas
    # y luego averiguar el PoW
    def mine(self):
        # si uncofirmed_transactions está vacío, no se realizará minería
        if not self.unconfirmed_transactions:
            return False
        last_block = self.last_block
        # Creamos un nuevo bloque para añadir la cadena
        new_block = Block(last_block.index + 1, \
                    self.unconfirmed_transactions, \
                    time.time(), \
                    last_block.hash)

        # Ejecución del algoritmo PoW para obtener valida y consenso
        proof = self.proof_of_work(new_block)
        # Se puede agregar un bloque verificado a la cadena (coincidencias de hash anteriores y PoW es válido) y luego agregarlo
        self.add_block(new_block, proof)
        # Vacía la lista de transacciones no confirmadas ya que se agregan a la cadena
        self.unconfirmed_transactions = []
        # Anunciamos a la red una vez que se haya minado un bloque, otros bloques pueden simplemente verificar el PoW y agregarlo a las cadenas respectivas
        announce_new_block(new_block)
        # Devuelve el índice del bloque que se añadió a la cadena.
        return new_block.index
    
    # algoritmo de prueba de trabajo que prueba diferentes valores de nonce para obtener un hash
    # que satisface los criterios de dificultad
    def proof_of_work(self, block):
        block.nonce = 0
        computed_hash = block.compute_hash()
        while not computed_hash.startswith("0" * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        return computed_hash

    # Agregamos una nueva transacción a la lista de transacciones no confirmadas (aún no en la cadena de bloques)
    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    # Comprobamos si la cadena es válida en el momento actual
    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"
        for block in chain:
            block_hash = block.hash
            # Eliminamos los atributos hash para volver a calcular el hash nuevamente usando compute_hash
            delattr(block, "hash")
            if not cls.is_valid_proof(block, block.hash) or previous_hash != block.previous_hash:
                result = False
                break
            block.hash = block_hash
            previous_hash = block_hash
        return result

   # Devuelve el último bloque actual en la cadena de bloques
    @classmethod
    def is_valid_proof(cls, block, block_hash):
        return (block_hash.startswith("0" * Blockchain.difficulty) and block_hash == block.compute_hash())

    @property
    def last_block(self):
        return self.chain[-1]

# Flask web application
app = Flask(__name__)
# La copia del nodo de la cadena de bloques.
blockchain = Blockchain()
# Un conjunto que almacena las direcciones de otros miembros participantes en la red.
peers = set()

# Creamos un nuevo endpoint y vinculamos la función a la URL
@app.route("/new_transaction", methods=["POST"])
# Subimos una nueva transacción
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "ciudad", "content"]
    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)
    return "Success", 201

@app.route("/chain", methods=["GET"])
def get_chain():
    consensus()
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length" : len(chain_data), "chain" : chain_data})
        
# Creamos un nuevo endpoint y vinculamos la función a la URL
@app.route("/mine", methods=["GET"])
# Solicitamos al nodo que extraiga la transacción no confirmada (si corresponde)
def mine_uncofirmed_transactions():
    result = blockchain.mine()
    message = "No hay mensajes que minar";
    if result:
        return redirect('http://127.0.0.1:5000/')
    else:
        return message
    # if not result:
    #     return "There are not transactions to mine"
    # else:
    #     return "Block #{0} has been mined.".format(result)


# Creamos un nuevo endpoint y vinculamos la función a la URL
# Agrega nuevos pares a la red
def register_new_peers():
    nodes = request.get_json()
    if not nodes:
        return "Invalid data", 400
    for node in nodes:
        peers.add(node)
    return "Success", 201


# Creamos un nuevo endpoint y vinculamos la función a la URL
@app.route("/pending_tx")
# Consultas de transacciones no confirmadas
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

# Un algoritmo simple para lograr consenso para mantener la integridad de Blochain
# Si se encuentra una cadena válida más larga, la cadena se reemplaza con ella y devuelve True, de lo contrario, no pasa nada y devuelve false
def consensus():
    global blockchain
    longest_chain = None
    curr_len = len(blockchain.chain)
    # Logre el consenso verificando los campos Json de cada nodo en la red
    for node in peers:
        response = request.get("http://{0}".format(node))
        length = response.json()["length"]
        chain = response.json()["chain"]
        if length > curr_len and blockchain.check_chain_validity(chain):
            curr_len = length
            longest_chain = chain
    if longest_chain:
        blockchain = longest_chain
        return True
    return False


# Creamos un nuevo endpoint y vinculamos la función a la URL
@app.route("/add_block", methods=["POST"])
# Adds a block mined by user to the node's chain
def validate_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"], \
            block_data["transactions"], \
            block_data["timestamp", block_data["previous_hash"]])
    proof = block_data["hash"]
    added = blockchain.add_block(block, proof)
    if not added:
        return "The Block was discarded by the node.", 400
    return "The block was added to the chain.", 201

# Anunciamos a la red una vez que se haya moneado un bloque
def announce_new_block(block):
    for peer in peers:
        url = "http://{0}/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))

app.run(port=8000, debug=True)