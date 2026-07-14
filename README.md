# 🤖 Robot Arm Pick & Place — ROS 2 Jazzy + Gazebo Sim

Hệ thống điều khiển cánh tay robot **Franka Emika Panda** thực hiện nhiệm vụ **gắp và đặt vật thể tự động** (Pick & Place) sử dụng **ROS 2 Jazzy**, **MoveIt 2**, và mô phỏng **Gazebo Sim**.

![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy-blue)
![Gazebo](https://img.shields.io/badge/Gazebo-Sim-orange)
![MoveIt](https://img.shields.io/badge/MoveIt-2-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Mục lục

- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Hướng dẫn chạy](#-hướng-dẫn-chạy)
  - [Cách 1: Xem mô hình robot (RViz2)](#cách-1-xem-mô-hình-robot-rviz2)
  - [Cách 2: Chạy Mock Hardware (không cần Gazebo)](#cách-2-chạy-mock-hardware-không-cần-gazebo)
  - [Cách 3: Chạy trên Gazebo Sim (mô phỏng đầy đủ)](#cách-3-chạy-trên-gazebo-sim-mô-phỏng-đầy-đủ)
- [Tùy chỉnh tham số](#-tùy-chỉnh-tham-số)
- [Quy trình Pick & Place](#-quy-trình-pick--place)

---

## 💻 Yêu cầu hệ thống

| Thành phần | Phiên bản |
|---|---|
| **Hệ điều hành** | Ubuntu 24.04 LTS (Noble Numbat) |
| **ROS 2** | Jazzy Jalisco |
| **Gazebo** | Gazebo Sim (Harmonic) |
| **MoveIt 2** | MoveIt 2 cho Jazzy |
| **Python** | 3.12+ |

### Các package ROS 2 cần thiết

```bash
sudo apt install -y \
  ros-jazzy-moveit \
  ros-jazzy-moveit-resources-panda-description \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-ros-gz \
  ros-jazzy-controller-manager \
  ros-jazzy-joint-state-broadcaster \
  ros-jazzy-joint-trajectory-controller \
  ros-jazzy-gripper-controllers
```

---

## 📥 Cài đặt

### 1. Tạo workspace và clone repository

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/D121104/arm_robot.git .
```

> **Lưu ý:** Lệnh `git clone ... .` sẽ clone nội dung trực tiếp vào thư mục `src/`, không tạo thêm thư mục con.

### 2. Cài đặt dependencies

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
```

### 3. Build workspace

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

### 4. Source workspace

```bash
source ~/ros2_ws/install/setup.bash
```

> **Mẹo:** Thêm dòng sau vào `~/.bashrc` để tự động source mỗi khi mở terminal:
> ```bash
> echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
> echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
> ```

---

## 📁 Cấu trúc dự án

```
src/
├── my_robot_arm_description/      # Mô tả robot (URDF/Xacro + Meshes)
│   ├── urdf/
│   │   ├── my_robot_arm.urdf.xacro
│   │   ├── panda_arm.ros2_control.xacro
│   │   └── panda_hand.ros2_control.xacro
│   └── config/
│       └── initial_positions.yaml
│
├── my_robot_arm_control/          # Cấu hình ros2_control controllers
│   └── config/
│       └── ros2_controllers.yaml
│
├── my_robot_arm_gazebo/           # Mô phỏng Gazebo
│   ├── worlds/
│   │   └── pick_place_world.sdf
│   └── launch/
│       └── gazebo.launch.py
│
├── my_robot_arm_moveit_config/    # Cấu hình MoveIt 2
│   └── config/
│       ├── panda.srdf
│       ├── kinematics.yaml
│       ├── moveit_controllers.yaml
│       └── ompl_planning.yaml
│
└── my_robot_arm_pick_place/       # Node Pick & Place chính
    ├── my_robot_arm_pick_place/
    │   └── pick_place_node.py
    ├── config/
    │   └── pick_place_params.yaml
    └── launch/
        ├── pick_place.launch.py
        └── pick_place_gazebo.launch.py
```

---

## 🚀 Hướng dẫn chạy

> **Quan trọng:** Mỗi terminal mới đều cần source môi trường ROS 2:
> ```bash
> source /opt/ros/jazzy/setup.bash
> source ~/ros2_ws/install/setup.bash
> ```

### Cách 1: Xem mô hình robot (RViz2)

Kiểm tra mô hình 3D và hệ thống khung tọa độ (TF) của robot:

```bash
ros2 launch my_robot_arm_description display.launch.py
```

**Kết quả:** RViz2 hiển thị robot Panda 3D với bảng điều khiển thanh trượt để xoay thử các khớp.

---

### Cách 2: Chạy Mock Hardware (không cần Gazebo)

Chạy toàn bộ hệ thống trong chế độ giả lập — Controller Manager ảo tự phản hồi trạng thái:

```bash
ros2 launch my_robot_arm_pick_place pick_place.launch.py
```

**Kết quả:** Robot thực hiện chu trình Pick & Place bằng mô phỏng toán học (không có giao diện đồ họa Gazebo).

---

### Cách 3: Chạy trên Gazebo Sim (mô phỏng đầy đủ)

Đây là chế độ chính — robot sẽ di chuyển trực quan trong Gazebo và gắp khối hộp màu đỏ.

#### Terminal 1 — Khởi động Gazebo + Robot + Controllers:

```bash
ros2 launch my_robot_arm_gazebo gazebo.launch.py
```

Chờ cho đến khi:
- ✅ Gazebo mở và hiển thị bàn gỗ + hộp đỏ + vùng xanh
- ✅ Robot Panda xuất hiện trên bàn
- ✅ Terminal hiện log "Successfully loaded and activated controller..."

#### Terminal 2 — Chạy Pick & Place + MoveIt:

```bash
ros2 launch my_robot_arm_pick_place pick_place_gazebo.launch.py
```

**Kết quả:** Cánh tay robot sẽ tự động:
1. Di chuyển về vị trí sẵn sàng (Ready Pose)
2. Mở gripper
3. Tiếp cận vật thể từ phía trên
4. Hạ xuống gắp vật
5. Nâng vật lên
6. Di chuyển đến vùng xanh
7. Đặt vật xuống
8. Quay lại vị trí ban đầu
9. Lặp lại chu trình

---

### Chạy Gazebo headless (không GUI — tiết kiệm tài nguyên)

```bash
ros2 launch my_robot_arm_gazebo gazebo.launch.py headless:=true
```

---

## ⚙️ Tùy chỉnh tham số

Chỉnh sửa file `src/my_robot_arm_pick_place/config/pick_place_params.yaml`:

```yaml
pick_place_node:
  ros__parameters:
    approach_height: 0.12         # Chiều cao tiếp cận trước khi gắp (m)
    retreat_height: 0.20          # Chiều cao nhấc vật sau khi gắp (m)
    place_approach_height: 0.15   # Chiều cao tiếp cận trước khi đặt (m)

    gripper_open: 0.035           # Độ mở gripper (m/ngón)
    gripper_close: 0.018          # Độ đóng gripper (m/ngón)

    pick_position:                # Tọa độ vật thể (hộp đỏ)
      x: 0.5
      y: 0.0
      z: 0.445

    place_position:               # Tọa độ vùng đặt (vùng xanh)
      x: 0.5
      y: 0.3
      z: 0.445

    max_velocity_scaling_factor: 0.3     # Hệ số tốc độ (0.0 - 1.0)
    max_acceleration_scaling_factor: 0.2 # Hệ số gia tốc (0.0 - 1.0)
```

**Sau khi sửa, cần build lại:**

```bash
cd ~/ros2_ws
colcon build --packages-select my_robot_arm_pick_place
source install/setup.bash
```

---

## 🔄 Quy trình Pick & Place

```
Bước 1  ➜  Di chuyển về vị trí Ready Pose
    │
Bước 2  ➜  Mở Gripper
    │
Bước 3  ➜  Di chuyển đến Pre-grasp (trên vật +12cm)
    │
Bước 4  ➜  Hạ xuống vị trí Grasp
    │
Bước 5  ➜  Đóng Gripper (kẹp vật)
    │
Bước 6  ➜  Nâng vật lên (Post-grasp +20cm)
    │
Bước 7  ➜  Di chuyển đến Pre-place (trên vùng đặt +15cm)
    │
Bước 8  ➜  Hạ xuống vị trí Place
    │
Bước 9  ➜  Mở Gripper (thả vật)
    │
Bước 10 ➜  Nâng lên (Post-place +20cm)
    │
Bước 11 ➜  Quay về Ready Pose ➜ Lặp lại từ Bước 1
```

---

## 🐛 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `Controller not found` | Gazebo chưa load xong plugin | Chờ thêm 10-15 giây rồi thử lại |
| `Planning failed` | Vị trí mục tiêu ngoài tầm với | Kiểm tra tọa độ trong `pick_place_params.yaml` |
| Robot rung lắc | `use_sim_time` chưa đồng bộ | Đảm bảo cả 2 terminal đều chạy |
| Gripper không kẹp được | Sai thông số gripper | Kiểm tra `gripper_close` trong params |
| `Could not find robot_description` | Chưa source workspace | Chạy `source install/setup.bash` |

---

## 📄 License

MIT License — Xem file [LICENSE](LICENSE) để biết thêm chi tiết.
