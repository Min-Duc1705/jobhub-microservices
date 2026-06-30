import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="NotificationService",
    user="postgres",
    password="root"
)
cur = conn.cursor()
cur.execute('SELECT "UserId", "TelegramChatId", "Username", "BotToken" FROM "UserTelegramBindings";')
rows = cur.fetchall()
print("Bindings:")
for r in rows:
    print(f"UserId: {r[0]}, ChatId: {r[1]}, Username: {r[2]}, BotToken: {r[3]}")
cur.close()
conn.close()
