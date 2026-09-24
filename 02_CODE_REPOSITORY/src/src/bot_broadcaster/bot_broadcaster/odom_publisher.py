#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from rclpy.time import Time
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Quaternion
from tf2_ros import TransformBroadcaster
from std_msgs.msg import Float32MultiArray

try:
    import serial
except Exception:
    serial = None


def yaw_to_quaternion(yaw: float) -> Quaternion:
    # basic yaw -> quaternion (only z-rotation)
    # yaw in radians
    half = yaw * 0.5
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(half)
    q.w = math.cos(half)
    return q


def shortest_angular_distance(a, b):
    # normalize angle difference into [-pi, pi]
    diff = b - a
    while diff > math.pi:
        diff -= 2.0 * math.pi
    while diff <= -math.pi:
        diff += 2.0 * math.pi
    return diff


class OdomNode(Node):
    def __init__(self):
        super().__init__('odom_node')

        # params
        self.declare_parameter('port', '/dev/mega3')
        self.declare_parameter('baud', 115200)            
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')
        self.declare_parameter('pose_cov_xy', 0.00)
        self.declare_parameter('pose_cov_y', 0.0)
        self.declare_parameter('pose_cov_yaw', 0.0)

        # read params
        self.port = self.get_parameter('port').get_parameter_value().string_value
        self.baud = self.get_parameter('baud').get_parameter_value().integer_value
        self.odom_frame = self.get_parameter('odom_frame').get_parameter_value().string_value
        self.base_frame = self.get_parameter('base_frame').get_parameter_value().string_value

        cov_xy = self.get_parameter('pose_cov_xy').get_parameter_value().double_value
        cov_y = self.get_parameter('pose_cov_y').get_parameter_value().double_value
        cov_yaw = self.get_parameter('pose_cov_yaw').get_parameter_value().double_value

        # publisher and TF
        self.odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.height_pub = self.create_publisher(Float32MultiArray, 'height', 10)

        # covariances setup
        self.pose_cov = [0.0] * 36
        self.twist_cov = [0.0] * 36
        self.pose_cov[0] = cov_xy
        self.pose_cov[7] = cov_y
        self.pose_cov[35] = cov_yaw
        self.twist_cov = list(self.pose_cov)

        # state for finite-difference velocity
        self.prev_x = None
        self.prev_y = None
        self.prev_theta = None
        self.prev_time = None

        # serial setup
        self.ser = None
        if serial is None:
            self.get_logger().error("pyserial not installed. Install `pyserial` to read from serial.")
        else:
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                self.get_logger().info(f"Read line: '{line}'")
                self.get_logger().info(f"Opened serial {self.port} @ {self.baud}")
            except Exception as e:
                self.get_logger().error(f"Failed to open serial {self.port}: {e}")
                self.ser = None
        
        # timer polls serial (100 ms)
        self.create_timer(0.10, self.timer_cb)

    def timer_cb(self):
        if self.ser is None:
            return
        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line =='': return
            self.get_logger().info(f"Read line: '{line}'")
        except Exception as e:
            self.get_logger().warn(f"Serial read failed: {e}")
            return

        if not line:
            return
        
        # allow lines starting with "ODOM:" or just numbers
        if line.upper().startswith('ODOM'):
            rest = line[4:].lstrip(':').strip()
        else:
            rest = line

        # accept comma and white seperated values
        rest = rest.replace(',', ' ')
        parts = rest.split()
        self.get_logger().info(f"Parsing odom data: '{parts}'")
        if len(parts) < 3:
            self.get_logger().debug(f"Ignoring bad serial line: '{line}'")
            return
        
        # basic parse
        try:
            x = float(parts[0])
            y = float(parts[1])
            theta_raw = float(parts[2])
        except ValueError:
            self.get_logger().debug(f"Could not parse numbers from: '{line}'")
            return

        # degrees -> radians conversion
        theta = theta_raw
        z_value = None
        center_ticks = None
        center_angle_deg = None
        now = self.get_clock().now()
        if len(parts) >= 4:
            try:
                possible_heading = float(parts[3])
                z_value = float(parts[2])
                theta = possible_heading 
                # indices: 0:x 1:y 2:z 3:heading 4:L_ticks 5:R_ticks 6:C_ticks 7:L_ang 8:R_ang 9:C_ang
                if len(parts) > 6:
                    try:
                        center_ticks = float(parts[6])
                    except Exception:
                        center_ticks = None
                if len(parts) > 9:
                    try:
                        center_angle_deg = float(parts[9])
                    except Exception:
                        center_angle_deg = None
            except Exception:
                z_value = None
                if len(parts) > 5:
                    try:
                        center_ticks = float(parts[5])
                    except Exception:
                        center_ticks = None
                if len(parts) > 8:
                    try:
                        center_angle_deg = float(parts[8])
                    except Exception:
                        center_angle_deg = None
        else:
            if len(parts) > 5:
                try:
                    center_ticks = float(parts[5])
                except Exception:
                    center_ticks = None
            if len(parts) > 8:
                try:
                    center_angle_deg = float(parts[8])
                except Exception:
                    center_angle_deg = None

        # defaults if not present
        if center_ticks is None:
            center_ticks = 0.0
        if center_angle_deg is None:
            center_angle_deg = 0.0

        # velocity via finite differences
        now = self.get_clock().now()
        vx = 0.0
        vy = 0.0
        wz = 0.0
        if self.prev_time is None:
            self.prev_x = x
            self.prev_y = y
            self.prev_theta = theta
            self.prev_time = now
        else:
            dt = (now - self.prev_time).nanoseconds / 1e9
            if dt > 1e-6:
                dx = x - self.prev_x
                dy = y - self.prev_y

                # rotate into robot frame
                cos_th = math.cos(self.prev_theta)
                sin_th = math.sin(self.prev_theta)
                forward = dx * cos_th + dy * sin_th
                lateral = -dx * sin_th + dy * cos_th
                vx = forward / dt
                vy = lateral / dt
                dtheta = shortest_angular_distance(self.prev_theta, theta)
                wz = dtheta / dt
            self.prev_x = x
            self.prev_y = y
            self.prev_theta = theta
            self.prev_time = now

        # fill odom message
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame

        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y

        # if z_value present, use it, else (0.0)
        odom.pose.pose.position.z = 0.0 if z_value is None else float(z_value)

        odom.pose.pose.orientation = yaw_to_quaternion(theta)
        odom.pose.covariance = self.pose_cov

        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = wz
        odom.twist.covariance = self.twist_cov

        self.odom_pub.publish(odom)

        # broadcast tf odom -> base_link 
        t = TransformStamped()
        t.header.stamp = now.to_msg()
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = odom.pose.pose.position.x
        t.transform.translation.y = odom.pose.pose.position.y
        t.transform.translation.z = odom.pose.pose.position.z
        t.transform.rotation = odom.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)

        # publish height topic
        hmsg = Float32MultiArray()
        hmsg.data = [float(z_value),float(center_ticks), float(center_angle_deg)]
        self.height_pub.publish(hmsg)


def main(args=None):
    rclpy.init(args=args)
    node = OdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.ser:
            try:
                node.ser.close()
            except Exception:
                pass
        node.destroy_node()
        rclpy.shutdown()