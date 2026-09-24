#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String,Float32
import serial
import time
import math

class CmdVelToSerial(Node):
    def __init__(self):
        super().__init__('cmd_vel_uno')
        # Params
        self.declare_parameter('serial_port', '/dev/mega1')
        self.declare_parameter('baudrate', 19200) # baud rate
        self.declare_parameter('wheel_base', 0.431) # meters 
        self.declare_parameter('wheel_radius', 0.05) # meters 
        self.declare_parameter('max_wheel_speed', 20.0) # rad/s 
        self.declare_parameter('stop_timeout_s', 0.3)   
        self.declare_parameter('resend_rate_hz', 10.0) # how often to resend last cmd_vel

        port = self.get_parameter('serial_port').get_parameter_value().string_value
        baud = self.get_parameter('baudrate').get_parameter_value().integer_value
        self.wheel_base = self.get_parameter('wheel_base').get_parameter_value().double_value
        self.wheel_radius = self.get_parameter('wheel_radius').get_parameter_value().double_value
        self.max_wheel_speed = self.get_parameter('max_wheel_speed').get_parameter_value().double_value
        self.stop_timeout_s = self.get_parameter('stop_timeout_s').get_parameter_value().double_value
        self.resend_rate_hz = self.get_parameter('resend_rate_hz').get_parameter_value().double_value

        # serial port
        try:
            self.ser = serial.Serial(port, baud, timeout=0.05)
            time.sleep(0.1)
            self.get_logger().info(f'Opened serial {port} @ {baud}')
        except Exception as e:
            self.ser = None
            self.get_logger().error(f'Could not open serial {port}: {e}')

        # state
        self.last_cmd_time = self.get_clock().now()
        self.last_twist = Twist()
        self.node_rate_hz = float(self.resend_rate_hz)
        self.w_n = 0.0 

        # subscriber
        self.create_subscription(Twist, '/cmd_vel', self.cmdvel_cb, 10)
        self.create_subscription(Float32, '/z_camera', self._z_camera_cb, 10)

        # timer to resend and check timeout
        self.create_timer(1.0 / self.node_rate_hz, self.timer_cb)

    def cmdvel_cb(self, msg: Twist):
        # store last and then immediately send
        self.last_twist = msg
        self.last_cmd_time = self.get_clock().now()
        self._send_twist_as_M(msg)

    def timer_cb(self):
        now = self.get_clock().now()
        dt = (now - self.last_cmd_time).nanoseconds / 1e9
        self._send_twist_as_M(self.last_twist)
        if self.ser and self.ser.in_waiting:
            try:
                line = self.ser.readline().decode('ascii', errors='ignore').strip()
                if line:
                    msg = String()
                    msg.data = line
            except Exception as e:
                self.get_logger().warn(f"Serial read error: {e}")

    def _send_twist_as_M(self, twist: Twist):
        v = twist.linear.x
        omega = twist.angular.z

        # compute wheel linear velocities
        v_l = v - omega * (self.wheel_base / 2.0)
        v_r = v + omega * (self.wheel_base / 2.0)

        # convert linear (m/s) to wheel angular vel (rad/s)
        if self.wheel_radius == 0:
            self.get_logger().error("wheel_radius is zero!")
            return
        w_l = v_l / self.wheel_radius
        w_r = v_r / self.wheel_radius

        # bounding the values 
        w_l = max(-self.max_wheel_speed, min(self.max_wheel_speed, w_l))
        w_r = max(-self.max_wheel_speed, min(self.max_wheel_speed, w_r))

        # scale rad/s to int PWM in -255..255
        scale = 255.0 / self.max_wheel_speed if self.max_wheel_speed != 0 else 0.0
        pwm_l = int(round(w_l * scale))
        pwm_r = int(round(w_r * scale))

        # clamp to allowed PWM range
        pwm_l = max(-255, min(255, pwm_l))
        pwm_r = max(-255, min(255, pwm_r))
        pwm_n = self.w_n

        self._send_M(pwm_l, pwm_r, pwm_n)

    def _send_M(self, w_l, w_r, w_n):
        if not self.ser:
            return
        try:
            packet = f"{int(w_l)},{int(w_r)},{int(w_n)}\n".encode('ascii')
            self.ser.write(packet)
        except Exception as e:
            self.get_logger().error(f"Serial write error: {e}")
            
    # z_camera callback stores last value in self.w_n
    def _z_camera_cb(self, msg: Float32):
        try:
            self.w_n = float(msg.data)
        except:
            self.w_n = 0.0   # default if anything goes wrong


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToSerial()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()