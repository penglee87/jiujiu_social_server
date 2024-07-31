import os
from werkzeug.utils import secure_filename
from flask import request, jsonify
from app.services.auth_service import AuthService
from app.services.file_service import FileService
from . import api_bl



@api_bl.route('/upload_file', methods=['POST'])
def upload_file():
    # 打印所有查询参数
    query_params = request.args.to_dict()
    print("Query Params:", query_params)

    # 打印JSON数据
    #json_data = request.get_json()
    #print("JSON Data:", json_data)

    # 打印所有上传的文件
    files_data = {key: file.filename for key, file in request.files.items()}
    print("Files Data:", files_data)

    # 打印所有表单数据
    form_data = request.form.to_dict()
    print("Form Data:", form_data)
    folder = form_data.get('folder')
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        file_url = FileService.save_image(folder, file)
        if file_url:
            return jsonify({'url': file_url})
        else:
            return jsonify({'error': 'File upload failed'}), 500
    
    return jsonify({'error': 'Unexpected error'}), 500