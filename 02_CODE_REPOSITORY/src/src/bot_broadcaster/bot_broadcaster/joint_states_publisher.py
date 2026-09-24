#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist 

class JointStateFromOdom(Node):
    def __init__(self):
        super().__init__('joint_state_from_odom')
        # params
        self.declare_parameter('wheel_base', 0.431) # meters 
        self.declare_parameter('wheel_radius', 0.05) # meters
        self.declare_parameter('max_wheel_speed', 20.0) # rad/s

        self.wheel_base = self.get_parameter('wheel_base').get_parameter_value().double_value
        self.wheel_radius = self.get_parameter('wheel_radius').get_parameter_value().double_value
        self.max_wheel_speed = self.get_parameter('max_wheel_speed').get_parameter_value().double_value

        self.joint_names = ['base_right_wheel_joint', 'base_left_wheel_joint']

        # publisher for joint_states
        self.pub = self.create_publisher(JointState, '/joint_states', 10)

        # subscribe to odom 
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        self.get_logger().info('JointStateFromOdom started: listening to /odom and publishing /joint_states')

    def odom_callback(self, msg: Odometry):
        twist: Twist = msg.twist.twist

        v = twist.linear.x # forward linear velocity (m/s)
        omega = twist.angular.z # yaw angular velocity (rad/s)

        # wheel linear velocities (m/s)
        half_L = self.wheel_base / 2.0
        v_l = v - omega * half_L
        v_r = v + omega * half_L

        # linear velocities -> wheel angular velocities (rad/s)
        if self.wheel_radius == 0.0:
            self.get_logger().error('wheel_radius parameter is zero — cannot compute wheel speeds')
            return

        w_l = v_l / self.wheel_radius
        w_r = v_r / self.wheel_radius

        w_l = max(-self.max_wheel_speed, min(self.max_wheel_speed, w_l))
        w_r = max(-self.max_wheel_speed, min(self.max_wheel_speed, w_r))

        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = self.joint_names
        js.velocity = [w_r, w_l]

        self.pub.publish(js)

def main(args=None):
    rclpy.init(args=args)
    node = JointStateFromOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt, shutting down.')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
