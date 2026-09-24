from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'bot_broadcaster'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='xyz',
    maintainer_email='xyz@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'joint_states_publisher = bot_broadcaster.joint_states_publisher:main',
            'imu_publisher = bot_broadcaster.imu_publisher:main',
            'odom_publisher = bot_broadcaster.odom_publisher:main',
            'cmd_vel_uno = bot_broadcaster.cmd_vel_uno:main',
        ],
    },
)
