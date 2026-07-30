# Gói Điều khiển: `my_robot_arm_control`

Gói này đóng vai trò cấu hình và vận hành hệ thống điều khiển khớp (joint controllers) cho cánh tay robot Panda bằng framework `ros2_control`. Hệ thống hỗ trợ cả chế độ giả lập phần cứng (mock hardware) và mô phỏng vật lý thực tế trong Gazebo Sim.

---

## 1. Cấu trúc Thư mục và Tệp tin chính
- **[config/ros2_controllers.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_control/config/ros2_controllers.yaml)**: File cấu hình các bộ điều khiển, định nghĩa giao diện phần cứng và các tham số giới hạn sai số khớp.
- **[launch/robot_control.launch.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_control/launch/robot_control.launch.py)**: File khởi chạy tích hợp, có trách nhiệm nạp mô hình robot, chạy trình quản lý bộ điều khiển (`controller_manager`) và khởi động các bộ điều khiển theo trình tự logic.

---

## 2. Chi tiết Cấu hình Bộ điều khiển (`ros2_controllers.yaml`)

Tệp tin này định nghĩa các tham số cốt lõi cho `controller_manager` hoạt động ở tần số quét **500 Hz** và định nghĩa 3 bộ điều khiển chính:

1. **`joint_state_broadcaster`** (Kiểu: `joint_state_broadcaster/JointStateBroadcaster`):
   - Đọc trạng thái vị trí/vận tốc từ phần cứng và xuất bản lên topic `/joint_states`.
2. **`panda_arm_controller`** (Kiểu: `joint_trajectory_controller/JointTrajectoryController`):
   - Điều khiển chuyển động bám quỹ đạo cho 7 khớp của cánh tay robot (`panda_joint1` đến `panda_joint7`).
   - **Giao diện nhận lệnh (Command Interfaces)**: `position` (Điều khiển bằng vị trí khớp).
   - **Giao diện phản hồi trạng thái (State Interfaces)**: `position` và `velocity`.
   - **Tham số hành vi**:
     - `allow_nonzero_velocity_at_trajectory_end: true` (Cho phép robot duy trì vận tốc nhỏ ở cuối quỹ đạo khi chuyển tiếp quỹ đạo tiếp theo).
     - Sai số dung sai vị trí khớp mục tiêu (`goal_tolerance`) được thiết lập chặt chẽ ở mức **0.01 rad** cho tất cả các khớp.
3. **`panda_hand_controller`** (Kiểu: `position_controllers/GripperActionController`):
   - Bộ điều khiển dạng Action để điều khiển cơ cấu kẹp (gripper) qua khớp `panda_finger_joint1`.
   - Lực tác động tối đa giới hạn ở **20.0 N** (`max_effort`).
   - Tần số kiểm tra hành động: **20.0 Hz** (`action_monitor_rate`).

---

## 3. Phân tích Chi tiết File Launch (`robot_control.launch.py`)

File launch này sử dụng Python Launch API của ROS 2 để thiết lập trình tự nạp bộ điều khiển tuần tự nhằm tránh xung đột tài nguyên trong `controller_manager`:

### Các tham số đầu vào (Launch Arguments)
- `ros2_control_hardware_type`: Xác định giao diện phần cứng đầu ra. Mặc định là `mock_components` (chỉ giả lập tính toán vòng lặp phản hồi ảo). Có thể cấu hình thành `gz_ros2_control` when kết nối với mô phỏng Gazebo Sim.

### Các Node và Trình tự Hoạt động
1. **`robot_state_publisher`**: Nạp mô hình URDF được sinh ra từ Xacro ([my_robot_arm.urdf.xacro](file:///e:/Robotics/arm_robot/src/my_robot_arm_description/urdf/my_robot_arm.urdf.xacro)) để xuất bản cấu trúc hình học TF của robot.
2. **`ros2_control_node`** (Trình quản lý `controller_manager`): Nạp các tham số bộ điều khiển từ `ros2_controllers.yaml`.
3. **Spawners (Bộ nạp bộ điều khiển)**:
   - Spawn bộ điều khiển trạng thái khớp `joint_state_broadcaster` trước.
   - **Trì hoãn Cánh tay (`delay_arm_controller`)**: Sử dụng bộ bắt sự kiện `RegisterEventHandler` lắng nghe sự kiện thoát tiến trình (`OnProcessExit`) của `joint_state_broadcaster` để bắt đầu spawn `panda_arm_controller`. Việc này đảm bảo thông tin khớp đã được xuất bản trước khi cánh tay nhận lệnh.
   - **Trì hoãn Gripper (`delay_hand_controller`)**: Lắng nghe sự kiện kết thúc spawn của `panda_arm_controller` để spawn `panda_hand_controller` sau cùng.
