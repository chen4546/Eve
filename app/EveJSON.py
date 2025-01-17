import cv2
import mediapipe as mp
import time
import socket
import os

class PoseDetector:
    def __init__(self, udp_ip="127.0.0.1", udp_port=5053, input_source=0, target_fps=15):
        """
        初始化 PoseDetector。
        :param udp_ip: Unity 的 IP 地址
        :param udp_port: Unity 的 UDP 端口
        :param input_source: 输入源（摄像头索引或视频文件路径）
        :param target_fps: 目标帧率
        """
        # 初始化 Mediapipe Pose
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 初始化 UDP 客户端
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 设置输入源
        self.input_source = input_source
        self.cap = cv2.VideoCapture(input_source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # 获取视频帧的高度
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # 设置目标帧率
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps

        # 初始化关键点数据
        self.initial_landmarks = [
            round(449.3459165096283, 2), round(714.5003080368042, 2), round(-559.8941445350647, 2),  # 0
            round(446.0371434688568, 2), round(725.4952192306519, 2), round(-530.1176309585571, 2),  # 1
            round(440.5176341533661, 2), round(725.0558137893677, 2), round(-530.6529998779297, 2),  # 2
            round(434.7280263900757, 2), round(724.7721552848816, 2), round(-530.587911605835, 2),   # 3
            round(464.2413556575775, 2), round(725.5840301513672, 2), round(-542.7607297897339, 2),  # 4
            round(473.37135672569275, 2), round(724.7544527053833, 2), round(-543.2844161987305, 2), # 5
            round(481.39965534210205, 2), round(723.5409021377563, 2), round(-543.4849262237549, 2), # 6
            round(434.19671058654785, 2), round(716.3832783699036, 2), round(-348.60917925834656, 2),# 7
            round(498.5007345676422, 2), round(712.8079533576965, 2), round(-403.3050537109375, 2),  # 8
            round(440.59720635414124, 2), round(698.7218856811523, 2), round(-486.8302643299103, 2), # 9
            round(463.70384097099304, 2), round(697.0092058181763, 2), round(-506.0541033744812, 2), # 10
            round(368.1108057498932, 2), round(636.3992691040039, 2), round(-241.0183995962143, 2),  # 11
            round(572.7627277374268, 2), round(639.5279765129089, 2), round(-271.5398967266083, 2),  # 12
            round(239.09048736095428, 2), round(605.8329343795776, 2), round(-241.91229045391083, 2),# 13
            round(697.2125172615051, 2), round(612.7327680587769, 2), round(-186.40141189098358, 2), # 14
            round(137.99265027046204, 2), round(552.7921915054321, 2), round(-427.7322590351105, 2), # 15
            round(793.2202219963074, 2), round(564.5583868026733, 2), round(-179.79419231414795, 2), # 16
            round(106.95347189903259, 2), round(540.9569144248962, 2), round(-463.08860182762146, 2),# 17
            round(819.149315357208, 2), round(547.2962260246277, 2), round(-196.8640685081482, 2),   # 18
            round(111.50521039962769, 2), round(534.2422127723694, 2), round(-525.5852341651917, 2), # 19
            round(811.360776424408, 2), round(543.0751442909241, 2), round(-257.5419545173645, 2),   # 20
            round(127.1783709526062, 2), round(534.3748331069946, 2), round(-458.9795768260956, 2),  # 21
            round(799.0863919258118, 2), round(545.5693006515503, 2), round(-207.73892104625702, 2), # 22
            round(404.49199080467224, 2), round(432.55892395973206, 2), round(7.361092139035463, 2), # 23
            round(509.8167657852173, 2), round(428.034245967865, 2), round(-7.865667343139648, 2),   # 24
            round(406.3750207424164, 2), round(292.21808910369873, 2), round(142.98605918884277, 2), # 25
            round(499.7726380825043, 2), round(288.2435917854309, 2), round(78.69795709848404, 2),   # 26
            round(404.51154112815857, 2), round(195.0087994337082, 2), round(566.814124584198, 2),   # 27
            round(504.44960594177246, 2), round(193.44022870063782, 2), round(476.88689827919006, 2),# 28
            round(418.79019141197205, 2), round(186.1301213502884, 2), round(599.4629859924316, 2),  # 29
            round(493.7026798725128, 2), round(183.14270675182343, 2), round(510.17600297927856, 2), # 30
            round(379.9905776977539, 2), round(138.60613107681274, 2), round(446.16782665252686, 2), # 31
            round(536.101222038269, 2), round(135.16759872436523, 2), round(354.1853427886963, 2)    # 32
        ]
        self.previous_landmarks = self.initial_landmarks
        base_name = os.path.basename(input_source).split('.')[0]
        self.data_file_path = os.path.join('data', f'{base_name}.txt')

        self.data_file = open(self.data_file_path, 'w')

    def run(self):
        """
        运行 PoseDetector。
        """
        while self.cap.isOpened():
            start_time = time.time()  # 记录当前帧开始处理的时间

            ret, frame = self.cap.read()
            if not ret:
                break

            # 如果是摄像头输入，进行左右镜像
            if self.input_source == 0:  # 摄像头输入
                frame = cv2.flip(frame, 1)  # 1 表示左右镜像

            # 转换颜色空间
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 进行关键点检测
            results = self.pose.process(frame_rgb)

            # 如果有检测到关键点
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # 提取 33 个关键点的 x, y, z 值
                data = self.previous_landmarks.copy()  # 初始化为上一帧的数据
                for idx, landmark in enumerate(landmarks):
                    # 检查关键点是否可见
                    if landmark.visibility >= 0.5:  # 可见的关键点
                        x = landmark.x * 1000
                        y = (1 - landmark.y) * self.height  # 上下翻转 y 坐标
                        z = landmark.z * 1000
                        data[idx * 3] = '{:.2f}'.format(x)  # x 坐标
                        data[idx * 3 + 1] = '{:.2f}'.format(y)  # y 坐标（上下翻转）
                        data[idx * 3 + 2] = '{:.2f}'.format(z)  # z 坐标
                self.previous_landmarks = data  # 更新上一帧的关键点数据
            else:
                # 如果当前帧没有检测到关键点，使用上一帧的数据
                data = self.previous_landmarks

            # 在发送数据之前，检查数据长度
            data_str = ",".join(map(str, data)) + "\n"
            #print(f"Sending data length: {len(data_str.split(','))}")  # 输出数据长度
            #print(data_str)  # 输出数据内容
            # 将数据写入文件
            self.data_file.write(data_str)
            self.sock.sendto(data_str.encode(), (self.udp_ip, self.udp_port))

            # 在图像上绘制关键点
            if results.pose_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )

            # 显示结果（不翻转）
            cv2.imshow('Mediapipe Pose', frame)
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

            # 计算处理当前帧所花费的时间
            elapsed_time = time.time() - start_time
            # 等待剩余的时间，以确保达到目标帧率
            time_to_wait = self.frame_interval - elapsed_time
            if time_to_wait > 0:
                time.sleep(time_to_wait)

        # 释放资源
        self.cap.release()
        cv2.destroyAllWindows()
        self.sock.close()
        self.data_file.close()

    def stop(self):
        """
        停止 PoseDetector。
        """
        self.running = False
        self.cap.release()
        cv2.destroyAllWindows()
        self.sock.close()
        self.data_file.close()