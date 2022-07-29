from threading import Thread
from flask import current_app
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer


def generate_signed_token(app, payload, salt):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(payload, salt=salt)


def confirm_signed_token(app, token, salt, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    sig_okay, payload = serializer.loads_unsafe(token, salt=salt,
                                                max_age=expiration)
    return sig_okay, payload
            

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
