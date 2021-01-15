import datetime
import sqlite3
import time



# S C R I T T U R A    D A T I   N E L   D B
def scrivi_dati_nel_db(database, codice_tag, codice_varco):
    """
    """
    try:
        print(database)
        conn = sqlite3.connect(database)
        c = conn.cursor()

        tmstamp = int(round(time.time() * 1000))
        c.execute("INSERT INTO dati (codice_tag, codice_varco, timestamp) VALUES (?, ?, ?)", (codice_tag, codice_varco, tmstamp ) )

        conn.commit();

        c.close()
        conn.close()

    except Exception as ex:
        print("ERRORE: {0} - scrivi_dati_nel_db".format(str(ex)))


# C A N C E L L A    R E C O R D
def cancella_record(database, record_id):
    """
    """
    try:
        print("CANCELLO RECORD DA DB...")
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute("DELETE FROM dati WHERE id = ?", ( record_id, ))

        conn.commit();

        c.close()
        conn.close()

    except Exception as ex:
        print("ERRORE: {0} - cancella_record".format(str(ex)))


def record_fifo(database):
    """
    """
    conn = sqlite3.connect(database)
    c = conn.cursor()
    c.execute("SELECT * FROM dati WHERE timestamp = ( SELECT MIN(timestamp) FROM dati)")
    record = c.fetchone()

    c.close()
    conn.close()

    return record


def dati_nel_db(database):

    try:
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute("SELECT * FROM dati")
        records = c.fetchall()
        num_records = len(records)

        c.close()
        conn.close()

        if num_records >= 1:
            return True
        else:
            return False

    except Exception as ex:
        print("FUNCT: dati_nel_db(database)")
        print("ERRORE: {0} - dati_nel_db".format(str(ex)))
