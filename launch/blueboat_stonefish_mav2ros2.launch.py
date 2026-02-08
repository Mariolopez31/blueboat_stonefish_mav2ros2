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

    # A) TU PUENTE (El script de Python que me has pasado arriba)
    sim_bridge_node = Node(
        package='blueboat_stonefish_mav2ros2',
        executable='stonefish_bridge', # Busca la entrada en setup.py
        name='stonefish_bridge',
        output='screen',
        parameters=[
            {'mavlink_ip': '127.0.0.1'}, 
            {'mavlink_port': 14551}
        ]
    )

    # B) MAVROS (El estándar de ROS)
    mavros_node = Node(
            package='mavros',
            executable='mavros_node',
            output='screen',
            # Quitamos namespace='mavros' para que coincida con tu YAML
            parameters=[
                mavros_config, 
                # Forzamos la URL limpia sin puerto de salida fijo (@) para evitar el "Busy"
                {'fcu_url': 'udp://@127.0.0.1:14560'},
                {'target_system_id': 1},
                {'target_component_id': 1}
            ]
        )

    # C) JOYSTICK DRIVER (Lee el USB del mando)
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{'deadzone': 0.05}]
    )

    # D) TELEOP (Convierte botones en velocidad cmd_vel)
    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        parameters=[joy_config], # Carga el YAML del joystick
        remappings=[
            # REDIRIGIMOS: Lo que sale de teleop va a la entrada de MAVROS
            ('/cmd_vel', '/mavros/setpoint_velocity/cmd_vel_unstamped')
        ]
    )

    # 3. Retornamos la descripción para que ROS ejecute todo
    return LaunchDescription([
        fcu_url_arg,
        sim_bridge_node,
        mavros_node,
        joy_node,
        teleop_node
    ])