from flask import Flask
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt
from blockchain import Blockchain
from uuid import uuid4
# Initialize node
node_identifier = str(uuid4()).replace('-', '')
# Initialize the Blockchain
blockchain = Blockchain()
# Initialize the App instance
app = Flask(__name__)
app.config.from_pyfile('config.py')
# Initialize the Database
mysql = MySQL(app)
# Importing decorators from local file( this produce errors: W0614:Unused import dashboard from wildcard import, that are meaningless)
from views import *
# End of views

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000,
                        type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run()
