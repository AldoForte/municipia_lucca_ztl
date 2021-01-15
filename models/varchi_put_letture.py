import requests
import time
from models.configuration import Configuration

from xml.dom.minidom import parse, parseString


class VarchiPutLetture():

    def __init__(self):

        self.body = """
            {{
                "CODICE_TAG":"{0}",
                "CODICE_VARCO":"{1}",
                "TIMESTAMP": "{2}"
            }}
            """

    def put_lettura(self, tag, varco, tmstamp=0):

        try:
            if tmstamp == 0:
                tmstamp = int(round(time.time() * 1000))

            body = self.body.format(tag, varco, tmstamp)

            print("[INFO] BODY: ", body)

            requests.packages.urllib3.disable_warnings()
            response = requests.post(Configuration.endpoint,  data=body,
                                     auth=(Configuration.username, Configuration.password),
                                     verify=False, timeout=5)

            status_code = response.status_code
            return status_code

        except requests.exceptions.ConnectionError:
            print("connection error")
            return 405

        except Exception as ex:
            print("EXCEPTION IN PUT LETTURE:", str(ex))
            print(str(ex))

