from threading import Thread
from flask import current_app
from flask_mail import Message


def send_async_email(app, msg):
    assert hasattr(app, 'flask_mail_mail'), 'app was not decorated with mail instance'
    with app.app_context():
        app.flask_mail_mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()
