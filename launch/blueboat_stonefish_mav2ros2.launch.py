import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Obtenemos la ruta de tu paquete y configs
    pkg_share = get_package_share_directory('blueboat_stonefish_mav2ros2')
    
    mavros_config = os.path.join(pkg_share, 'config', 'mavros_blueboat.yaml')
    joy_config = os.path.join(pkg_share, 'config', 'joystick.yaml')

    # 2. Argumentos de lanzamiento (IPs y Puertos)
    fcu_url_arg = DeclareLaunchArgument(
        'fcu_url',
        default_value='udp://127.0.0.1:14551@14555', # Conexión con ArduPilot
        description='URL de conexión MAVLink'
    )

    # --- DEFINICIÓN DE NODOS ---

    sim_bridge_node = Node(
        package='blueboat_stonefish_mav2ros2',
        executable='stonefish_bridge', 
        name='stonefish_bridge',
        output='screen',
        parameters=[
            {'mavlink_ip': '127.0.0.1'}, 
            {'mavlink_port': 14551}
        ]
    )

    mavros_node = Node(
            package='mavros',
            executable='mavros_node',
            output='screen',
            parameters=[
                mavros_config, 
                {'fcu_url': 'udp://@127.0.0.1:14560'},
                {'target_system_id': 1},
                {'target_component_id': 1}
            ]
        )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{'deadzone': 0.05}]
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[joy_config],
        remappings=[
            ('/cmd_vel', '/mavros/setpoint_velocity/cmd_vel_unstamped')
        ]
    )

    return LaunchDescription([
        fcu_url_arg,
        sim_bridge_node,
        mavros_node,
        joy_node,
        teleop_node
    ])