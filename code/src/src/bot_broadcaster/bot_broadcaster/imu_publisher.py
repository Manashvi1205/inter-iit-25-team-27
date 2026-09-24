import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import serial

class BNO055RosNode(Node):
    def __init__(self):
        super().__init__('bno055_serial_node')
        self.publisher_ = self.create_publisher(Imu, '/imu', 10)
        self.ser = serial.Serial('/dev/mega2', 115200, timeout=1)
        self.timer = self.create_timer(0.1, self.timer_callback)

    def timer_callback(self):
        if self.ser.in_waiting > 0:
            line = self.ser.readline().decode('utf-8').strip()
            try:
                values = [float(x) for x in line.split(',')]
                if len(values) != 10:
                    return
                imu_msg = Imu()

                # Orientation
                imu_msg.orientation.x = values[0]
                imu_msg.orientation.y = values[1]
                imu_msg.orientation.z = values[2]
                imu_msg.orientation.w = values[3]

                # Angular velocity
                imu_msg.angular_velocity.x = values[4]
                imu_msg.angular_velocity.y = values[5]
                imu_msg.angular_velocity.z = values[6]
                
                # Linear acceleration
                imu_msg.linear_acceleration.x = values[7]
                imu_msg.linear_acceleration.y = values[8]
                imu_msg.linear_acceleration.z = values[9]
                self.get_logger().info("imu")

                self.publisher_.publish(imu_msg)
            except Exception as e:
                self.get_logger().warn(f'Failed to parse: {line}, error: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = BNO055RosNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()