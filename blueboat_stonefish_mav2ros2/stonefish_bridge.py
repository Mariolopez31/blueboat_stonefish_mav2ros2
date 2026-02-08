#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, Imu
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray 
from pymavlink import mavutil

class SimBridge(Node):
    def __init__(self):
        super().__init__('stonefish_ardupilot_bridge')

        # --- PARÁMETROS DE CONEXIÓN ---
        self.declare_parameter('mavlink_ip', '127.0.0.1')
        self.declare_parameter('mavlink_port', 14551)
        
        ip = self.get_parameter('mavlink_ip').value
        port = self.get_parameter('mavlink_port').value
        
        connection_str = f'udpin:{ip}:{port}'
        self.get_logger().info(f'Conectando a ArduPilot en {connection_str}...')
        
        # Conexión UDP
        self.mav = mavutil.mavlink_connection(connection_str)
        self.mav.wait_heartbeat()
        self.get_logger().info('¡Conectado a ArduPilot SITL!')
        
        self.thruster_pub = self.create_publisher(Float64MultiArray, '/blueboat/controller/thruster_setpoints_sim', 10)

        self.create_subscription(NavSatFix, '/blueboat/gps', self.gps_callback, 10)
        self.create_subscription(Odometry, '/blueboat/navigator/odometry', self.odom_callback, 10)
        self.create_subscription(Imu, '/blueboat/imu/data', self.imu_callback, 10)

        # --- TIMER (Bucle de Control) ---
        # 50 Hz para procesar comandos de motores
        self.create_timer(0.02, self.control_loop) 

        # Variables para almacenar estado temporal
        self.current_vel = [0.0, 0.0, 0.0]

    def odom_callback(self, msg):
        # Guardamos velocidad lineal para mejorar la estimación del EKF de ArduPilot
        self.current_vel = [
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z
        ]

    def imu_callback(self, msg):
        # Enviamos la orientación real (Cuaterniones) a ArduPilot
        # Esto evita que el horizonte artificial "baile" o derive
        q = msg.orientation
        self.mav.mav.sim_state_send(
            q.w, q.x, q.y, q.z,
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
            0, 0, 0 # Lat/Lon se ignoran aquí (van en el mensaje GPS)
        )

    def gps_callback(self, msg):
        # Callback principal de posición
        if msg.status.status < 0:
            return # Si Stonefish dice que no hay GPS, no enviamos nada

        lat = int(msg.latitude * 1e7)
        lon = int(msg.longitude * 1e7)
        alt = int(msg.altitude * 1000) # mm

        # Enviamos GPS_INPUT a ArduPilot
        # Flags: 1(time), 8(vel horiz), 16(vel vert), 32(pos)
        self.mav.mav.gps_input_send(
            0, 0, 
            (1 | 8 | 16 | 32), 
            0, 0, 3, # Fix 3D
            lat, lon, alt,
            1.0, 1.0, 
            self.current_vel[0], self.current_vel[1], self.current_vel[2], 
            0, 0, 0, 12 # 12 Satélites visibles
        )

    def control_loop(self):
        """Lee PWM de ArduPilot -> Envía Setpoint Normalizado (-1 a 1) a Stonefish"""
        if self.mav.recv_match(type='SERVO_OUTPUT_RAW', blocking=False):
            msg = self.mav.messages.get('SERVO_OUTPUT_RAW')
            if msg:
                # 1. Obtener PWM (suelen ser los canales 1 y 3)
                pwm_left = msg.servo1_raw
                pwm_right = msg.servo3_raw

                # 2. Normalizar PWM (1100 a 1900) -> Rango (-1.0 a 1.0)
                # Usamos 1500 como centro y 400 como rango (1500 +/- 400)
                u_left = (pwm_left - 1500) / 400.0
                u_right = (pwm_right - 1500) / 400.0

                # 3. Limitar valores por seguridad (clamping)
                u_left = max(min(u_left, 1.0), -1.0)
                u_right = max(min(u_right, 1.0), -1.0)
                
                # 4. Publicar directamente el valor normalizado
                # Stonefish recibirá este número, verá que max_setpoint es 387.4, 
                # y multiplicará (u_left * 387.4) para buscar en la tabla de Newtons.
                thrust_msg = Float64MultiArray()
                thrust_msg.data = [u_left, u_right]
                
                self.thruster_pub.publish(thrust_msg)

def main(args=None):
    rclpy.init(args=args)
    node = SimBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()