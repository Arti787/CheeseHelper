import py7zr, os, toml

# Function that loads configuration from an archive and returns the Discord bot token and OpenAI keys array
def load_config(archive_file):
    password = input("Password required for configuration file: ")
    with py7zr.SevenZipFile(archive_file, mode='r', password=password) as archive:
        archive.extract(targets=['config.toml'], path='temp')
        with open('temp/config.toml', encoding="utf-8", errors="ignore") as f:
            config = toml.load(f)
        # Delete temporary folder
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

    unban_guild_ids = config["Unban"]["guild_ids"]
    appeal_channel_id = config["Unban"]["appeal_channel_id"]
    welcome_thread_channel_id = config["Unban"]["welcome_thread_channel_id"]

    docs_transfer_report_channel_id = config["DocsTransfer"]["report_channel_id"]
    docs_transfer_spreadsheet_key = config["DocsTransfer"]["spreadsheet_key"]

    return password, admins, servers, discord_token, openai_keys, moder_roles, unban_guild_ids, appeal_channel_id, welcome_thread_channel_id, docs_transfer_report_channel_id, docs_transfer_spreadsheet_key