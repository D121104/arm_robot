# Gói Mô phỏng Vật lý: `my_robot_arm_gazebo`

Gói này cung cấp cấu hình môi trường mô phỏng vật lý ba chiều trong Gazebo Sim phục vụ cho việc thử nghiệm cánh tay robot Panda gắp và thả vật thể. Nó tích hợp trực tiếp dữ liệu cảm biến và chấp hành với ROS 2 thông qua các cầu nối dữ liệu (bridges) và plugin chuyên dụng.

---

## 1. Cấu trúc Thư mục và Tệp tin chính
- **[worlds/pick_place_world.sdf](file:///e:/Robotics/arm_robot/src/my_robot_arm_gazebo/worlds/pick_place_world.sdf)**: Tệp tin SDF (Simulation Description Format) mô tả chi tiết thế giới ảo bao gồm các định luật vật lý, nguồn sáng, bàn làm việc và khối hộp cần gắp.
- **[launch/gazebo.launch.py](file:///e:/Robotics/arm_robot/src/my_robot_arm_gazebo/launch/gazebo.launch.py)**: File khởi chạy tích hợp chịu trách nhiệm kích hoạt Gazebo Sim, tải thế giới ảo, spawn robot Panda vào thế giới mô phỏng và khởi chạy các bộ điều khiển liên quan.

---

## 2. Chi tiết Thế giới Mô phỏng (`pick_place_world.sdf`)

Thế giới giả lập được thiết lập tối giản nhưng đảm bảo tính chính xác cao về tương tác vật lý:
- **Cấu hình Vật lý**: Chu kỳ tính toán (max step size) là **1 ms** (`0.001`), với hệ số thời gian thực (`real_time_factor`) giữ ở mức **1.0** nhằm đảm bảo tốc độ chạy mô phỏng đồng bộ với thời gian thực tế.
- **Các Plugin Thế giới**: Tải các hệ thống cốt lõi của Gazebo bao gồm Physics (Tính toán va chạm/trọng lực), UserCommands (Nhận lệnh GUI), SceneBroadcaster (Phát hình ảnh hiển thị), và Contact (Phát hiện va chạm).
- **Thành phần Môi trường**:
  - Một mô hình tĩnh `table` (mặt bàn gỗ kích thước $0.8 \times 0.8 \times 0.05$ m) được đặt tại tâm điểm tọa độ $(0.5, 0.0, 0.4)$.
  - Một khối hộp đỏ đại diện cho vật gắp (`pick_object`) có kích thước cạnh **4 cm** ($0.04$ m), khối lượng **0.1 kg** được đặt tại tọa độ $(0.5, 0.0, 0.445)$. Hệ số mô-men quán tính xoay được tính toán chính xác để chống trượt và rung lắc khi gripper kẹp chặt:
    $$I_{xx} = I_{yy} = I_{zz} = \frac{m}{6} \cdot s^2 = \frac{0.1}{6} \cdot 0.04^2 \approx 2.667 \times 10^{-5} \text{ kg}\cdot\text{m}^2$$

---

## 3. Phân tích Luồng Khởi chạy trong `gazebo.launch.py`

File launch được thiết kế tối ưu hóa tài nguyên phần cứng và điều khiển tuần tự:

### Các Tham số Khởi chạy (Launch Arguments)
- `world`: Đường dẫn tới tệp SDF thế giới mô phỏng (mặc định nạp tệp `pick_place_world.sdf`).
- `headless`: Nếu đặt là `true`, mô phỏng sẽ chạy ở chế độ server-only (không mở GUI 3D của Gazebo), giúp tiết kiệm lượng lớn tài nguyên CPU và GPU khi kiểm tra logic thuật toán.

### Luồng Xử lý và Các Node Chính
1. **Khởi động Gazebo (`gz_sim`)**: Gọi tệp khởi chạy mẫu `gz_sim.launch.py` từ gói `ros_gz_sim` để khởi động trình giả lập Gazebo Sim cùng thế giới đã chọn.
2. **Đồng bộ Thời gian (`clock_bridge`)**: Kích hoạt node `parameter_bridge` thuộc gói `ros_gz_bridge` để chuyển tiếp luồng dữ liệu thời gian từ Gazebo về hệ thống ROS 2 dưới dạng topic `/clock`:
   ```bash
   /clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock
   ```
   Điều này đảm bảo toàn bộ hệ thống ROS 2 sử dụng thời gian của bộ mô phỏng thay vì thời gian của CPU máy tính, giúp tránh các lỗi trễ đồng bộ.
3. **Mô tả Robot (`robot_state_publisher`)**: Đọc tệp URDF cánh tay robot với tham số phần cứng được gán là `gz_ros2_control` và kích hoạt tham số `use_sim_time: True`.
4. **Spawn Robot (`spawn_robot`)**: Gọi tiến trình tạo thực thể `create` của Gazebo để đưa cánh tay robot Panda từ mô tả `/robot_description` vào thế giới giả lập tại vị trí gốc tọa độ.
5. **Trình quản lý Bộ điều khiển (Lưu ý đặc biệt)**:
   > [!IMPORTANT]
   > Khi chạy giả lập Gazebo Sim, trình quản lý bộ điều khiển `controller_manager` được sinh ra tự động bởi plugin `GazeboSimROS2ControlPlugin` được khai báo trong URDF của robot. Do đó, tuyệt đối **không** được chạy node `ros2_control_node` một cách độc lập từ file launch này vì nó sẽ xung đột với trình quản lý do Gazebo quản lý.
6. **Khởi chạy Bộ điều khiển Tuần tự**:
   - Sử dụng `TimerAction` để trì hoãn việc gọi bộ nạp `joint_state_broadcaster` đi **5.0 giây**. Độ trễ này là cần thiết để Gazebo hoàn tất quá trình tải thế giới, nạp robot và đăng ký dịch vụ `/controller_manager`.
   - Các bộ điều khiển khớp `panda_arm_controller` và `panda_hand_controller` lần lượt được khởi chạy tuần tự sau đó thông qua cơ chế lắng nghe sự kiện kết thúc tiến trình trước (`OnProcessExit`).
