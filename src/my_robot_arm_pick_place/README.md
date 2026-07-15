# Gói Kịch bản Gắp thả: `my_robot_arm_pick_place`

Gói này chứa mã nguồn Node điều khiển logic cấp cao thực hiện chuỗi hoạt động tuần tự gắp và thả vật thể (Pick & Place) sử dụng thư viện **MoveIt 2 Python API (`MoveItPy`)**. Gói phần mềm hỗ trợ chạy thử nghiệm trên phần cứng ảo (mock) và mô phỏng vật lý thực tế trong Gazebo Sim.

---

## 1. Cấu trúc Thư mục và Tệp tin chính
- **[my_robot_arm_pick_place/pick_place_node.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_pick_place/my_robot_arm_pick_place/pick_place_node.py)**: Mã nguồn Python chính định nghĩa class điều khiển gắp thả `PickPlaceNode`.
- **[config/pick_place_params.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_pick_place/config/pick_place_params.yaml)**: File cấu hình các tọa độ gắp, đặt vật, khoảng mở ngón kẹp, chiều cao tiếp cận an toàn và các thông số tốc độ của robot.
- **[config/global_params.yaml](file:///e:/Robotics/arm_robot/src/my_robot_arm_pick_place/config/global_params.yaml)**: Cấu hình dùng chung để kích hoạt chế độ thời gian mô phỏng (`use_sim_time: true`).
- **[launch/pick_place.launch.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_pick_place/launch/pick_place.launch.py)**: File launch tích hợp khởi chạy đồng thời MoveIt 2, RViz và Node gắp thả chạy với phần cứng mock.
- **[launch/pick_place_gazebo.launch.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_pick_place/launch/pick_place_gazebo.launch.py)**: File launch khởi động MoveIt 2, RViz và Node gắp thả kết nối trực tiếp với Gazebo Sim (Gazebo Sim cần được khởi động trước qua gói `my_robot_arm_gazebo`).

---

## 2. Các Tham số Cấu hình (`pick_place_params.yaml`)
- `approach_height: 0.12`: Khoảng cách tiếp cận an toàn phía trên vật gắp (m).
- `retreat_height: 0.20`: Khoảng cách rút lui nâng vật lên sau khi gắp và sau khi đặt (m).
- `place_approach_height: 0.15`: Khoảng cách tiếp cận an toàn phía trên vị trí thả vật (m).
- `gripper_open: 0.035`: Khoảng cách mở mỗi ngón kẹp khi nhả vật (m, tổng độ mở kẹp khoảng 7 cm).
- `gripper_close: 0.018`: Khoảng cách đóng ngón kẹp khi gắp khối hộp cạnh 4 cm (m).
- **Vị trí gắp (`pick_position`)**: Tâm khối hộp đỏ tại $(x=0.5, y=0.0, z=0.445)$.
- **Vị trí đặt (`place_position`)**: Tâm vùng đặt màu xanh tại $(x=0.5, y=0.3, z=0.445)$.
- **Hướng Quaternion cuối (`pick_orientation` / `place_orientation`)**: Hướng đầu kẹp thẳng đứng từ trên xuống $(x=1.0, y=0.0, z=0.0, w=0.0)$.
- Các scaling factor giới hạn vận tốc khớp ở mức **30%** (`0.3`) và gia tốc khớp ở mức **20%** (`0.2`) để bảo vệ an toàn cơ khí.

---

## 3. Phân tích Chi tiết Mã nguồn `pick_place_node.py`

### Kiến trúc Khởi tạo (`__init__`)
Node điều khiển khai báo các tham số ROS 2, sau đó khởi dựng thư viện `MoveItPy` động:
1. Xác định môi trường phần cứng thông qua tham số `use_sim_time`. Nếu dùng giả lập, kiểu phần cứng là `gz_ros2_control`, ngược lại là `mock_components`.
2. Sử dụng `MoveItConfigsBuilder` để tải cấu hình robot Panda trực tiếp từ gói `my_robot_arm_moveit_config` thông qua tệp Xacro URDF từ gói mô tả robot:
   ```python
   moveit_config = (
       MoveItConfigsBuilder("panda", package_name="my_robot_arm_moveit_config")
       .robot_description(file_path=urdf_path, mappings={"ros2_control_hardware_type": hardware_type})
       .moveit_cpp(file_path="config/moveit_cpp.yaml")
       .planning_pipelines(pipelines=["ompl"])
       .to_moveit_configs()
   )
   ```
3. Khởi tạo đối tượng `MoveItPy` và lấy hai Planning Component chính: `panda_arm` điều khiển cánh tay và `gripper` điều khiển kẹp.
4. Kích hoạt một tiến trình chạy nền (background thread):
   ```python
   self.thread = threading.Thread(target=self.run_pick_and_place, daemon=True)
   self.thread.start()
   ```
   Luồng chạy nền này giúp Node thực thi vòng lặp tuần tự Pick & Place liên tục mà không gây nghẽn luồng xử lý chính của ROS 2 executor (`rclpy.spin`), cho phép các dịch vụ và topic phản hồi thời gian thực bình thường.

---

### Phân tích chi tiết các Hàm chức năng

#### `move_arm_to_named_state(self, state_name: str) -> bool`
- **Mục đích**: Di chuyển cánh tay robot đến một cấu hình khớp định danh trước trong file SRDF (như `ready`).
- **Cách thức**: Đặt trạng thái bắt đầu bằng trạng thái khớp hiện tại của robot (`set_start_state_to_current_state`), đặt mục tiêu bằng cấu hình tên (`set_goal_state(configuration_name=state_name)`), gọi hàm tính toán quỹ đạo (`self.arm.plan()`), và thực thi quỹ đạo thông qua bộ điều khiển `panda_arm_controller`.
- **Độ tin cậy**: Cho phép thử lại tối đa **3 lần** nếu việc lập kế hoạch đường đi thất bại.

#### `move_arm_to_pose(self, x, y, z, ox, oy, oz, ow, label) -> bool`
- **Mục đích**: Di chuyển điểm cuối cánh tay (khớp `panda_link8`) đến tọa độ Cartesian mong muốn.
- **Cách thức**: Tạo tin nhắn tọa độ đích kiểu `PoseStamped` tham chiếu về khung tọa độ đế robot (`panda_link0`), thiết lập mục tiêu chuyển động của MoveIt, thực hiện tính toán tránh va chạm và gửi quỹ đạo thực thi đến bộ điều khiển cánh tay. Cho phép thử lại tối đa 3 lần.

#### `set_gripper(self, state_name: str) -> bool`
- **Mục đích**: Đóng hoặc mở kẹp của robot.
- **Cách thức**: Lập kế hoạch chuyển động cho khớp kẹp đến cấu hình đặt sẵn (`open` hoặc `close`), thực thi quỹ đạo thông qua bộ điều khiển `panda_hand_controller`.

#### `reset_world(self)`
- **Mục đích**: Đưa thế giới mô phỏng Gazebo về trạng thái ban đầu sau mỗi chu kỳ gắp thả thành công.
- **Cách thức**: Sử dụng thư viện `subprocess` của Python để thực thi các lệnh dịch vụ của hệ thống Gazebo (`gz service`):
  1. Đặt lại tọa độ vị trí của toàn bộ các mô hình trong thế giới giả lập về trạng thái tĩnh ban đầu:
     `gz service -s /world/pick_place_world/control --reqtype gz.msgs.WorldControl --req "reset: {model_only: true}"`
  2. Định vị lại khối hộp cần gắp (`pick_object`) chính xác về tọa độ gắp ban đầu $(0.5, 0.0, 0.445)$:
     `gz service -s /world/pick_place_world/set_pose --reqtype gz.msgs.Pose --req 'name: "pick_object", position: {x: 0.5, y: 0.0, z: 0.445}'`

#### `reactivate_controllers(self)`
- **Mục đích**: Khởi động lại các bộ điều khiển ROS 2 Control sau khi Gazebo được reset.
- **Cách thức**: Lệnh reset mô hình của Gazebo sẽ đưa phần cứng mô phỏng về trạng thái khởi đầu, làm tắt các bộ điều khiển ROS 2 Control. Hàm này gọi dịch vụ `/controller_manager/switch_controller` để kích hoạt lại danh sách bộ điều khiển: `joint_state_broadcaster`, `panda_arm_controller`, và `panda_hand_controller` ở chế độ kích hoạt khẩn cấp (`activate_asap = True`).

#### `run_pick_and_place(self)`
- **Mục đích**: Vòng lặp quản trị chu trình làm việc vô hạn.
- **Cách thức**: Gọi hàm thực thi tuần tự `execute_sequence()`. Nếu chạy trong môi trường mô phỏng (`use_sim_time`), sau mỗi chu kỳ, node sẽ tiến hành gọi hàm `reset_world()` và `reactivate_controllers()`, sau đó chờ 2 giây trước khi khởi chạy chu kỳ kế tiếp.

---

### Chuỗi kịch bản Gắp và Thả tuần tự (`execute_sequence`)
Hàm thực thi tuần tự bao gồm **11 bước** chi tiết như sau:

| Bước | Hành động | Hàm gọi | Trạng thái / Tọa độ đích |
| :---: | :--- | :--- | :--- |
| **1** | Di chuyển về vị trí Home | `move_arm_to_named_state` | Góc khớp cấu hình `'ready'` |
| **2** | Mở rộng cơ cấu kẹp | `set_gripper` | Cấu hình ngón kẹp `'open'` |
| **3** | Di chuyển tới điểm an toàn trên vật | `move_arm_to_pose` | $(x_{\text{pick}}, y_{\text{pick}}, z_{\text{pick}} + 0.12)$ |
| **4** | Hạ kẹp xuống vị trí gắp | `move_arm_to_pose` | $(x_{\text{pick}}, y_{\text{pick}}, z_{\text{pick}})$ |
| **5** | Đóng kẹp giữ chặt vật thể | `set_gripper` | Cấu hình ngón kẹp `'close'` |
| **6** | Rút lui nhấc vật lên cao | `move_arm_to_pose` | $(x_{\text{pick}}, y_{\text{pick}}, z_{\text{pick}} + 0.20)$ |
| **7** | Di chuyển tới điểm an toàn trên bàn đặt | `move_arm_to_pose` | $(x_{\text{place}}, y_{\text{place}}, z_{\text{place}} + 0.15)$ |
| **8** | Hạ tay robot xuống vị trí đặt vật | `move_arm_to_pose` | $(x_{\text{place}}, y_{\text{place}}, z_{\text{place}})$ |
| **9** | Mở kẹp giải phóng vật thể | `set_gripper` | Cấu hình ngón kẹp `'open'` |
| **10** | Rút tay robot lên cao tránh vật | `move_arm_to_pose` | $(x_{\text{place}}, y_{\text{place}}, z_{\text{place}} + 0.20)$ |
| **11** | Đưa robot quay lại vị trí Home | `move_arm_to_named_state` | Góc khớp cấu hình `'ready'` |
