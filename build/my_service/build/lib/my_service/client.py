import rclpy

from rclpy.node import Node

from example_interfaces.srv import AddTwoInts


class AddClient(Node):

    def __init__(self):

        super().__init__("add_client")

        self.client = self.create_client(
            AddTwoInts,
            "add_two_ints"
        )

        while not self.client.wait_for_service(timeout_sec=1):

            self.get_logger().info("Waiting...")

    def send_request(self, a, b):

        req = AddTwoInts.Request()

        req.a = a

        req.b = b

        future = self.client.call_async(req)

        rclpy.spin_until_future_complete(self, future)

        return future.result()


def main():

    rclpy.init()

    node = AddClient()

    result = node.send_request(10, 20)

    print(result.sum)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == "__main__":
    main()