from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import User, ChatRoom, Message
from flask_jwt_extended import decode_token

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('response', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join')
def handle_join(data):
    chat_room_id = data['chat_room_id']
    token = data['token']
    openid = decode_token(token)['identity']
    user = User.query.filter_by(openid=openid).first()
    join_room(chat_room_id)
    print(f'{user.nickname} has joined the room {chat_room_id}')

@socketio.on('leave')
def handle_leave(data):
    chat_room_id = data['chat_room_id']
    token = data['token']
    openid = decode_token(token)['identity']
    user = User.query.filter_by(openid=openid).first()
    leave_room(chat_room_id)
    print(f'{user.nickname} has left the room {chat_room_id}')

@socketio.on('send_message')
def handle_send_message(data):
    chat_room_id = data['chat_room_id']
    body = data['body']
    token = data['token']
    openid = decode_token(token)['identity']
    user = User.query.filter_by(openid=openid).first()

    if user:
        message = Message(
            body=body, 
            author_id=user.id, 
            chat_room_id=chat_room_id
        )
        db.session.add(message)
        db.session.commit()
        emit('receive_message', {
            'chat_room_id': chat_room_id,
            'message': message.to_json()
        }, room=chat_room_id)
