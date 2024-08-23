# app/blueprints/api/v2/labroratory.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User,LabRoom, UserLabRoom, LabMessage
from . import api_bl

def add_user_to_lab_room(lab_room, user):
    """Add a user to a lab room."""
    user_lab_room = UserLabRoom.query.filter_by(user_id=user.id, lab_room_id=lab_room.id).first()
    if not user_lab_room:
        user_lab_room = UserLabRoom(user_id=user.id, lab_room_id=lab_room.id)
        db.session.add(user_lab_room)
        db.session.commit()


@api_bl.route('/lab/create_lab_room', methods=['POST'])
@jwt_required()
def create_lab_room():
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    
    data = request.get_json()
    if not data or 'recipient_id' not in data:
        return jsonify({'message': 'Recipient ID is required'}), 400

    recipient = User.query.get(data['recipient_id'])
    print('create_lab_room_recipient',recipient)

    # Check if the room already exists
    lab_room_name = f"{min(current_user.id, recipient.id)}_{max(current_user.id, recipient.id)}"
    lab_room = LabRoom.query.filter_by(name=lab_room_name).first()

    if not lab_room:
        lab_room = LabRoom(name=lab_room_name)
        db.session.add(lab_room)
        db.session.commit()

        add_user_to_lab_room(lab_room, current_user)
        add_user_to_lab_room(lab_room, recipient)
        return jsonify({'message': 'Lab room created', 'lab_room_id': lab_room.id}), 200
    else:
        return jsonify({'message': 'Lab room already exists', 'lab_room_id': lab_room.id}), 200


@api_bl.route('/lab/lab_room/<int:lab_room_id>/send_question', methods=['POST'])
@jwt_required()
def lab_send_question(lab_room_id):
    data = request.get_json()
    question = data.get('question')
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()

    lab_message = LabMessage(question=question, body='', author_id=current_user.id, lab_room_id=lab_room_id)
    db.session.add(lab_message)
    db.session.commit()

    return jsonify({'message': 'Question sent', 'lab_message_id': lab_message.id})


@api_bl.route('/lab/lab_room/<int:lab_room_id>/answer_question/<int:lab_message_id>', methods=['POST'])
@jwt_required()
def lab_answer_question(lab_room_id, lab_question_id, lab_message_id):
    data = request.get_json()
    answer = data.get('answer')
    #openid = get_jwt_identity()
    #current_user = User.query.filter_by(openid=openid).first()

    lab_message = LabMessage.query.filter_by(id=lab_message_id, lab_room_id=lab_room_id, lab_question_id=lab_question_id).first()
    if lab_message:
        lab_message.body = answer
        db.session.commit()

        return jsonify({'message': 'Answer recorded'})
    else:
        return jsonify({'message': 'Lab message not found'}), 404
    

@api_bl.route('/lab/lab_room/<int:lab_room_id>/messages', methods=['GET'])
@jwt_required()
def lab_get_messages(lab_room_id):
    lab_messages = LabMessage.query.filter_by(lab_room_id=lab_room_id).all()
    messages = [{'id': msg.id, 'question': msg.question, 'body': msg.body, 'author_id': msg.author_id, 'timestamp': msg.timestamp} for msg in lab_messages]

    return jsonify({'messages': messages})