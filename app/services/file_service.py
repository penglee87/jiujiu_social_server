import os
from flask import current_app
from werkzeug.utils import secure_filename

class FileService:
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav'}
    ALLOWED_FILE_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS).union(ALLOWED_AUDIO_EXTENSIONS)

    @staticmethod
    def allowed_file(filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @staticmethod
    def save_file(folder, file, file_type, allowed_extensions):
        print('file.filename1',file.filename)
        if file and FileService.allowed_file(file.filename, allowed_extensions):
            print('file.filename2',file.filename)
            filename = secure_filename(file.filename)
            print('secure_filename',filename)
            # 确保目录存在
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], folder, file_type)
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            return f"/static/uploads/{folder}/{file_type}/{filename}"
        return None

    @staticmethod
    def save_image(folder, file):
        return FileService.save_file(folder, file, 'images', FileService.ALLOWED_IMAGE_EXTENSIONS)

    @staticmethod
    def save_video(folder, file):
        return FileService.save_file(folder, file, 'videos', FileService.ALLOWED_VIDEO_EXTENSIONS)

    @staticmethod
    def save_audio(folder, file):
        return FileService.save_file(folder, file, 'audios', FileService.ALLOWED_AUDIO_EXTENSIONS)
    
