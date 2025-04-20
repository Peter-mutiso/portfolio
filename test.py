import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='portfolio'
    )
    print("✅ Connected to MySQL successfully!")
except Exception as e:
    print("❌ Connection failed:", e)
