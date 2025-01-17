from flask import Flask, request, jsonify,Blueprint,render_template
from flask_cors import CORS
from EveJSON import PoseDetector
import threading
import os

app = Flask(__name__)
CORS(app)

detector = None
detector_thread = None
video_path = None  # 添加全局变量存储当前上传的视频路径
def current_video_path(*path):
    global video_path
    if len(path)==0:
        return video_path
    else:
        video_path=path[0]
        return video_path

@app.route('/')
def index():
    return render_template('test.html')  # 确保 'test.html' 在 'templates' 文件夹中


# 定义上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'avi', 'mov'}

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 定义 /upload 路由
@app.route('/upload', methods=['POST'])
def upload_video():
    # 检查是否有文件上传
    if 'video' not in request.files:
        return jsonify({"status": "error", "message": "No video file provided"}), 400

    video_file = request.files['video']

    # 检查文件是否为空
    if video_file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    # 检查文件类型是否允许
    if not allowed_file(video_file.filename):
        return jsonify({"status": "error", "message": "Invalid file type"}), 400

    # 保存文件
    try:
        # 生成安全的文件名
        filename = os.path.join(UPLOAD_FOLDER, video_file.filename)
        video_file.save(filename)

        current_video_path(repr(filename).strip("'"))   # 缓存当前上传的视频路径
        #print(current_video_path())
        return jsonify({"status": "success", "message": "Video uploaded", "video_url": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 定义 /process 路由
@app.route('/process', methods=['POST'])
def process_video():
    global detector, detector_thread
    data = request.json
    #video_path = data.get('video_path')
    udp_ip = data.get('udp_ip', '127.0.0.1')
    udp_port = data.get('udp_port', 5053)
    target_fps = data.get('target_fps', 15)
    #print(data)
    #print('111')
    #print(current_video_path())
    if not current_video_path():
        return jsonify({"status": "error", "message": "No video path provided"}), 400

    # 停止已运行的 PoseDetector
    if detector:
        detector.stop()
        detector_thread.join()

    detector = PoseDetector(udp_ip, udp_port, current_video_path(), target_fps)

    # 定义一个函数来启动 PoseDetector
    def start_pose_detector():
        detector.run()

    detector_thread = threading.Thread(target=start_pose_detector)
    #pose_detector_thread.daemon = True  # 设置为守护线程，确保主程序退出时线程也退出
    detector_thread.start()
    return jsonify({"status": "success", "message": "Video processing started"})
if __name__ == '__main__':
    app.run(debug=True, port=5000)