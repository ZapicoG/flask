from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS, cross_origin


# Database and App initialization:

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# db.init_app(app)


# Flask Mail config:

app.config['MAIL_SERVER'] = 'sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '0ece1b8bde9449'
app.config['MAIL_PASSWORD'] = 'a952360782797b'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)


# Schemas:

class Task(db.Model):

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=True, default=None)
    updated_at = db.Column(db.DateTime, nullable=True, default=None)

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'description': self.description, 'status': self.status}


@app.before_first_request
def create_tables():
    db.create_all()


# Routes:

@app.route('/tasks', methods=['GET'])
def get_tasks():

    tasks = Task.query.filter(Task.status != 3).all()
    return jsonify([task.to_dict() for task in tasks])


@app.route('/tasks/paginated', methods=['GET'])
def get_tasks_paginated():
    page = int(request.args["page"])
    per_page = int(request.args["per_page"])
    if request.args.get("status") != None:
        status = (int(request.args["status"]))
    else:
        status = 0
    # print(page, per_page)
    tasks = Task.query.filter(Task.status != 3, Task.status != status).paginate(
        page=page, per_page=per_page, count=True)

    return jsonify(tasks.total, [task.to_dict() for task in tasks])


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task.to_dict())


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()

    task = Task(
        title=data['title'], description=data['description'], status=data["status"])

    db.session.add(task)
    db.session.commit()

    send_email_alert('New task created',
                     'A new task has been created with title: ' + data['title'])
    return jsonify(task.to_dict())


@app.route('/tasks/<int:id>', methods=['PUT'])
def update_task(id):
    task = Task.query.get(id)

    if task is None:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json()

    task.title = data['title']
    task.description = data['description']
    task.status = data['status']
    title = task.title
    db.session.commit()

    send_email_alert(
        'Task updated', 'A task has been updated with title: ' + title)
    return jsonify(task.to_dict())


@app.route('/tasks/toggle/<int:id>', methods=['PUT'])
def toggle_task(id):
    task = Task.query.get(id)

    if task is None:
        return jsonify({'error': 'Task not found'}), 404

    task.status = 1 if task.status == 2 else 2
    title = task.title
    db.session.commit()

    send_email_alert(
        'Task updated', 'A task has been updated with title: ' + title)
    return jsonify(task.to_dict())


@app.route('/tasks/<int:id>', methods=['DELETE'])
def delete_task(id):
    task = Task.query.get(id)
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    task.status = 3
    db.session.commit()
    send_email_alert(
        'Task deleted', 'A task has been deleted with title: ' + task.title)
    return jsonify({'message': 'Task deleted'})


# Extra methods:
async def send_email_alert(subject, body):
    try:
        message = Message(subject=subject, sender='your_email@example.com',
                          recipients=['recipient@example.com'])
        message.body = body
        mail.send(message)
    except:
        print("error")
    return jsonify(status_code=200, content={"message": "email has been sent"})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
