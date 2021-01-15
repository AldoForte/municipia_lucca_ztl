#!/usr/bin/python3

from flask import Flask, make_response, request, current_app, Response
import socket
import json

from flask.ext.cors import CORS, cross_origin

import RPi.GPIO as GPIO
from time import sleep
import configparser

app = Flask(__name__)
cors = CORS(app)

config = configparser.ConfigParser()
config.read('/home/sensorid/verona_mercato/config_old.cfg')

IP_HOST = config['gate']['ip_address']
SRV_SOCKET_PORT = config['gate']['sock_port']

print("SERVER ADDRESS: {0}".format(IP_HOST));
print("SERVER PORT: {0}".format(SRV_SOCKET_PORT));

RELAY_01 = int(config['gate']['relay_1'])
RELAY_02 = int(config['gate']['relay_2'])

RELAY_SBARRA = int(RELAY_01)
RELAY_DISPLAY = int(RELAY_02)

GPIO.setwarnings(False)

# Pin setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_SBARRA, GPIO.OUT)
GPIO.setup(RELAY_DISPLAY, GPIO.OUT)

ON = 1
OFF = 0


# -------------------------------------------------------------------
# A P E R T U R A   S B A R R A
# -------------------------------------------------------------------
def apri_sbarra():
    #GPIO.output(RELAY_SBARRA, 1)
    #sleep(1)
    #GPIO.output(RELAY_SBARRA, 0)
    return "ok"

# -------------------------------------------------------------------
#  BLOCCA SBARRA APERTA
# -------------------------------------------------------------------
def blocca_sbarra_aperta():
    #GPIO.output(RELAY_SBARRA, 1)
    #GPIO.output(RELAY_DISPLAY,0)
    pass

# -------------------------------------------------------------------
#  BLOCCA SBARRA CHIUSA
# -------------------------------------------------------------------
def blocca_sbarra_chiusa():
	print("ESEGUO COMANDO blocca_sbarra_chiusa")
	#GPIO.output(int(RELAY_SBARRA), 0)
	print("GPIO.output(int(RELAY_SBARRA), 0)")
	#GPIO.output(int(RELAY_DISPLAY), 0)
	print("GPIO.output(int(RELAY_DISPLAY), 0)")

# -------------------------------------------------------------------
#  INVIO MESSAGGIO TRAMITE SOCKET
# -------------------------------------------------------------------
def invia_msg_sock_server(messaggio):
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect((IP_HOST, int(SRV_SOCKET_PORT)))
    clientsocket.send(messaggio.encode())
    sleep(0.2)
    clientsocket.send('X'.encode())

# -------------------------------------------------------------------
#  SCRIVE STATO SU FILE
# -------------------------------------------------------------------
def scrivi_stato_gate(stato):
	global config
	config.set('gate','stato', stato)

	with open('/home/sensorid/gate_app/source_code/config_old.cfg', 'w') as configfile:
		config.write(configfile)

	print("Scrittura eseguita")


# --------------------------------------------------------------------
# LETTURA DELLO STATO DEL GATE
# --------------------------------------------------------------------
def leggi_stato_gate():
	global config
	stato_gate = config['gate']['stato']
	print(stato_gate)
	return stato_gate


# -------------------------------------------------------------------
# L O G I N   P A G E
# -------------------------------------------------------------------
@app.route('/')
def login():
    return 'SERVER OK!'


@app.route('/attiva/<stato>')
def attiva_gate(stato):
    scrivi_stato_gate(stato)
    return stato


# -------------------------------------------------------------------
# D I S C O V E R Y   C O M M A N D S   -   J S O N
# -------------------------------------------------------------------
@app.route('/discovery_cmds', methods=['POST'])
@cross_origin()
def json_controllo_sbarra():

    post_data = ""

    if request.method == "POST":

        try:

            print("DATA: {0}".format(request.data))

            rcv_data = request.json
            post_data = json.loads(json.dumps(rcv_data))

            print("REQUEST JSON : {0}".format(rcv_data))

            # legge il comando inviato al discoverygate
            comando = post_data['cmd']

            print("POST DATA : {0}".format(comando))

            risposta = '{{"risposte" : [{{"comando ricevuto" : "{0}"}}]}}'.format(comando)

            if comando == "apri_sbarra":
                apri_sbarra()
                risposta = '{{"risposte" : [{{"comando_ricevuto" : "{0}"}}, {{"comando_eseguito" : "ok"}}]}}'.format(comando)
                print(risposta)

            elif comando == "accesso_aperto":
                blocca_sbarra_aperta()
                risposta = '{{"risposte" : [{{"comando_ricevuto" : "{0}"}}, {{"comando_eseguito" : "ok"}}]}}'.format(comando)
                invia_msg_sock_server('FS_AP')
                invia_msg_sock_server('X')
                scrivi_stato_gate('FS_AP')
                print(risposta)


            elif comando == "accesso_chiuso":
                blocca_sbarra_chiusa()
                risposta = '{{"risposte" : [{{"comando_ricevuto" : "{0}"}}, {{"comando_eseguito" : "ok"}}]}}'.format(comando)
                invia_msg_sock_server('FS_CH')
                invia_msg_sock_server('X')
                scrivi_stato_gate('FS_CH')
                print(risposta)

            elif comando == "attiva_gate":
                print("ricevo comando {0}:".format(comando))
                blocca_sbarra_chiusa() # Chiude la barriera
                risposta = '{{"risposte" : [{{"comando_ricevuto" : "{0}"}}, {{"comando_eseguito" : "ok"}}]}}'.format(comando)
                invia_msg_sock_server('OK')
                invia_msg_sock_server('X')
                scrivi_stato_gate('OK')
                print(risposta)

            elif comando == "stato_gate":
                stato = leggi_stato_gate()
                risposta = '{{"stato" : "{0}"}}'.format(stato)


            else:
                risposta = '{{"risposte" : [{{"comando_ricevuto" : "{0}"}}, {{"comando_eseguito" : "no - comando sconosciuto"}}]}}'.format(comando)
                print(risposta)

            headers = {'Access-Control-Allow-Origin': '*'}

            #resp = make_response(risposta, 200)
            #resp.headers.extend({'Access-Control-Allow-Origin': '*'})

            resp = Response(response=risposta, status=200, mimetype="application/json")

            return resp

        except Exception as e:

            risposta='{{"errore":"{0}"}}'.format(e)
            resp = Response(response=risposta, status=200, mimetype="application/json")
            return resp

    return "xxx"
# -------------------------------------------------------------------


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)
