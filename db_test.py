from psycopg2 import pool, extras


connection_pool = pool.ThreadedConnectionPool(
    1, 50, host='127.0.0.1', database='autocalib', user='admin', password='1234')

con = connection_pool.getconn()

cursor = con.cursor(cursor_factory=extras.NamedTupleCursor)
q = "INSERT INTO job_manager( job_id,  pid1,  pid2,  complete)VALUES ('0', '95580', 'None', 'running')"
#q = "UPDATE job_manager SET  complete= 'test' where job_id = 0"
print(q)
result = cursor.execute(q)
con.commit()
# result = cursor.fetchall()
print(result)
