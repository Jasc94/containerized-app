from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)
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
	, t.due_date
	, array_agg(t2.tag) as tags
from tasks t
left join task_tag tt on t.task_id = tt.task_id
left join tags t2 on tt.tag_id = t2.tag_id
group by t.task_id, t.task, t.status, t.due_date
;
"""

ADD_TASK_TASKS = """
INSERT INTO tasks (task) values (%s);
"""

ADD_TASK_TAG = """
INSERT INTO tags (tag) values(%s);
"""

ADD_TASK_TASK_TAG = """
INSERT INTO task_tak (task_id, tag_id) values (%s, %s);
"""


@app.route('/')
def index():
    with db_connection.cursor() as cursor:
        cursor.execute(READ_TASKS)
        rows = cursor.fetchall()
        column_names = [metadata[0] for metadata in cursor.description]
        tasks = [dict(zip(column_names, row)) for row in rows]
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    task = request.form['task']
    with db_connection.cursor() as cursor:
        cursor.execute(ADD_TASK_TASKS, (task,))
    db_connection.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:index>', methods=['GET', 'POST'])
def edit(index):
    todo = todos[index]
    if request.method == 'POST':
        todo['task'] = request.form['todo']
        return redirect(url_for('index'))
    else:
        return render_template('edit.html', todo=todo, index=index)

@app.route('/check/<int:index>')
def check(index):
    todos[index]['done'] = not todos[index]['done']
    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
def delete(index):
    del todos[index]
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)