import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Hardware I2C packages
try:
    import board
    import busio
    import adafruit_amg88xx
    HAS_AMG = True
except (ImportError, NotImplementedError, AttributeError):
    HAS_AMG = False


class ThermalPublisher(Node):
    def __init__(self):
        super().__init__('thermal_publisher')
        
        self.declare_parameter('use_sim', False)
        self.declare_parameter('threshold', 30.0)
        self.use_sim = self.get_parameter('use_sim').get_parameter_value().bool_value
        self.threshold = self.get_parameter('threshold').get_parameter_value().double_value

        self.sensor = None
        if HAS_AMG and not self.use_sim:
            try:
                i2c_bus = busio.I2C(board.SCL, board.SDA)
                self.sensor = adafruit_amg88xx.AMG88XX(i2c_bus)
                self.get_logger().info("Hardware AMG8833 thermal sensor connected via I2C.")
            except Exception as e:
                self.get_logger().warn(f"Failed to connect AMG8833 sensor: {e}. Falling back to simulation.")
                self.sensor = None
        else:
            self.get_logger().info("Thermal Publisher started in SIMULATION mode.")

        # ROS Publisher
        self.publisher_ = self.create_publisher(String, 'thermal_data', 10)
        
        # In simulation, subscribe to a simulated raw grid or coordinate if available
        self.sim_thermal_sub = self.create_subscription(
            String, 'sim_thermal_command', self.sim_command_callback, 10
        )
        self.sim_command = "N"

        # Timer to publish data every 1 second
        self.timer = self.create_timer(1.0, self.publish_thermal_data)
        self.get_logger().info("Thermal Publisher Node Initialized")

    def sim_command_callback(self, msg):
        self.sim_command = msg.data.strip()

    def publish_thermal_data(self):
        if self.sensor is not None:
            direction = self.analyze_sensor_data()
        else:
            direction = self.sim_command

        msg = String()
        msg.data = direction
        self.publisher_.publish(msg)
        if direction != "N":
            self.get_logger().info(f"Published Thermal Command: {msg.data}")

    def analyze_sensor_data(self):
        try:
            sensor_data = self.sensor.pixels
        except Exception as e:
            self.get_logger().error(f"Error reading I2C sensor: {e}")
            return "N"

        threshold = self.threshold
        total_pixels = len(sensor_data) * len(sensor_data[0])
        above_threshold = sum(1 for row in sensor_data for pixel in row if pixel > threshold)

        # All dots below threshold
        if above_threshold < 0.05 * total_pixels:
            return "N"

        # If >50% pixels above threshold -> Close enough to shoot!
        if above_threshold >= 0.5 * total_pixels:
            return "S"

        left_count = sum(1 for row in sensor_data for i in range(4) if row[i] > threshold)
        right_count = sum(1 for row in sensor_data for i in range(4, 8) if row[i] > threshold)
        center_count = sum(1 for row in sensor_data for i in range(2, 6) if row[i] > threshold)

        if center_count > left_count and center_count > right_count:
            return f"F{center_count}"
        elif left_count > right_count:
            return "L"
        else:
            return "R"


def main(args=None):
    rclpy.init(args=args)
    node = ThermalPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down Thermal Publisher")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
