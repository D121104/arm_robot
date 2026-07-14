import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class PublisherNode(Node):

    def __init__(self):

        super().__init__('publisher_node')

        self.publisher = self.create_publisher(
            String,
            'robot_status',
            10
        )

        self.timer = self.create_timer(
            0.2,
            self.timer_callback
        )

        self.count = 0

    def timer_callback(self):

        msg = String()

        msg.data = (
            f"Count = {self.count}, "
            f"Time = {self.get_clock().now().to_msg().sec}"
        )

        self.publisher.publish(msg)

        self.get_logger().info(
            f'Publish: {msg.data}'  
        )

        self.count += 1


def main(args=None):

    rclpy.init(args=args)

    node = PublisherNode()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()