 --> Start TCP in venv


cd your/project/
source venv/bin/activate
python3 vision_tcp_server.py
[see tthis=--> [VISION SERVER] Running on 127.0.0.1:9090 ]




----> ROS Side (system python)


from vision_tcp_client import VisionTCPClient

vision = VisionTCPClient()

vision.capture(1.0, 0.5)
vision.wait_done()
vision.led("red")
vision.shutdown()

===


🚀 You're now ready to run:
Terminal 1 (inside venv):
python3 vision_tcp_server.py

Terminal 2 (ROS):
ros2 run <your_pkg> z_control_service