class Global:
    def __init__(self):
        self.config_file = None  # название конфигуриционного файла
        self.config_pass = None  # Да
        self.admins = None  # массив с id админов
        self.servers = None  # массив с id серверов и их id для отправки и чтения сообщений
        self.discord_token = None  # говорит само за себя
        self.openai_keys = None  # как и это
        self.moder_roles = None  # массив с id ролей модеров и их приоритетом
        self.guilds = None  # массив чисто с id серваков на котором есть бот и ещё всякой инфой(кол-во участников и прочее)