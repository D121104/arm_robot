# Gói Cấu hình Lập kế hoạch Chuyển động: `my_robot_arm_moveit_config`

Gói này chứa toàn bộ các thiết lập cấu hình cần thiết cho framework lập kế hoạch chuyển động MoveIt 2 hoạt động trên robot Panda. Nó định nghĩa các nhóm lập kế hoạch, các thuật toán tìm kiếm đường đi, bộ giải động học ngược và tích hợp với các driver bộ điều khiển của ROS 2.

---

## 1. Cấu trúc Thư mục và Tệp tin chính
- **[config/panda.srdf](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/config/panda.srdf)**: Tệp SRDF (Semantic Robot Description Format) chứa thông tin bổ trợ ngữ nghĩa cho robot (các nhóm khớp, các tư thế khớp đặt sẵn và ma trận bỏ qua va chạm nội bộ).
- **[config/kinematics.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/config/kinematics.yaml)**: Định nghĩa bộ giải động học ngược (Inverse Kinematics solver) và các tham số giới hạn tìm kiếm nghiệm.
- **[config/ompl_planning.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/config/ompl_planning.yaml)**: Thiết lập cấu hình thư viện OMPL (Open Motion Planning Library) bao gồm các thuật toán lấy mẫu không gian như RRT, RRTConnect, PRM...
- **[config/moveit_controllers.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/config/moveit_controllers.yaml)**: Liên kết các bộ điều khiển thực thi quỹ đạo của MoveIt với các giao tiếp Action của bộ điều khiển ROS 2 Control.
- **[config/joint_limits.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/config/joint_limits.yaml)**: Cấu hình giới hạn an toàn vật lý của khớp (vận tốc tối đa, gia tốc tối đa, góc quay tối thiểu/tối đa).
- **[config/moveit_cpp.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/config/moveit_cpp.yaml)**: Cấu hình tham số mức thấp phục vụ cho MoveIt 2 C++ API và MoveItPy Python API.
- **[launch/moveit.launch.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_moveit_config/launch/moveit.launch.py)**: Tệp khởi chạy toàn diện chạy MoveIt 2 kết hợp RViz trực quan hóa và bộ điều khiển mock.

---

## 2. Chi tiết Cấu hình Ngữ nghĩa (`panda.srdf`)

Tệp tin SRDF định nghĩa cấu trúc làm việc logic của robot:
- **Planning Groups (Nhóm lập kế hoạch)**:
  - **`panda_arm`**: Nhóm chính điều khiển cánh tay từ khớp `panda_joint1` tới khớp `panda_joint7` với điểm cuối (end-effector) là `panda_link8`.
  - **`hand`**: Nhóm điều khiển cơ cấu kẹp, bao gồm khớp ngón kẹp `panda_finger_joint1` và `panda_finger_joint2`.
- **Predefined States (Các tư thế khớp đặt sẵn)**:
  - Nhóm `panda_arm` có tư thế `ready` (tư thế sẵn sàng hoạt động với các góc khớp được định nghĩa trước).
  - Nhóm `hand` có hai trạng thái `open` (mở kẹp hết cỡ) và `close` (đóng kẹp lại).
- **Bỏ qua Va chạm Nội bộ (Collision Disabling)**:
  - Khai báo các cặp liên kết cơ khí liền kề hoặc không thể va chạm vật lý với nhau (ví dụ: giữa `panda_link0` và `panda_link1`). Việc này giúp bộ lập kế hoạch bỏ qua các tính toán va chạm dư thừa, tăng tốc độ tính toán quỹ đạo lên hàng chục lần.

---

## 3. Cấu hình Lập kế hoạch và Động học Ngược
- **Bộ giải động học ngược (`kinematics.yaml`)**:
  Nhóm cánh tay `panda_arm` sử dụng bộ giải mặc định **KDL** (`kdl_kinematics_plugin/KDLKinematicsPlugin`).
  - Độ phân giải tìm kiếm góc khớp: **0.005 rad**.
  - Thời gian chờ tính toán tối đa: **0.05 giây** (`kinematics_solver_timeout`).
  - Số lần thử giải lại tối đa: **3 lần**.
- **Bộ lập kế hoạch đường đi (`ompl_planning.yaml`)**:
  Định nghĩa các tham số chi tiết cho thuật toán lập kế hoạch. Thuật toán mặc định thường dùng là `RRTConnect` (Rapidly-exploring Random Trees Connect) do khả năng tìm kiếm quỹ đạo tránh chướng ngại vật rất nhanh trong không gian phức tạp.

---

## 4. Quản lý Điều khiển Quỹ đạo (`moveit_controllers.yaml`)
Tệp tin này cấu hình `MoveItSimpleControllerManager` kết nối trực tiếp với dịch vụ Action của ROS 2:
- Gửi dữ liệu quỹ đạo của cánh tay robot qua Action Client `/panda_arm_controller/follow_joint_trajectory` dưới dạng chuẩn `FollowJointTrajectory`.
- Gửi lệnh đóng/mở gripper qua Action Client `/panda_hand_controller/gripper_cmd` dưới dạng chuẩn `GripperCommand`.

---

## 5. Phân tích Chi tiết File Launch (`moveit.launch.py`)
Tệp khởi chạy này thiết lập một môi trường làm việc MoveIt 2 độc lập sử dụng phần cứng mock ảo:
1. **Nạp Tham số Cấu hình**: Đọc đồng thời các file cấu hình URDF, SRDF, `kinematics.yaml`, `ompl_planning.yaml`, và `moveit_controllers.yaml` thành các biến cấu hình dạng Dictionary.
2. **Khởi chạy Node `move_group`**: Node cốt lõi tích hợp của MoveIt 2. Nó lắng nghe các yêu cầu lập kế hoạch chuyển động trên các Action Server của MoveIt, gọi bộ giải OMPL và KDL để tìm quỹ đạo, sau đó giám sát quá trình thực thi của các bộ điều khiển phần cứng.
3. **Khởi chạy `rviz2`**: Nạp tệp cấu hình chuyên dụng `moveit.rviz` tích hợp plugin MoveIt Motion Planning để người dùng có thể kéo thả tọa độ điểm cuối của robot trực quan và ra lệnh cho robot tự động lập quỹ đạo tránh va chạm.
4. **Spawn bộ điều khiển**: Kích hoạt `ros2_control_node` (mock) và tự động spawn các bộ điều khiển khớp để robot có thể chạy mô phỏng ngay lập tức trên màn hình RViz.
