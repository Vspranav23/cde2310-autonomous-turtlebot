import math
import time
import numpy as np

# ROS 2 & Middleware Abstraction (Permits both real ROS 2 and standalone simulation test execution)
try:
    import rclpy
    from rclpy.node import Node
    from nav_msgs.msg import OccupancyGrid, Odometry
    from geometry_msgs.msg import PoseStamped
    from nav2_msgs.action import NavigateToPose
    from rclpy.action import ActionClient
    from std_msgs.msg import String
    HAS_ROS = True
except (ImportError, ModuleNotFoundError):
    HAS_ROS = False
    class Node:
        def __init__(self, name):
            self._name = name
        def create_subscription(self, *args, **kwargs): return None
        def create_timer(self, *args, **kwargs): return None
        def get_logger(self):
            class L:
                def info(self, m): pass
                def warn(self, m): pass
                def error(self, m): pass
            return L()
        def declare_parameter(self, *args, **kwargs): pass
        def get_parameter(self, name):
            class P:
                class V:
                    def bool_value(self): return True
                    def double_value(self): return 30.0
                def get_parameter_value(self): return self.V()
            return P()
    class ActionClient:
        def __init__(self, *args, **kwargs): pass
        def wait_for_server(self, timeout_sec=1.0): return True
        def send_goal_async(self, goal):
            class F:
                def add_done_callback(self, cb): pass
            return F()
    class OccupancyGrid: pass
    class Odometry: pass
    class PoseStamped:
        def __init__(self):
            class H:
                stamp = None
                frame_id = 'map'
            self.header = H()
            class P:
                class Pos:
                    x = 0.0
                    y = 0.0
                    z = 0.0
                class Orient:
                    x = 0.0
                    y = 0.0
                    z = 0.0
                    w = 1.0
                position = Pos()
                orientation = Orient()
            self.pose = P()
    class NavigateToPose:
        class Goal:
            pose = None
    class String:
        def __init__(self): self.data = ""

try:
    import tf_transformations
except (ImportError, ModuleNotFoundError):
    class tf_transformations:
        @staticmethod
        def euler_from_quaternion(q):
            x, y, z, w = q
            siny_cosp = 2.0 * (w * z + x * y)
            cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
            yaw = math.atan2(siny_cosp, cosy_cosp)
            return (0.0, 0.0, yaw)

        @staticmethod
        def quaternion_from_euler(roll, pitch, yaw):
            cy = math.cos(yaw * 0.5)
            sy = math.sin(yaw * 0.5)
            return (0.0, 0.0, sy, cy)

# Hardware abstraction for GPIO
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except (ImportError, RuntimeError):
    HAS_GPIO = False


