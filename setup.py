from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'blueboat_stonefish_mav2ros2'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # 1. Registro del paquete en ament (Boilerplate estándar de ROS)
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        # 2. INSTALAR LAUNCH FILES
        # Copia todo lo que termine en .launch.py de la carpeta 'launch'
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        
        # 3. INSTALAR CONFIG FILES (.yaml)
        # Copia todo lo que termine en .yaml de la carpeta 'config'
        # ¡Esto es vital para tu joystick.yaml y mavros_blueboat.yaml!
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mariolopez31',
    maintainer_email='al427817@uji.es',
    description='Paquete de integracion Stonefish con ArduPilot y MAVROS',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Aquí definimos los ejecutables para 'ros2 run'
            # Nombre_del_nodo = carpeta_python.nombre_archivo:funcion_main
            
            'stonefish_bridge = blueboat_stonefish_mav2ros2.stonefish_bridge:main',
        ],
    },
)