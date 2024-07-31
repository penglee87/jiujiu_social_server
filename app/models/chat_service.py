from app import db
from app.models import ChatRoom, UserChatRoom

def create_chat_room(name):
    chat_room = ChatRoom(name=name)
    db.session.add(chat_room)
    db.session.commit()
    return chat_room

#def add_user_to_chat_room(chat_room, user):
#    if not chat_room.users.filter_by(id=user.id).first():
#        chat_room.users.append(user)
#        db.session.commit()

def add_user_to_chat_room(chat_room, user):
    if not db.session.query(UserChatRoom).filter_by(user_id=user.id, chat_room_id=chat_room.id).first():
        user_chat_room = UserChatRoom(user_id=user.id, chat_room_id=chat_room.id)
        db.session.add(user_chat_room)
        db.session.commit()