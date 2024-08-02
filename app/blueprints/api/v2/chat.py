# app/blueprints/api/v2/chat.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from app import db, socketio
from app.models import User, ChatRoom, Message
from app.models.chat_service import create_chat_room, add_user_to_chat_room
from . import api_bl

@api_bl.route('/chat/create_chat', methods=['POST'])
@jwt_required()
def create_chat():
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    
    data = request.get_json()
    if not data or 'recipient_id' not in data:
        return jsonify({'message': 'Recipient ID is required'}), 400

    recipient = User.query.get(data['recipient_id'])
    if not recipient:
        return jsonify({'message': 'Recipient not found'}), 404

    chat_room_name = f"{min(current_user.id, recipient.id)}_{max(current_user.id, recipient.id)}"
    chat_room = ChatRoom.query.filter_by(name=chat_room_name).first()

    if not chat_room:
        chat_room = create_chat_room(chat_room_name)
        add_user_to_chat_room(chat_room, current_user)
        add_user_to_chat_room(chat_room, recipient)
        return jsonify({'message': 'Chat room created', 'chat_room_id': chat_room.id}), 200
    else:
        return jsonify({'message': 'Chat room already exists', 'chat_room_id': chat_room.id}), 200


@api_bl.route('/chat/<int:chat_room_id>/messages', methods=['GET'])
@jwt_required()
def get_chat_messages(chat_room_id):
    chat_room = ChatRoom.query.get_or_404(chat_room_id)    
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    if current_user not in chat_room.users:
        return jsonify({'message': 'Access denied'}), 403

    messages = Message.query.filter_by(chat_room_id=chat_room_id).order_by(Message.timestamp).all()
    return jsonify([{
        'id': message.id,
        'body': message.body,
        'timestamp': message.timestamp,
        'author_id': message.author_id
    } for message in messages])


@api_bl.route('/chat/<int:chat_room_id>/send_message', methods=['POST'])
@jwt_required()
def send_message(chat_room_id):
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    print('send_message_current_user',current_user)
    data = request.get_json()
    print('send_message_data',data)
    if not data or 'body' not in data:
        return jsonify({'message': 'Message body is required'}), 400

    try:
        chat_room = ChatRoom.query.get_or_404(chat_room_id)
        #if current_user not in chat_room.users:
        #    return jsonify({'message': 'Access denied'}), 403

        message = Message(
            body=data['body'], 
            author_id=current_user.id, 
            chat_room_id=chat_room.id
            )
        print('send_message_message',message)
        db.session.add(message)
        db.session.commit()

        # 使用 SocketIO 发送消息
        socketio.emit('new_message', {
            'id': message.id,
            'body': message.body,
            'timestamp': message.timestamp,
            'author_id': message.author_id
        }, room=chat_room.name)

        return jsonify({'message': 'Message sent', 'message_id': message.id}), 200
    except:
        return jsonify({'message': 'Error occurred'}), 500
    

#@socketio.on('join')
#def handle_join(data):
#    room = data['room']
#    join_room(room)
#    emit('status', {'msg': f'{data["username"]} has entered the room.'}, room=room)
#
#@socketio.on('leave')
#def handle_leave(data):
#    room = data['room']
#    leave_room(room)
#    emit('status', {'msg': f'{data["username"]} has left the room.'}, room=room)



#@api_bl.route('chat/create_or_get', methods=['POST'])
#def create_or_get_chat():
#    data = request.get_json()
#    user1_id = data.get('user1_id')
#    user2_id = data.get('user2_id')
#
#    if not user1_id or not user2_id:
#        return jsonify({'message': 'User IDs are required'}), 400
#
#    # 检查是否已经存在聊天房间
#    chat_room = ChatRoom.query.filter(
#        (ChatRoom.users.any(id=user1_id)) & (ChatRoom.users.any(id=user2_id))
#    ).first()
#
#    if not chat_room:
#        # 创建新的聊天房间
#        chat_room = ChatRoom()
#        db.session.add(chat_room)
#        db.session.commit()
#
#        # 添加用户到聊天房间
#        user1 = User.query.get(user1_id)
#        user2 = User.query.get(user2_id)
#        chat_room.users.append(user1)
#        chat_room.users.append(user2)
#        db.session.commit()
#
#    return jsonify({'chat_room': {'id': chat_room.id}})