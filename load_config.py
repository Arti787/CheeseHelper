import py7zr, os, toml
# функция, которая загружает конфигурацию из архива и возвращает токен дискорд бота и массив ключей от open ai
def load_config(archive_file):
    password = input("Требуется пароль от конфигурационного файла: ")
    with py7zr.SevenZipFile(archive_file, mode='r', password=password) as archive:
        archive.extract(targets=['config.toml'], path='temp')
        with open('temp/config.toml') as f:
            config = toml.load(f)
        # удаляем временную папку
        os.remove('temp/config.toml')
        os.rmdir('temp')

    discord_token = config["DISCORD_BOT_TOKEN"]
    openai_keys = config["OpenAi_keys"]
    admins = config["Admins"]
    moder_roles = config["Moder_roles"]
    servers = {}
    for server in config["Server"]:
        server_id = server["id"]
        servers[server_id] = {"send": None, "read": []}
        send_channels = server["send_channels"]["ids"]
        read_channels = server["read_channels"]["ids"]
        servers[server_id]["send"] = send_channels
        servers[server_id]["read"] = read_channels
    return admins, servers, discord_token, openai_keys, moder_roles
