# Gói Mô tả Robot: `my_robot_arm_description`

Gói này chứa các tệp định nghĩa mô hình hình học, các đặc tính động học, động lực học và các giao diện phần cứng cho robot Panda dưới dạng Xacro/URDF, phục vụ cho việc lập kế hoạch quỹ đạo và mô phỏng.

---

## 1. Cấu trúc Thư mục và Tệp tin chính
- **[urdf/my_robot_arm.urdf.xacro](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/urdf/my_robot_arm.urdf.xacro)**: Tệp Xacro gốc cấu hình toàn bộ robot Panda, kết nối robot với thế giới (`world`) và nạp các plugin cần thiết.
- **[urdf/panda_arm.ros2_control.xacro](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/urdf/panda_arm.ros2_control.xacro)**: Định nghĩa cấu hình phần cứng `ros2_control` cho 7 khớp của cánh tay robot.
- **[urdf/panda_hand.ros2_control.xacro](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/urdf/panda_hand.ros2_control.xacro)**: Định nghĩa cấu hình phần cứng `ros2_control` cho cơ cấu kẹp (gripper).
- **[config/initial_positions.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/config/initial_positions.yaml)**: Định nghĩa tư thế ban đầu (tọa độ khớp mặc định) của robot khi khởi động.
- **[rviz/display.rviz](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/rviz/display.rviz)**: Thiết lập cấu hình giao diện trực quan RViz.
- **[launch/display.launch.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/launch/display.launch.py)**: Tệp khởi chạy dùng để hiển thị và kiểm tra cấu trúc khớp robot trong RViz thông qua thanh trượt GUI điều khiển khớp thủ công.

---

## 2. Chi tiết Thiết kế mô hình Xacro

Tệp [my_robot_arm.urdf.xacro](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/urdf/my_robot_arm.urdf.xacro) đóng vai trò là "chất keo" lắp ráp các phần khác nhau của robot:
- **Tải tệp hình học mặc định**: Sử dụng lệnh `<xacro:include>` để nhập mô hình meshes, các liên kết (links) và khớp (joints) tiêu chuẩn của Panda từ gói tài nguyên hệ thống `moveit_resources_panda_description`.
- **Định vị thế giới**: Định nghĩa liên kết ảo cố định `<link name="world"/>` và gắn chân đế robot (`panda_link0`) vào thế giới qua khớp cố định `<joint name="panda_joint_world" type="fixed">`.
- **Plugin mô phỏng Gazebo**:
  Nếu tham số `ros2_control_hardware_type` được đặt là `gz_ros2_control`, hệ thống sẽ nạp plugin tích hợp mô phỏng:
  ```xml
  <gazebo>
      <plugin filename="gz_ros2_control-system" name="gz_ros2_control::GazeboSimROS2ControlPlugin">
          <parameters>$(arg parameters_file)</parameters>
      </plugin>
  </gazebo>
  ```
  Plugin này cho phép bộ giả lập Gazebo trực tiếp giao tiếp với các bộ điều khiển ROS 2 qua bus bộ nhớ dùng chung.

---

## 3. Cấu hình Phần cứng trong `ros2_control`
Mô hình `ros2_control` được thiết kế linh hoạt bằng cách sử dụng các macro Xacro:

1. **Cánh tay (`panda_arm.ros2_control.xacro`)**:
   - Sử dụng plugin phần cứng dựa trên tham số: `mock_components/GenericSystem` (giả lập ảo) hoặc `gz_ros2_control/GazeboSimSystem` (trong mô phỏng Gazebo).
   - Mỗi khớp từ 1 đến 7 đều khai báo:
     - Giao diện điều khiển `<command_interface name="position"/>`.
     - Giao diện trạng thái phản hồi `<state_interface name="position">` và `<state_interface name="velocity">`.
     - Vị trí khởi đầu của các khớp được ánh xạ động từ tệp [initial_positions.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/config/initial_positions.yaml) (Ví dụ: `panda_joint1: 0.0`, `panda_joint4: -1.57`).

2. **Kẹp kẹp (`panda_hand.ros2_control.xacro`)**:
   - Khai báo 2 khớp ngón kẹp (`panda_finger_joint1` và `panda_finger_joint2`).
   - Cả hai ngón kẹp đều mở rộng tối đa ở mức **0.035 m** khi khởi động.
   - Trình điều khiển kẹp nhận lệnh vị trí trên ngón kẹp 1, ngón kẹp 2 phản hồi trạng thái vị trí đồng bộ.

---

## 4. Phân tích Chi tiết File Launch (`display.launch.py`)
File launch này dùng để kiểm tra mô hình 3D độc lập mà không cần bộ điều khiển thực thi quỹ đạo:
- Sử dụng lệnh biên dịch Xacro động `Command(['xacro', 'my_robot_arm.urdf.xacro'])` để sinh ra dữ liệu chuỗi URDF XML truyền trực tiếp vào tham số `robot_description`.
- Khởi chạy các Node:
  - **`robot_state_publisher`**: Xuất bản các khung tọa độ TF động.
  - **`joint_state_publisher_gui`**: Tạo cửa sổ giao diện đồ họa chứa các thanh trượt điều khiển khớp để người dùng thay đổi góc quay các khớp thủ công.
  - **`rviz2`**: Mở giao diện RViz với cấu hình lưu sẵn `display.rviz` để quan sát mô hình robot chuyển động theo các thanh trượt khớp.
