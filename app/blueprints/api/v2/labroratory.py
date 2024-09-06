# app/blueprints/api/v2/labroratory.py
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, LabQuestion, LabRoom, UserLabRoom, LabMessage
from . import api_bl

def add_user_to_lab_room(lab_room, user):
    """Add a user to a lab room."""
    user_lab_room = UserLabRoom.query.filter_by(user_id=user.id, lab_room_id=lab_room.id).first()
    if not user_lab_room:
        user_lab_room = UserLabRoom(user_id=user.id, lab_room_id=lab_room.id)
        db.session.add(user_lab_room)
        db.session.commit()



# 管理员添加或编辑 LabQuestion 的方法
@api_bl.route('/lab/admin/question', methods=['POST'])
@jwt_required()
def add_or_edit_question():
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()

    # Check if the user is an admin
    if not current_user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    question_id = data.get('question_id')
    question_class = data.get('question_class')
    question_body = data.get('question_body')

    if not question_class or not question_body:
        return jsonify({'message': 'Question class and body are required'}), 400

    if question_id:
        # Edit existing question
        question = LabQuestion.query.get(question_id)
        if not question:
            return jsonify({'message': 'Question not found'}), 404
        question.question_class = question_class
        question.question_body = question_body
    else:
        # Add new question
        question = LabQuestion(question_class=question_class, question_body=question_body)
        db.session.add(question)

    db.session.commit()
    return jsonify({'message': 'Question saved', 'question_id': question.id})

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



@api_bl.route('/lab/get_questions', methods=['GET'])
@jwt_required()
def lab_get_questions():
    """Get lab questions by category"""
    question_class = request.args.get('question_class')  # 获取查询参数
    if question_class:
        # 如果提供了 question_class 参数，则根据该分类过滤问题
        lab_questions = LabQuestion.query.filter_by(question_class=question_class).all()
    else:
        # 否则，获取所有问题
        lab_questions = LabQuestion.query.all()

    questions = [{'question_id': q.id, 'question_class': q.question_class, 'question_body': q.question_body} for q in lab_questions]
    return jsonify({'questions': questions})

@api_bl.route('/lab/lab_room/<int:lab_room_id>/add_question', methods=['POST'])
@jwt_required()
def lab_add_question(lab_room_id):
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()
    data = request.get_json()

    new_question = LabQuestion(
        user_id=current_user.id,
        question_class=data.get('question_class', ''),
        question_body=data['question_body']
    )
    db.session.add(new_question)
    db.session.commit()

    new_message = LabMessage(
        lab_room_id=lab_room_id,
        question_id=new_question.id,
        user_id=current_user.id,
        answer=data['answer']
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Question and answer added successfully"}), 201

@api_bl.route('/lab/lab_room/<int:lab_room_id>/answer_question', methods=['POST'])
@jwt_required()
def lab_answer_question(lab_room_id):
    openid = get_jwt_identity()
    current_user = User.query.filter_by(openid=openid).first()

    data = request.get_json()
    question_id = data.get('question_id')
    answer = data.get('answer')

    lab_message = LabMessage(
            lab_room_id=lab_room_id,
            question_id=question_id, 
            user_id=current_user.id, 
            answer=answer
            )
    db.session.add(lab_message)
    db.session.commit()
    return jsonify({'message': 'Answer recorded'})


@api_bl.route('/lab/lab_room/<int:lab_room_id>/messages', methods=['GET'])
@jwt_required()
def lab_get_messages(lab_room_id):
    lab_messages = LabMessage.query.filter_by(lab_room_id=lab_room_id).all()
    messages = []
    for msg in lab_messages:
        message_data = {
            'id': msg.id,
            'question_id': msg.question_id,
            'question_class': msg.question.question_class if msg.question else None,
            'question_body': msg.question.question_body if msg.question else None,
            'user_id': msg.user_id,
            'answer': msg.answer,
            'created_at': msg.created_at
        }
        messages.append(message_data)

    return jsonify({
        "message": "Messages loaded successfully",
        "data": messages
    }), 200
    
