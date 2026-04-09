import sqlite3
conn = sqlite3.connect(r'c:\Users\ING.HACKER\Desktop\TFE\soc-llm-audit-platform\backend\dev.db')
cursor = conn.execute("SELECT sql FROM sqlite_master WHERE name='audit_trail'")
row = cursor.fetchone()
print(row[0] if row else "TABLE NOT FOUND")
conn.close()
