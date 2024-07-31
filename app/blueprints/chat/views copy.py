from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask_login import login_required, current_user
from flask_socketio import emit
from . import chat_bl
from .forms import MessageForm
from app import db, socketio
from app.models import User, ChatRoom, UserChatRoom, Message
from app.decorators import admin_required, permission_required



@chat_bl.route('/create_room', methods=['GET', 'POST'])
@login_required
def create_room():
    form = MessageForm()
    if form.validate_on_submit():
        room = ChatRoom(name=form.name.data, is_group=form.is_group.data)
        db.session.add(room)
        db.session.commit()
        # Add current user to the room
        user_chat_room = UserChatRoom(user_id=current_user.id, chat_room_id=room.id)
        db.session.add(user_chat_room)
        db.session.commit()
        flash('Chat room created successfully.')
        return redirect(url_for('.chat_room', room_id=room.id))
    return render_template('chat/create_room.html', form=form)


@chat_bl.route('/room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def chat_room(room_id):
    room = ChatRoom.query.get_or_404(room_id)
    # Add current user to the room if not already a member
    if not UserChatRoom.query.filter_by(user_id=current_user.id, chat_room_id=room_id).first():
        user_chat_room = UserChatRoom(user_id=current_user.id, chat_room_id=room_id)
        db.session.add(user_chat_room)
        db.session.commit()
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(body=form.body.data, author=current_user, chat_room=room)
        db.session.add(message)
        db.session.commit()
        flash('Message sent.')
        return redirect(url_for('.chat_room', room_id=room.id))
    messages = room.messages.order_by(Message.timestamp.asc()).all()
    return render_template('chat/chat_room.html', room=room, form=form, messages=messages)



@chat_bl.route('/chat/<recipient_id>', methods=['GET', 'POST'])
@login_required
def chat(recipient_id):
    recipient = User.query.get_or_404(recipient_id)
    if recipient == current_user:
        abort(403)

    chat_room = ChatRoom.query.join(UserChatRoom).filter(
        (UserChatRoom.user_id == current_user.id) &
        (UserChatRoom.chat_room_id == ChatRoom.id) &
        (ChatRoom.users.any(User.id == recipient_id))
    ).first()

    if not chat_room:
        chat_room = ChatRoom(name=f'chat_{current_user.id}_{recipient.id}')
        db.session.add(chat_room)
        db.session.commit()
        user_chat_room_1 = UserChatRoom(user_id=current_user.id, chat_room_id=chat_room.id)
        user_chat_room_2 = UserChatRoom(user_id=recipient.id, chat_room_id=chat_room.id)
        db.session.add(user_chat_room_1)
        db.session.add(user_chat_room_2)
        db.session.commit()

    form = MessageForm()
    if form.validate_on_submit():
        message = Message(body=form.message.data, author=current_user, chat_room=chat_room)
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('chat.chat', recipient_id=recipient.id))

    messages = chat_room.messages.order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', recipient=recipient, messages=messages, form=form)