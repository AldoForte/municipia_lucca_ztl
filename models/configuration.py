import configparser

class Configuration:

    username = ""
    password = ""
    endpoint = ""
    sp_port = "";
    sp_baudrate = ""
    sp_bytesize = 8
    sp_stopbits = 1
    sp_parity = 'N'


    @staticmethod
    def get_username():
        return Configuration.username

    @staticmethod
    def get_password():
        return Configuration.password

    @staticmethod
    def get_password():
        return Configuration.endpoint


    @staticmethod
    def loadConfiguration( config_path):
        conf = configparser.ConfigParser()
        conf.read(config_path)
        Configuration.endpoint = conf['autorizzazione_web']['endpoint']
        Configuration.username = conf['autorizzazione_web']['username']
        Configuration.password = conf['autorizzazione_web']['password']

        print("LOAD CONFIGURATION")
        print(Configuration.password)
        print(Configuration.username)
