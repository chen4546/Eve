// 使用立即执行函数（IIFE）确保变量只声明一次
(function () {
  let recordStream,
    mediaRecorder,
    recordedChunks = [];
  let isRecording = false;
  let isPaused = false;
  let startTime,
    elapsedTime = 0;
  let timerInterval;
  const timerElement = document.getElementById("timer");
  const recordVideo = document.getElementById("recordVideo");

  // 缓存上传的视频文件
  let uploadedFile = null;

  // 获取摄像头视频流并显示
  async function initCamera() {
    try {
      const constraints = {
        audio: true,
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "user",
        },
      };

      // 检查媒体设备支持
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("浏览器不支持访问媒体设备");
      }

      // 获取权限
      const permissions = await navigator.permissions.query({ name: "camera" });
      if (permissions.state === "denied") {
        throw new Error("摄像头权限被拒绝");
      }

      recordStream = await navigator.mediaDevices.getUserMedia(constraints);
      recordVideo.srcObject = recordStream;

      // 添加视频加载监听
      recordVideo.addEventListener("loadedmetadata", () => {
        console.log(
          "视频分辨率:",
          recordVideo.videoWidth,
          "x",
          recordVideo.videoHeight
        );
      });

      recordVideo.addEventListener("error", (e) => {
        console.error("视频播放错误:", e);
        alert("视频播放失败，请检查摄像头连接");
      });
    } catch (error) {
      console.error("无法访问摄像头：", error);
      alert(
        `无法访问摄像头：${error.message}\n请确保：\n1. 摄像头已连接\n2. 已授予摄像头权限\n3. 使用HTTPS协议`
      );
      // 禁用录制按钮
      document.getElementById("startRecord").disabled = true;
    }
  }

  // 初始化摄像头
  initCamera();

  // 更新计时器
  function updateTimer() {
    elapsedTime = Date.now() - startTime;
    const seconds = Math.floor((elapsedTime / 1000) % 60);
    const minutes = Math.floor((elapsedTime / (1000 * 60)) % 60);
    const hours = Math.floor((elapsedTime / (1000 * 60 * 60)) % 24);
    timerElement.textContent = `${hours.toString().padStart(2, "0")}:${minutes
      .toString()
      .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }

  // 开始录制
  document.getElementById("startRecord").addEventListener("click", () => {
    if (recordStream) {
      mediaRecorder = new MediaRecorder(recordStream, {
        mimeType: "video/webm; codecs=vp9",
      });
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunks.push(event.data);
        }
      };

      mediaRecorder.start();
      isRecording = true;
      startTime = Date.now();
      timerInterval = setInterval(updateTimer, 1000);
      document.getElementById("startRecord").disabled = true;
      document.getElementById("pauseRecord").disabled = false;
      document.getElementById("stopRecord").disabled = false;
      timerElement.style.display = "block"; // 显示时间条
    } else {
      alert("摄像头未初始化，请刷新页面重试。");
    }
  });

  // 暂停录制
  document.getElementById("pauseRecord").addEventListener("click", () => {
    if (isRecording && !isPaused) {
      mediaRecorder.pause();
      isPaused = true;
      document.getElementById("pauseRecord").disabled = true;
      document.getElementById("resumeRecord").disabled = false;
      clearInterval(timerInterval); // 停止计时
    }
  });

  // 继续录制
  document.getElementById("resumeRecord").addEventListener("click", () => {
    if (isRecording && isPaused) {
      mediaRecorder.resume();
      isPaused = false;
      document.getElementById("pauseRecord").disabled = false;
      document.getElementById("resumeRecord").disabled = true;
      startTime = Date.now() - elapsedTime; // 重置开始时间
      timerInterval = setInterval(updateTimer, 1000); // 重新启动计时
    }
  });

  // 停止录制
  document.getElementById("stopRecord").addEventListener("click", () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      mediaRecorder.onstop = () => {
        clearInterval(timerInterval);
        timerElement.textContent = "00:00:00";
        timerElement.style.display = "none"; // 隐藏时间条

        const blob = new Blob(recordedChunks, { type: "video/webm" });
        const url = URL.createObjectURL(blob);
        document.getElementById("exportVideo").src = url;
        document.getElementById("playVideo").disabled = false;
        document.getElementById("uploadVideo").disabled = false;
        isRecording = false;
        isPaused = false;
        document.getElementById("startRecord").disabled = false;
        document.getElementById("pauseRecord").disabled = true;
        document.getElementById("resumeRecord").disabled = true;
        document.getElementById("stopRecord").disabled = true;
      };
    }
  });

  // 预览视频
  document.getElementById("playVideo").addEventListener("click", () => {
    const videoElement = document.getElementById("exportVideo");
    videoElement.play();
  });

  // 上传视频
  document.getElementById("uploadVideo").addEventListener("click", () => {
    let blob, fileName;

    if (uploadedFile) {
      // 如果是上传的视频文件
      blob = uploadedFile;
      fileName = uploadedFile.name; // 使用上传文件的原始名称
    } else if (recordedChunks.length > 0) {
      // 如果是录制的视频
      blob = new Blob(recordedChunks, { type: "video/mp4" });
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      fileName = `recorded_video_${timestamp}.mp4`; // 使用时间戳命名
    } else {
      alert("没有可上传的视频");
      return;
    }

    // 创建FormData对象并上传
    const formData = new FormData();
    formData.append("video", blob, fileName);

    // 调用后端接口上传视频
    fetch("/upload", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("上传失败，服务器返回错误状态");
        }
        return response.json();
      })
      .then((data) => {
        alert("视频上传成功，后端返回结果：" + JSON.stringify(data));
        // 上传成功后启用处理按钮
        document.getElementById("processVideo").disabled = false;
      })
      .catch((error) => {
        console.error("视频上传失败：", error);
        alert("视频上传失败，请重试。");
      });
  });

  // 处理视频
document.getElementById("processVideo").addEventListener("click", () => {
  console.log("处理视频按钮被点击");  // 添加日志输出

  const data = {
    udp_ip: "127.0.0.1",
    udp_port: 5053,
    target_fps: 15
  };

  // 调用后端接口处理视频
  fetch("/process", {
    method: "POST",
    headers: {
      "Content-Type": "application/json", // 设置请求头为application/json
    },
    body: JSON.stringify(data), // 将数据转换为JSON字符串
  })
  .then((response) => {
    if (!response.ok) {
      throw new Error("视频处理启动失败");
    }
    return response.json();
  })
  .then((data) => {
    alert("视频处理已启动：" + JSON.stringify(data));
    // 禁用处理按钮防止重复点击
    document.getElementById("processVideo").disabled = true;
  })
  .catch((error) => {
    console.error("视频处理失败：", error);
    alert("视频处理失败，请重试。");
  });
});

  // 文件上传逻辑
  document.getElementById("uploadFile").addEventListener("click", () => {
    const fileInput = document.getElementById("fileInput");
    if (fileInput.files.length === 0) {
      alert("请选择一个视频文件");
      return;
    }

    const file = fileInput.files[0];
    const videoURL = URL.createObjectURL(file);

    // 显示上传的视频
    const exportVideo = document.getElementById("exportVideo");
    exportVideo.src = videoURL;
    exportVideo.controls = true;

    // 缓存上传的文件
    uploadedFile = file;

    // 启用预览和上传按钮
    document.getElementById("playVideo").disabled = false;
    document.getElementById("uploadVideo").disabled = false;

    // 清空录制的视频块（如果存在）
    recordedChunks = [];
  });
//显示选择的视频文件
  document.getElementById('fileInput').addEventListener('change', function() {
    const filenameDisplay = document.getElementById('filenameDisplay');
    if (this.files.length > 0) {
        const filename = this.files[0].name;
        filenameDisplay.textContent = `${filename}`;
    } else {
        filenameDisplay.textContent = '未选择任何文件';
    }
});
})();