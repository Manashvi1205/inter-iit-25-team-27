import launch
import launch_ros
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import os
import xacro
from launch.conditions import IfCondition
from ament_index_python.packages import get_package_share_directory

package_name = 'bot_description'
xacroRelativePath = 'urdf/my_robot.urdf.xacro'
rvizConfigRelativePath = 'rviz/config.rviz'

def generate_launch_description():
    pkgPath = launch_ros.substitutions.FindPackageShare(package=package_name).find(package_name)
    xacroModelPath = os.path.join(pkgPath, xacroRelativePath)
    rvizConfigPath = os.path.join(pkgPath, rvizConfigRelativePath)
    
    bringup_dir = get_package_share_directory('nav2_bringup')
    launch_dir = os.path.join(bringup_dir, 'launch')
    robot_desc = xacro.process_file(xacroModelPath).toxml()
    nav2_dir = get_package_share_directory('bot_bringup')
    robot_description = {'robot_description': robot_desc}

    # === Launch arguments ===
    slam = LaunchConfiguration('slam')
    map_yaml_file = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    async_param = LaunchConfiguration('async_param')

    declare_slam_cmd = DeclareLaunchArgument(
        'slam',
        default_value='False',
        description='Whether run a SLAM')

    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(nav2_dir, 'maps', 'map.yaml'),
        description='Full path to map yaml file to load')

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(nav2_dir, 'params', 'nav2_params.yaml'),
        description='Full path to the ROS2 parameters file to use for all launched nodes')

    declare_mapper_online_async_param_cmd = DeclareLaunchArgument(
        'async_param',
        default_value=os.path.join(nav2_dir, 'config', 'mapper_params_online_async.yaml'),
        description='Set mappers online async param file')

    # mapper include (mapping)
    mapper_online_async_param_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py'),
        ),
        launch_arguments=[('slam_params_file', LaunchConfiguration('async_param'))],
    )

    # === Publish robot description ===
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[robot_description],
    )

    # === RViz (optional) ===
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=['-d', rvizConfigPath]
    )

    # launch rplidar node (fixed to use PythonLaunchDescriptionSource)
    rp_lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rplidar_ros'), 'launch', 'rplidar_s2e_launch.py')
        )
    )

    joint_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('bot_broadcaster'), 'launch', 'joint_state_publisher.launch.py')
        )
    )

    robot_localization_node = Node(
       package='robot_localization',
       executable='ekf_node',
       name='ekf_filter_node',
       output='screen',
       parameters=[os.path.join(nav2_dir, 'config/ekf.yaml'), {'use_sim_time': False}]
    )

    # Note: DO NOT leave trailing commas here — that creates tuples
    slam_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'slam_launch.py')),
        condition=IfCondition(slam),
        launch_arguments={
            'use_sim_time': 'False',
            'autostart': 'True',
            'params_file': async_param
        }.items()
    )

    localization_launch_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'localization_launch.py')),
        condition=IfCondition(launch.substitutions.PythonExpression(['not ', slam])),
        launch_arguments={
            'map': map_yaml_file,
            'use_sim_time': 'False',
            'autostart': 'True',
            'params_file': params_file,
            'container_name': 'nav2_container'
        }.items()
    )

    nav_launch_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(launch_dir, 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'False',
            'autostart': 'True',
            'params_file': params_file,
            'container_name': 'nav2_container'
        }.items()
    )

    declared_arguments = [
        declare_slam_cmd,
        declare_map_yaml_cmd,
        declare_params_file_cmd,
        declare_mapper_online_async_param_cmd
    ]

    nodeList = [
        robot_state_publisher_node,
        rviz_node,
        rp_lidar_launch,
        joint_state_publisher_launch,
        robot_localization_node,
        # slam_node,
        # localization_launch_node,   # enable if you want localization (not SLAM)
        # nav_launch_node,
        mapper_online_async_param_launch  # include mapping launch here (if you want it always launched)
    ]

    return launch.LaunchDescription(declared_arguments + nodeList)

