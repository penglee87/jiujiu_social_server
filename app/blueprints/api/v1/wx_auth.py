from flask import request, jsonify
from app.services.auth_service import AuthService
from . import api_bl


@api_bl.route('/register_bak', methods=['POST'])
def register_bak():
    data = request.get_json()
    response = AuthService.register(data)
    return jsonify(response)

@api_bl.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    response = AuthService.register(data)
    return jsonify(response)

@api_bl.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    response = AuthService.login(data)
    return jsonify(response)

@api_bl.route('/user_edit', methods=['POST'])
def user_edit():
    data = request.form.to_dict()
    file = request.files.get('avatar')
    response = AuthService.user_edit(data,file)
    return jsonify(response)


#@api_bl.route('/upload_file', methods=['POST'])
#def upload_file():
#    data = request.form.to_dict()
#    files = request.files.to_dict()
#    response = AuthService.register(data,files)
#    return jsonify(response)