import base64
import os
import sys
import uuid
import cv2
import time
import threading
import zipfile
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from data_augmentation import DataAugmentation


def get_runtime_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


BASE_DIR = get_runtime_base_dir()
TEMPLATE_DIR = resource_path("templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# 配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024  # 256MB max file size

# 初始化数据增强器
augmenter = DataAugmentation()

# 任务进度追踪
task_progress = {}
task_lock = threading.Lock()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def image_to_base64(image_path):
    """将图像转换为base64编码"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return encoded_string


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'files' not in request.files:
            return jsonify({'error': '没有文件被上传'}), 400

        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                # 生成唯一文件名
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                uploaded_files.append({'filename': unique_filename, 'original_name': filename})
            else:
                return jsonify({'error': f'不支持的文件格式: {file.filename}'}), 400

        return jsonify({'success': True, 'files': uploaded_files, 'message': f'成功上传 {len(uploaded_files)} 个文件'})

    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


def process_single_image(filename, augmentations, task_id, index, total):
    try:
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(input_path):
            return {'success': False, 'filename': filename, 'error': '文件不存在'}

        output_filename = f"augmented_{uuid.uuid4()}_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        image = cv2.imread(input_path)
        if image is None:
            return {'success': False, 'filename': filename, 'error': '无法读取图像文件'}

        params = {'noise_type': 'gaussian', 'blur_type': 'gaussian'}
        augmented_image = augmenter.apply_augmentation(image, augmentations, **params)

        cv2.imwrite(output_path, augmented_image)

        with task_lock:
            if task_id in task_progress:
                task_progress[task_id]['processed'] += 1
                task_progress[task_id]['progress'] = (task_progress[task_id]['processed'] / total) * 100

        return {'success': True, 'original_filename': filename, 'output_filename': output_filename}

    except Exception as e:
        return {'success': False, 'filename': filename, 'error': str(e)}


@app.route('/augment', methods=['POST'])
def augment_image():
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        augmentations = data.get('augmentations', [])

        if not filenames:
            return jsonify({'error': '没有指定文件名'}), 400

        task_id = str(uuid.uuid4())
        total = len(filenames)

        with task_lock:
            task_progress[task_id] = {'total': total, 'processed': 0, 'progress': 0}

        results = [None] * total
        max_workers = min(8, os.cpu_count() or 4)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_single_image, fn, augmentations, task_id, idx, total): idx
                      for idx, fn in enumerate(filenames)}

            for future in as_completed(futures):
                result = future.result()
                idx = futures[future]
                results[idx] = result

        with task_lock:
            if task_id in task_progress:
                del task_progress[task_id]

        success_count = len([r for r in results if r['success']])
        return jsonify({
            'success': True,
            'results': results,
            'message': f'成功处理 {success_count}/{total} 个文件'
        })

    except Exception as e:
        return jsonify({'error': f'处理失败: {str(e)}'}), 500


@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500


@app.route('/preview/<filename>')
def preview_original(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            image_base64 = image_to_base64(file_path)
            return jsonify({'success': True, 'image_data': f"data:image/jpeg;base64,{image_base64}"})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'预览失败: {str(e)}'}), 500


@app.route('/preview_result/<filename>')
def preview_result(filename):
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if os.path.exists(file_path):
            image_base64 = image_to_base64(file_path)
            return jsonify({'success': True, 'image_data': f"data:image/jpeg;base64,{image_base64}"})
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': f'预览失败: {str(e)}'}), 500


@app.route('/download_all', methods=['POST'])
def download_all():
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])

        if not filenames:
            return jsonify({'error': '没有要下载的文件'}), 400

        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename in filenames:
                file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                if os.path.exists(file_path):
                    zf.write(file_path, arcname=filename)

        memory_file.seek(0)
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name='augmented_images.zip'
        )

    except Exception as e:
        return jsonify({'error': f'打包下载失败: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)
