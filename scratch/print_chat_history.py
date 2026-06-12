import psycopg2

def inspect():
    try:
        conn = psycopg2.connect(host='localhost', port=5432, dbname='NotificationService', user='postgres', password='root')
        cur = conn.cursor()
        
        # We need the conversation ID where one of the participants is 'ai_assistant' and the other is '0739d6f3-f96e-4f4e-b4df-3c8261be467c'
        user_id = '0739d6f3-f96e-4f4e-b4df-3c8261be467c'
        cur.execute('SELECT "Id", "ParticipantA", "ParticipantB" FROM "Conversations" WHERE ("ParticipantA" = \'ai_assistant\' AND "ParticipantB" = %s) OR ("ParticipantB" = \'ai_assistant\' AND "ParticipantA" = %s)', (user_id, user_id))
        row = cur.fetchone()
        if not row:
            print("No AI conversation found.")
            return
        conv_id, pA, pB = row
        print(f"AI Conversation ID: {conv_id} ({pA} <-> {pB})")
        
        cur.execute('SELECT "SenderId", "Content", "Type", "CreatedAt" FROM "Messages" WHERE "ConversationId" = %s ORDER BY "CreatedAt" ASC', (conv_id,))
        rows = cur.fetchall()
        print(f"=== DATABASE MESSAGES FOR AI CONVERSATION ===")
        for r in rows:
            print(f"[{r[3]}] {r[0]} ({r[2]}): {repr(r[1])}")
            
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    inspect()
