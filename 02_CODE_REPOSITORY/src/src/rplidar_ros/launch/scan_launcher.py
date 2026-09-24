#!/usr/bin/env python3
# scan_listener.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import math
import threading
import time

class ScanListener(Node):
    def __init__(self):
        super().__init__('scan_listener')

        # NOTE: Many LIDARs publish with Best Effort; match QoS if needed.
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        # Subscribe to the LIDAR scan topic (change '/scan' to your topic name if different)
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos
        )

        # store newest scan thread-safely
        self.latest_scan = None
        self._scan_lock = threading.Lock()

        # Example timer: run your nav2-compatible processing at 5 Hz using latest scan
        self.process_timer = self.create_timer(1.0/5.0, self.process_latest_scan)

        self.get_logger().info('Scan listener started, subscribing to /scan')

    def scan_callback(self, msg: LaserScan):
        """Called continuously for every incoming LaserScan message."""
        # quick sanity log (every few seconds)
        if time.time() % 10 < 0.05:
            self.get_logger().debug(f"scan received: angle_min={msg.angle_min:.2f} angle_inc={msg.angle_increment:.4f} ranges={len(msg.ranges)}")

        # store the whole message for later processing (thread-safe)
        with self._scan_lock:
            self.latest_scan = msg

        # Option A: do immediate processing here (fast checks / interrupts)
        # e.g., quick obstacle check in front:
        # check indexes around 0 angle (depends on your lidar orientation)
        mid_index = int((0.0 - msg.angle_min) / msg.angle_increment)
        window = 5
        ranges_window = msg.ranges[max(0, mid_index-window) : min(len(msg.ranges), mid_index+window+1)]
        # if any close obstacle within 0.3m in front -> emergency
        if any(r is not None and r < 0.3 for r in ranges_window):
            self.get_logger().warn('Immediate obstacle detected <0.3m in front!')

    def process_latest_scan(self):
        """Called periodically to run heavier algorithm using the latest scan."""
        with self._scan_lock:
            scan = self.latest_scan

        if scan is None:
            # no scan yet
            return

        # Convert ranges -> (x,y) points in laser frame
        points = []
        angle = scan.angle_min
        for r in scan.ranges:
            # LaserScan may contain 'inf' or 0.0 for no-return; skip them
            if r == float('inf') or r == 0.0 or math.isnan(r):
                angle += scan.angle_increment
                continue
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            points.append((x, y))
            angle += scan.angle_increment

        # Example: compute nearest obstacle distance and direction
        if points:
            nearest = min(points, key=lambda p: math.hypot(p[0], p[1]))
            dist = math.hypot(nearest[0], nearest[1])
            bearing = math.atan2(nearest[1], nearest[0])
            self.get_logger().info(f'Nearest obstacle at {dist:.2f} m, bearing {math.degrees(bearing):.1f}° (using latest scan)')

        # --- place here whatever nav algorithm you need ---
        # e.g., build occupancy grid slice, feed your local planner, update costmap via topics, etc.


def main(args=None):
    rclpy.init(args=args)
    node = ScanListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