class ExplorerNode(Node):
    def __init__(self):
        super().__init__('explorer')
        self.get_logger().info("Explorer Node Started")

        # Parameters
        self.declare_parameter('is_sim', False)
        self.declare_parameter('heat_threshold', 30.0)
        self.is_sim = self.get_parameter('is_sim').get_parameter_value().bool_value

        # Subscriptions
        self.map_sub = self.create_subscription(OccupancyGrid, '/map', self.map_callback, 10)
        self.thermal_sub = self.create_subscription(String, '/thermal_data', self.thermal_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        # Action client for Nav2
        self.nav_to_pose_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Navigation state tracking
        self.is_navigating = False
        self.current_goal_handle = None
        self.active_frontier = None

        # Robot position & pose in world coordinates (meters & radians)
        self.robot_position = (0.0, 0.0)
        self.current_yaw = 0.0

        # Visited frontiers and targets
        self.visited_frontiers = set()
        self.blacklisted_frontiers = set()
        self.visited_heat_sources = []
        self.heat_source = None
        self.followingHeat = None

        # Map state
        self.map_data = None

        # Setup GPIO if running on hardware
        if HAS_GPIO and not self.is_sim:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(18, GPIO.OUT)
                GPIO.setup(17, GPIO.OUT)
                GPIO.setup(27, GPIO.OUT)
                GPIO.output(17, GPIO.HIGH)
                GPIO.output(27, GPIO.LOW)
                self.get_logger().info("Hardware GPIO initialized successfully.")
            except Exception as e:
                self.get_logger().warn(f"Failed to initialize GPIO: {e}")
        else:
            self.get_logger().info("Running in SIMULATION mode: Hardware GPIO mocked.")

        # Timer for periodic exploration / state machine
        self.timer = self.create_timer(2.0, self.check_heat_source)

    def map_callback(self, msg):
        self.map_data = msg

    def odom_callback(self, msg):
        position = msg.pose.pose.position
        self.robot_position = (position.x, position.y)

        orientation_q = msg.pose.pose.orientation
        quat = (orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w)
        roll, pitch, self.current_yaw = tf_transformations.euler_from_quaternion(quat)

    def thermal_callback(self, msg):
        self.heat_source = msg.data.strip() if msg.data else None

    def startFiring(self):
        """Non-blocking simulated or hardware firing sequence."""
        self.get_logger().info("🔥 EXECUTING TARGET FIRING SEQUENCE 🔥")
        if HAS_GPIO and not self.is_sim:
            try:
                GPIO.output(18, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(18, GPIO.LOW)
            except Exception as e:
                self.get_logger().error(f"GPIO firing error: {e}")
        else:
            self.get_logger().info("[SIMULATION] Solenoid activated -> Projectile fired!")

    def check_heat_source(self):
        """Main decision loop: prioritizing thermal targets over frontier exploration."""
        if self.map_data is None:
            self.get_logger().info("Waiting for map data...")
            return

        # If we have an active heat signature, prioritize it!
        if self.heat_source and self.heat_source != "N":
            self.get_logger().info(f"Thermal target active: {self.heat_source}")
            command = self.heat_source[0]
            
            if command == "L":
                self.turn_relative(math.pi / 4)
            elif command == "R":
                self.turn_relative(-math.pi / 4)
            elif command == "F":
                pixel_str = self.heat_source[1:]
                pixels = int(pixel_str) if pixel_str.isdigit() else 10
                
                target_x, target_y = self.getCoordinates(pixels)
                already_visited = any(
                    math.hypot(target_x - hx, target_y - hy) < 0.3
                    for (hx, hy) in self.visited_heat_sources
                )
                if already_visited:
                    self.get_logger().info("Target already visited; resuming exploration.")
                    self.explore()
                else:
                    self.move_forward(pixels)
            elif command == "S":
                self.startFiring()
                self.visited_heat_sources.append(self.robot_position)
                self.heat_source = None
                self.explore()
            return

        # No heat detected: if not currently navigating, explore frontiers
        if not self.is_navigating:
            self.explore()

    def getForwardDistance(self, pixels):
        if pixels > 32:
            return 0.1
        elif pixels > 8:
            return 0.25
        else:
            return 0.50

    def getCoordinates(self, pixels):
        robot_x, robot_y = self.robot_position
        dist = self.getForwardDistance(pixels)
        target_x = robot_x + dist * math.cos(self.current_yaw)
        target_y = robot_y + dist * math.sin(self.current_yaw)
        return (target_x, target_y)

    def move_forward(self, pixels):
        target_x, target_y = self.getCoordinates(int(pixels))
        self.followingHeat = (target_x, target_y)
        self.navigate_to(target_x, target_y, self.current_yaw)

    def turn_relative(self, angle_rad):
        new_yaw = self.current_yaw + angle_rad
        new_yaw = (new_yaw + math.pi) % (2 * math.pi) - math.pi
        self.navigate_to(self.robot_position[0], self.robot_position[1], new_yaw)

    def navigate_to(self, x, y, yaw=None):
        if yaw is None:
            yaw = self.current_yaw

        if not self.nav_to_pose_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn("Nav2 action server 'navigate_to_pose' not available.")
            return

        goal_msg = PoseStamped()
        goal_msg.header.frame_id = 'map'
        if HAS_ROS:
            goal_msg.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.position.x = float(x)
        goal_msg.pose.position.y = float(y)

        q = tf_transformations.quaternion_from_euler(0, 0, yaw)
        goal_msg.pose.orientation.x = q[0]
        goal_msg.pose.orientation.y = q[1]
        goal_msg.pose.orientation.z = q[2]
        goal_msg.pose.orientation.w = q[3]

        nav_goal = NavigateToPose.Goal()
        nav_goal.pose = goal_msg

        self.get_logger().info(f"Navigating to: ({x:.2f}, {y:.2f}), yaw={yaw:.2f}")
        send_goal_future = self.nav_to_pose_client.send_goal_async(nav_goal)
        send_goal_future.add_done_callback(self.goal_response_callback)
        self.is_navigating = True

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected by Nav2!")
            self.is_navigating = False
            if self.active_frontier:
                self.blacklisted_frontiers.add(self.active_frontier)
                self.active_frontier = None
            self.explore()
            return

        self.get_logger().info("Goal accepted by Nav2")
        self.current_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.navigation_complete_callback)

    def navigation_complete_callback(self, future):
        self.is_navigating = False
        try:
            result = future.result().result
            if self.followingHeat:
                self.visited_heat_sources.append(self.followingHeat)
                self.followingHeat = None
            self.get_logger().info(f"Navigation completed with status: {result}")
        except Exception as e:
            self.get_logger().error(f"Navigation error: {e}")

        self.explore()

    def find_frontiers(self, map_array):
        """Fast vectorized frontier detection in 2D OccupancyGrid."""
        is_free = (map_array == 0)
        is_unknown = (map_array == -1)

        has_unknown_neighbor = (
            is_unknown[:-2, :-2] | is_unknown[:-2, 1:-1] | is_unknown[:-2, 2:] |
            is_unknown[1:-1, :-2] |                        is_unknown[1:-1, 2:] |
            is_unknown[2:, :-2]  | is_unknown[2:, 1:-1]  | is_unknown[2:, 2:]
        )

        frontier_mask = is_free[1:-1, 1:-1] & has_unknown_neighbor
        rows, cols = np.where(frontier_mask)
        rows = rows + 1
        cols = cols + 1

        frontiers = list(zip(rows, cols))
        return frontiers

    def choose_frontier(self, frontiers):
        """Choose closest valid frontier using real-world Euclidean distance in METERS."""
        if not frontiers:
            return None

        robot_x, robot_y = self.robot_position
        res = self.map_data.info.resolution
        origin_x = self.map_data.info.origin.position.x
        origin_y = self.map_data.info.origin.position.y

        min_distance = float('inf')
        chosen_frontier = None

        for r, c in frontiers:
            if (r, c) in self.visited_frontiers or (r, c) in self.blacklisted_frontiers:
                continue

            fx = c * res + origin_x
            fy = r * res + origin_y
            dist = math.hypot(robot_x - fx, robot_y - fy)

            if 0.3 < dist < min_distance:
                min_distance = dist
                chosen_frontier = (r, c)

        if chosen_frontier:
            self.visited_frontiers.add(chosen_frontier)
            self.active_frontier = chosen_frontier
            self.get_logger().info(f"Selected nearest frontier at cell {chosen_frontier}, dist={min_distance:.2f}m")
        return chosen_frontier

    def explore(self):
        if self.map_data is None:
            return

        map_array = np.array(self.map_data.data).reshape(
            (self.map_data.info.height, self.map_data.info.width)
        )

        frontiers = self.find_frontiers(map_array)
        if not frontiers:
            self.get_logger().info("No frontiers detected. Exploration fully complete!")
            return

        chosen = self.choose_frontier(frontiers)
        if not chosen:
            self.get_logger().info("All current frontiers visited or blacklisted.")
            return

        goal_x = chosen[1] * self.map_data.info.resolution + self.map_data.info.origin.position.x
        goal_y = chosen[0] * self.map_data.info.resolution + self.map_data.info.origin.position.y

        yaw = math.atan2(goal_y - self.robot_position[1], goal_x - self.robot_position[0])
        self.navigate_to(goal_x, goal_y, yaw)


def main(args=None):
    if HAS_ROS:
        rclpy.init(args=args)
        explorer_node = ExplorerNode()
        try:
            rclpy.spin(explorer_node)
        except KeyboardInterrupt:
            explorer_node.get_logger().info("Exploration stopped by user.")
        finally:
            if HAS_GPIO:
                try:
                    GPIO.cleanup()
                except Exception:
                    pass
            explorer_node.destroy_node()
            rclpy.shutdown()
    else:
        print("ROS 2 environment not detected. Use test harness for standalone execution.")


if __name__ == '__main__':
    main()
