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
        self.unban_guild_ids = None  # массив с idшниками guild для тикетов на Разбан
        self.appeal_channel_id = None  # это id канала в который постится эмбед с кнопкой для подачи апеляции на разбан
        self.welcome_thread_channel_id = None  # это id канала под которым оздаются приветные ветки с анкетами разбана
        self.docs_transfer_report_channel_id = None  # это id канала отчётов
        self.docs_transfer_spreadsheet_key = None  # это ключ идентефикатора таблицы на которую загружаются отчёты