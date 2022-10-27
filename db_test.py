from re import I
import psycopg
from psycopg_pool import ConnectionPool


cs = "dbname=%s user=%s password=%s host=%s" % ('autocalib', 'admin', '1234', '127.0.0.1')
# pool = ConnectionPool(cs)
# # print(connection_pool)
# conn = pool.connection()
# conn.execute("INSERT INTO test (num, data) VALUES (%s, %s)", 
# (200, "abc'def"))
# print("test end 3")            

pool = ConnectionPool(cs)
# with ConnectionPool(cs) as pool :
# conn = pool.connection()
with pool.connection() as conn:
    with conn.cursor() as cur:    
        cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)",
            (400, "abc'def"))
        print("test end ")

        cur.execute('select * from test')
        cur.fetchone()
        print(cur)
        for record in cur :
            print('why ? ')
            print(record)

# Connect to an existing database
'''
with psycopg.connect(cs) as conn:

    # Open a cursor to perform database operations
    with conn.cursor() as cur:
        print("conn", conn)
        print("cur" , cur)
        # Execute a command: this creates a new table
        # cur.execute("""
        #     CREATE TABLE test (
        #         id serial PRIMARY KEY,
        #         num integer,
        #         data text)
        #     """)

        # Pass data to fill a query placeholders and let Psycopg perform
        # the correct conversion (no SQL injections!)
        cur.execute(
            "INSERT INTO test (num, data) VALUES (%s, %s)",
            (100, "abc'def"))

        # Query the database and obtain data as Python objects.
        cur.execute("SELECT * FROM test")
        cur.fetchone()
        # will return (1, 100, "abc'def")

        # You can use `cur.fetchmany()`, `cur.fetchall()` to return a list
        # of several records, or even iterate on the cursor
        for record in cur:
            print(record)

        # Make the changes to the database persistent
        conn.commit()
        '''