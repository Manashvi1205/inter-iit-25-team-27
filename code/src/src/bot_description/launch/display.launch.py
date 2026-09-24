import launch
import launch_ros
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution
import os
import xacro

package_name = 'bot_description'

xacroRelativePath = 'urdf/my_robot.urdf.xacro'

rvizConfigRelativePath = 'rviz/config.rviz'

def generate_launch_description():
    pkgPath = launch_ros.substitutions.FindPackageShare(package=package_name).find(package_name)
    odometry_source = LaunchConfiguration("odometry_source", default=True)
    xacroModelPath = os.path.join(pkgPath, xacroRelativePath)
    rvizConfigPath = os.path.join(pkgPath, rvizConfigRelativePath)
    worldPath = os.path.join(pkgPath, 'worlds', 'arena.world')

    robot_desc = xacro.process_file(xacroModelPath).toxml()

    robot_description = {'robot_description': robot_desc}

    # Launch arguments
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(name="gui", default_value="true", description="Start the Rviz GUI")
    )

    gui = LaunchConfiguration("gui")
    gui_config = os.path.join(
        pkgPath,
        'config',
        'world.config'
    )

    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_ros.substitutions.FindPackageShare(package="ros_gz_sim").find("ros_gz_sim"), "/launch/gz_sim.launch.py"]),
        launch_arguments={
            'gz_args': f'-r {worldPath} -v 4',
        }.items(),
        
    )
    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [launch_ros.substitutions.FindPackageShare(package="ros_gz_sim").find("ros_gz_sim"), "/launch/gz_sim.launch.py"]
        ),
        launch_arguments={
            'gz_args': f'-g --gui-config {gui_config} -v3'
        }.items()
    )
    

    gazebo_bridge = launch_ros.actions.Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist",
            "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
            "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
            "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
            "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
            "/world/my_arena_world/model/my_robot/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model"
            ],
        output="screen",
        remappings=[
            ('/world/my_arena_world/model/my_robot/joint_state', '/joint_states'),
            ('/scan','my_robot/scan')
            ]
    )

    # Spawn robot
    gz_spawn_entity = launch_ros.actions.Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "/robot_description",
            "-name", "my_robot",
            "-allow-remaining", "true",
            '-z', '0.4',
            "-x", "0.0"
        ]
    )

    # Publish robot description
    robot_state_publisher_node = launch_ros.actions.Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[robot_description],
    )

    # RViz 
    rviz_node = launch_ros.actions.Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=['-d', rvizConfigPath]
    )

    nodeList = [gazebo_headless,
        robot_state_publisher_node,
        gz_spawn_entity,
        gazebo_bridge,
        rviz_node,
    ]
    
    return launch.LaunchDescription(declared_arguments + nodeList)
