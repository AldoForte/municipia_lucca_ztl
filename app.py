#!/usr/bin/python3.4

print("Configuration in progress, please wait...")
import os
import configparser
import serial
import time
import requests
from time import sleep
# import RPi.GPIO as GPIO
import json
import datetime
import sqlite3
import threading
import socket
import select

from models.varchi_put_letture import VarchiPutLetture
from models.configuration import Configuration
from modules import database

CONFIG_FILE_NAME = "configuration.ini"

config = configparser.ConfigParser()
config_path = os.path.dirname(os.path.realpath(__file__)) + str(os.path.sep) + CONFIG_FILE_NAME


config.read(config_path)

ID_GATE = config['gate']['id']

TIPO = config['gate']['tipo']
stato_gate = config['gate']['stato']
DB_FILE_NAME = config['db']['db_name']
db_path =  os.path.dirname(os.path.realpath(__file__)) + str(os.path.sep) + DB_FILE_NAME

configuration = Configuration()
configuration.loadConfiguration(config_path)


#
ON = 1
OFF = 0


DEBUG_MODE_JSON = False

ultimo_tag_letto = ""
tmstp_ultima_lettura = 0
ser = None

CONNECTION_LIST=[]

# -------------------------------------------------------------------
# Attiva/Disattiva  la lettura spontanea del gate
# -------------------------------------------------------------------
def attivazione_lettura_gate(stato):
    global scanning


    ser.flushOutput()
    ser.flushInput()

    cmd = ""

    if (stato == OFF):
        cmd = '$0C040100\r\n'.encode()
        scanning = False

    if (stato == ON):
        cmd = '$0C040101\r\n'.encode()
        scanning = True

    try:
        ser.write(cmd)

        sleep(0.5)

        ser.flushOutput()
        ser.flushInput()
        print("ATTIVAZIONE LETTURA GATE")

    except Exception as e:
        print("[ ERR ] {0}".format(str(e)))
        print('[ FNC ] attivazione_lettura_gate("{0}")'.format(stato))
        attivazione_lettura_gate(OFF)
# -------------------------------------------------------------------

# -------------------------------------------------------------------
#  I N I Z I A L I Z Z A Z I O N E
# -------------------------------------------------------------------
def discoverygate_init():
    """
    Inizializzazione del gate.
    Gestione dello stato
    Porta seriale

    :return 0
    """

    SERIAL_PORT = config['serial_port']['port']
    SERIAL_BAUDRATE = config['serial_port']['baudrate']
    SERIAL_BYTESIZE = config['serial_port']['bytesize']
    SERIAL_STOPBITS = config['serial_port']['stopbits']
    SERIAL_PARITY = config['serial_port']['parity']
    SERIAL_TIMEOUT = config['serial_port']['timeout']

    global ser
    ser = serial.Serial(SERIAL_PORT, baudrate=SERIAL_BAUDRATE, bytesize= int(SERIAL_BYTESIZE), stopbits=int(SERIAL_STOPBITS), parity='N', timeout=1)
    ser.close()
    ser.open()
    ser.flushOutput()

    attivazione_lettura_gate(ON)
    ser.flushOutput()
    ser.flushInput()

    print("\n"*100)

    print("  _____ ______ _   _  _____  ____  _____    _____ _____")
    print(" / ____|  ____| \ | |/ ____|/ __ \|  __ \  |_   _|  __ \\")
    print("| (___ | |__  |  \| | (___ | |  | | |__) |   | | | |  | |")
    print(" \___ \|  __| | . ` |\___ \| |  | |  _  /    | | | |  | |")
    print(" ____) | |____| |\  |____) | |__| | | \ \   _| |_| |__| |")
    print("|_____/|______|_| \_|_____/ \____/|_|  \_\ |_____|_____/")
    print("----------------------------*  Proximity Smart Solutions\n\n")

    print("DISCOVERYGATE READY !!!")
    print("Ver: 002")
    print("FOR: Kiunsys")
    print("")
    print("ID GATE: {0}".format(ID_GATE))
    print("START AT: {0}".format( datetime.datetime.now().strftime("%y-%m-%d %H-%M-%S")))

# --------------------------------------------- discovery_init() END

# ------------------------------------------------------------------
#
# ------------------------------------------------------------------
def socket_comm():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 5000))
    server_socket.listen(5)

    CONNECTION_LIST.append(server_socket)

    print(":> SERVER IS READY !!!")

    while 1:
        read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])

        for sock in read_sockets:

            if sock == server_socket:

                sockfd, addr = server_socket.accept()
                CONNECTION_LIST.append(sockfd)
                print("Client (%s, %s) connesso" % addr)

            else:
                try:
                    data = sock.recv(4096)
                except:
                    print("ERROR")
                    sock.close()
                    continue

                if data:
                    global stato_gate
                    msg = data.decode()

                    if len(msg) > 1:

                        if msg == 'STATO_NON_ATTIVO':
                            stato_gate = "NON_ATTIVO"
                            attivazione_lettura_gate(OFF)

                        if msg == 'OK':
                            print("RICEVO {0}".format(msg))
                            stato_gate = "OK"
                            print("ATTIVA GATE")
                            attivazione_lettura_gate(ON)

                        if msg == 'FS_AP':
                            stato_gate = "FS_AP"
                            attivazione_lettura_gate(ON)

                        if msg == 'FS_CH':
                            stato_gate = "FS_CH"
                            attivazione_lettura_gate(OFF)

                        if msg == 'ATTIVA_SBARRA':
                            # attiva_barriera()
                            pass

                        if msg == "X":
                            sock.close()
                            CONNECTION_LIST.remove(sock)
                            print("connessione terminata dal client")





