from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([
        Node(
            package='bot_broadcaster',            
            executable='joint_states_publisher',
            name='joint_state_publisher_node',
            output='screen'
        ),
        Node(
            package='bot_broadcaster',
            executable='imu_publisher',
            name='imu_publisher_node',
            output='screen'
        ),
        Node(
            package='bot_broadcaster',
            executable='odom_publisher',
            name='odom_publisher_node',
            output='screen'
        ),
        Node(
            package='bot_broadcaster',
            executable='cmd_vel_uno',
            name='cmd_vel_uno_node',
            output='screen'
        )
    ])
