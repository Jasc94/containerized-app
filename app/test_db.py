import utils

credentials = utils.read_credentials('secrets.yaml')
db_connection = utils.connect_to_db(credentials)

cursor = db_connection.cursor()

sql_statements = [
# """
# CREATE TYPE task_status_enum AS ENUM ('Not started', 'In progress', 'Done')
# """,
# """
# CREATE TABLE tasks (
#   task_id SERIAL PRIMARY KEY, 
#   task VARCHAR (150) NOT NULL, 
#   status task_status_enum NOT NULL DEFAULT 'Not started',
#   due_date TIMESTAMP
# );
# """,
# """
# CREATE TABLE tags (
#   tag_id SERIAL PRIMARY KEY,
#   tag VARCHAR(20) NOT NULL
# )
# """,
# """
# CREATE TABLE task_tag (
#   task_id int REFERENCES tasks(task_id),
#   tag_id int REFERENCES tags(tag_id),
#   PRIMARY KEY (task_id, tag_id)
# )
# """
# "insert into tasks (task, due_date) values('Ordenar', '2024-08-10');",
# "insert into tags (tag) values ('Casa');",
# "insert into task_tag (task_id, tag_id) values (2, 1)"
]

try:
    for query in sql_statements:
        cursor.execute(query)
        db_connection.commit()
    print('Queries correctly executed')
except Exception as e:
    db_connection.rollback()
    print("An error ocurred {}".format(e))
finally:
    cursor.close()
    db_connection.close()