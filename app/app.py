from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory
)
import os
import utils


app = Flask(__name__, template_folder='templates')
credentials = utils.read_credentials('secrets.yaml')
db_connection = utils.connect_to_db(credentials)

# QUERIES
READ_TASKS = """
select
	t.task_id
	, t.task
	, t.status
	, to_char(t.due_date, 'yyyy-mm-dd') due_date
	, (array_agg(t2.tag))[1] as tag
from tasks t
left join task_tag tt on t.task_id = tt.task_id
left join tags t2 on tt.tag_id = t2.tag_id
group by t.task_id, t.task, t.status, t.due_date
order by t.status asc
;
"""

READ_TASKS_STATUS = """
select distinct status
from tasks
order by status asc
;
"""

ADD_TASK_TASKS = """
INSERT INTO tasks (task, due_date) values (%s, %s) RETURNING task_id;
"""

ADD_TASK_TAGS = """
INSERT INTO tags(tag)
SELECT %s
WHERE
NOT EXISTS (
SELECT tag FROM tags WHERE tag = %s
)
RETURNING tag_id;
"""

ADD_TASK_TASK_TAG_1 = """
INSERT INTO task_tag (task_id, tag_id) values (%s, %s);
"""

ADD_TASK_TASK_TAG_2 = """
INSERT INTO task_tag (task_id, tag_id) values (%s, (select tag_id from tags where tag=%s));
"""

DELETE_TASK_FROM_TASKS = """
delete
from tasks
where task_id = %s
"""

DELETE_TASK_FROM_TASK_TAG = """
delete
from task_tag
where task_id = %s
"""

READ_TASK = """
select
	t.task_id
	, t.task
	, t.status
	, to_char(t.due_date, 'yyyy-mm-dd') due_date
	, (array_agg(t2.tag))[1] as tag
from tasks t
left join task_tag tt on t.task_id = tt.task_id
left join tags t2 on tt.tag_id = t2.tag_id
where t.task_id = %s
group by t.task_id, t.task, t.status, t.due_date
;
"""

UPDATE_TASK = """
update tasks
set task = %s, 
    status = %s,
    due_date = %s
where task_id = %s
;
"""

DELETE_TAGS_OF_A_TASK = """
delete
from task_tag
where task_id = %s
"""

READ_STATUS_ENUM = """
SELECT enumlabel
FROM pg_enum
JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
WHERE pg_type.typname = 'task_status_enum' and enumlabel != %s
order by enumlabel desc;
"""

node_modules_path = '/app/node_modules'

@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return send_from_directory(node_modules_path, filename)

@app.route('/')
def index():
    with db_connection.cursor() as cursor:
        # Tasks
        cursor.execute(READ_TASKS)
        rows = cursor.fetchall()
        column_names = [metadata[0] for metadata in cursor.description]
        tasks = [dict(zip(column_names, row)) for row in rows]
        # Status
        cursor.execute(READ_TASKS_STATUS)
        rows = cursor.fetchall()
        status = [_[0] for _ in rows]

        tasks_grouped_by_status = {
            status_i: [task for task in tasks if task['status']==status_i] for status_i in status
        }

    return render_template('index.html', tasks=tasks, tasks_grouped=tasks_grouped_by_status)

@app.route('/add', methods=['POST'])
def add():
    # Task attributes
    task = request.form['task']
    tag = request.form['tag'] if len(request.form['tag']) > 0 else None
    due_date = request.form['due_date'] if len(request.form['due_date']) > 0 else None
    # Create in database
    with db_connection.cursor() as cursor:
        # Add task to tasks table
        cursor.execute(ADD_TASK_TASKS, (task, due_date))
        task_id = cursor.fetchall()
        # Add tag to tags table
        tag_id = cursor.execute(ADD_TASK_TAGS, (tag, tag))
        tag_id = cursor.fetchall()
        # Add task tag relation
        # If it is a new tag
        if len(tag_id) > 0:
            cursor.execute(ADD_TASK_TASK_TAG_1, (task_id[0][0], tag_id[0][0]))
        # If the tag already existed
        else:
            cursor.execute(ADD_TASK_TASK_TAG_2, (task_id[0][0], tag))

    db_connection.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>')
def delete(task_id):
    with db_connection.cursor() as cursor:
        cursor.execute(DELETE_TASK_FROM_TASKS, (task_id, ))
        cursor.execute(DELETE_TASK_FROM_TASK_TAG, (task_id, ))
    db_connection.commit()
    return redirect(url_for('index'))

@app.route('/modify/<int:task_id>', methods=['GET', 'POST'])
def modify(task_id):
    with db_connection.cursor() as cursor:
        cursor.execute(READ_TASK, (task_id, ))
        task = cursor.fetchall()[0]
        column_names = [metadata[0] for metadata in cursor.description]
        task = dict(zip(column_names, task))


        cursor.execute(READ_STATUS_ENUM, (task['status'], ))
        status = cursor.fetchall()
        status = [_[0] for _ in status]

    return render_template('modify.html', task=task, status=status)

@app.route('/update/<int:task_id>', methods=['POST'])
def update(task_id):
    # To modify tasks table fields
    task = request.form['task']
    status = request.form['status']
    if request.form['due_date'] != 'None' and len(request.form['due_date']) > 0:
        due_date = request.form['due_date']
    else:
        due_date = None

    if request.form['tag'] != 'None' and len(request.form['tag']) > 0:
        tag = request.form['tag']
    else:
        tag = None

    with db_connection.cursor() as cursor:
        # delete all existing tags of the task
        cursor.execute(DELETE_TAGS_OF_A_TASK, (task_id, ))
        # To modify tags
        if tag is not None:

            # Add tag to tags table
            tag_id = cursor.execute(ADD_TASK_TAGS, (tag, tag))
            tag_id = cursor.fetchall()
            # Add task tag relation
            # If it is a new tag
            if len(tag_id) > 0:
                cursor.execute(ADD_TASK_TASK_TAG_1, (task_id, tag_id[0][0]))
            # If the tag already existed
            else:
                cursor.execute(ADD_TASK_TASK_TAG_2, (task_id, tag))

        # To update the rest of the fields
        cursor.execute(UPDATE_TASK, (task, status, due_date, task_id))

    db_connection.commit()

    return redirect(url_for('index'))

@app.route('/cancel')
def cancel():
    return redirect(url_for('index'))





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)