# -------------------------------------------------------------------
# T H R E A D   I N V I O   D A T I   I N E S
# -------------------------------------------------------------------
def thread_invia_dati():

    while True:
        # Il thread si attiva ogni 1 secondi
        sleep(1)

        if database.dati_nel_db(db_path):

            try:
                print("TRY TO SEND DB DATA...")
                record = database.record_fifo(db_path)

                print("RECORD:", record)
                record_id = record[0]
                tag = record[1]
                varco = record[2]
                timestamp = record[3]

                put_lettura = VarchiPutLetture()
                print("INVIO DATI...")
                response_msg = put_lettura.put_lettura(tag, varco, timestamp)

                print("RESP:", response_msg)

                if response_msg == "0" or response_msg == 200:
                    database.cancella_record(db_path, record_id)
                    print("IL RECORD E' STATO ELIMINATO DAL DB: ID-{0};TAG-{1};VARCO-{2};TIMESTAMP-{3}".format(record_id, tag, varco, timestamp))

            except Exception as ex:

                print("ERRORE: {0} - thread_invia_dati".format(str(ex)))
                continue


# -------------------------------------------------------------------
#  INVIA DATI SERVER INES
# -------------------------------------------------------------------
def chiedi_permesso_server_ines(tag, stato_barriera):

    global ID_GATE
    global ultimo_tag_letto
    global tmstp_ultima_lettura

    current_milli_time = lambda: int(round(time.time() * 1000))
    dtstmp = current_milli_time()

    print(abs(dtstmp - tmstp_ultima_lettura))

    # controllo lettura tag
    # se il tag e lo stesso entro i 10 secondi non viene riletto
    if ultimo_tag_letto == tag:

        if abs(dtstmp - tmstp_ultima_lettura) < 10000:
            print("TAG PRECEDENTE, NON VERRANNO INVIATI DATI AL SERVER")
            tmstp_ultima_lettura = dtstmp
            return

    try:

        # Ci sono dati da inviare nel db ?
        dati_in_attesa = database.dati_nel_db(db_path)
        print(dati_in_attesa)

        # SI
        if dati_in_attesa:
            # - apre barriera
            print("AGGIUNGO DATI NEL DB")
            database.scrivi_dati_nel_db(db_path, tag, ID_GATE )


        else:
            # NO
            # - invia i dati direttamente al server ines

            put_lettura = VarchiPutLetture()
            response = put_lettura.put_lettura(tag, ID_GATE)

            autorizzazione = True if response == 200 else False

            # QUESTA E' PER LA BETA
            if autorizzazione == True:
                #apre barriera
                print("-" * 70)
                print("* * *   A U T O R I Z Z A Z I O N E    C O N C E S S A   * * *")
                print("-" * 70)
                print("")

                pass
            else:
                print("-"*70)
                print("! ! !   A U T O R I Z Z A Z I O N E    N E G A T A   ! ! !")

                print("-" * 70)
                print("")
                pass

            if response == 405:
                database.scrivi_dati_nel_db(db_path, tag, ID_GATE)

    # - Problema di rete?
    except Exception as ex:
        print("ERRORE: {0}".format(str(ex)))
        # -- SI
        # -- Apre barriera
        # attiva_barriera()
        # -- inserisce i dati nel db
        print("SALVATAGGIO DATI NEL DB")
        database.scrivi_dati_nel_db(db_path, tag, ID_GATE)



    ultimo_tag_letto = tag
    tmstp_ultima_lettura = dtstmp

    # ------------------------------------- invia_dati_server_inse() END

# -------------------------------------------------------------------
#  L E T T U R A   T A G
# -------------------------------------------------------------------
def lettura_tag():

    while True:

        if stato_gate == 'OK':
            if ser.isOpen():


                try:
                    tag = ser.readline()
                except serial.SerialException as e:
                    continue

                tag = tag.decode("utf-8")

                if len(tag) > 10:

                    if tag[0] == '$' and tag[len(tag) - 2:len(tag)] == '\r\n':

                        tag = tag[1:len(tag) - 2]
                        print("TAG ACQUISITO: {0}".format(tag))

                        permesso = chiedi_permesso_server_ines(tag, "OK")

                        sleep(0.5)

                        ser.flushOutput()
                        ser.flushInput()
                        tag = ""

                    else:
                        ser.flushOutput()
                        ser.flushInput()
                        tag = ""

            ser.flushOutput()
            ser.flushInput()
# ------------------------------------- lettura_tag END


th_dati_ines = threading.Thread(name="invia_dati_ines", target=thread_invia_dati)
th_dati_ines.start()

discoverygate_init()
lettura_tag()
