# Gói Pick & Place: `my_robot_arm_pick_place`

Demo Gazebo Sim cho Panda gắp **năm vật thể vật lý** rồi đặt chúng lên năm pad riêng. Vật thể không bị teleport trong quá trình gắp/đặt: Gazebo giải quyết va chạm, ma sát và trọng lực; robot chỉ được phép nâng khi cả hai ngón kẹp báo contact với đúng vật đang chọn.

## Danh mục vật thể

| ID | Hình học | Vùng đặt |
|---|---|---|
| `box_small` | Hộp 0.035 × 0.045 × 0.040 m | Pad xanh lá |
| `box_medium` | Hộp 0.055 × 0.040 × 0.050 m | Pad xanh dương |
| `box_large` | Hộp 0.070 × 0.045 × 0.060 m | Pad vàng |
| `cylinder_small` | Trụ bán kính 0.022 m, cao 0.050 m | Pad tím |
| `cylinder_large` | Trụ bán kính 0.032 m, cao 0.060 m | Pad xanh ngọc |

Kích thước, pose nguồn/đích, retry và ngưỡng contact nằm trong [`config/pick_place_params.yaml`](config/pick_place_params.yaml). Danh mục được lưu tại `object_catalog_json` vì ROS 2 parameters không hỗ trợ mảng dictionary.

## Luồng an toàn

Mỗi vật được lấy theo thứ tự xáo trộn:

```text
ready → open → pre-grasp → approach → close → dual-contact → lift →
retain-contact → pre-place → lower → release → retreat
```

- Hai topic contact là `/panda/left_finger/contact` và `/panda/right_finger/contact`.
- Node chỉ lift nếu cả hai topic có contact mới, ổn định tối thiểu `contact_settle_duration`, và contact cùng model Gazebo mục tiêu.
- Nếu contact timeout hoặc mất khi lift, node mở kẹp, rút lên và thử lại vật đó tối đa `grasp_attempts`.
- Không dùng node này trên phần cứng thật.

## Build và chạy

```bash
source /opt/ros/jazzy/setup.bash
colcon build --packages-select my_robot_arm_description my_robot_arm_control my_robot_arm_gazebo my_robot_arm_pick_place
source install/setup.bash
```

Kiểm tra planning mà không phát lệnh controller:

```bash
ros2 launch my_robot_arm_pick_place pick_place.launch.py backend:=mock planning_only:=true
```

Chạy mô phỏng contact vật lý với GUI:

```bash
ros2 launch my_robot_arm_pick_place pick_place.launch.py backend:=gazebo
```

Chạy headless:

```bash
ros2 launch my_robot_arm_pick_place pick_place.launch.py backend:=gazebo headless:=true start_rviz:=false
```

Dùng seed tái lập thứ tự qua parameter override, ví dụ `--ros-args -p random_seed:=42`; giá trị `-1` (mặc định) tạo thứ tự mới mỗi lần khởi động. Một launch chỉ chạy một lượt gồm năm vật: `run_forever:=true` bị bỏ qua để không reset hoặc teleport object vật lý.

## Xác minh contact

Trong terminal đã source workspace, kiểm tra bridge và sensor trước khi autorun:

```bash
ros2 topic info /panda/left_finger/contact
ros2 topic info /panda/right_finger/contact
ros2 topic echo /panda/left_finger/contact --once
```

Nếu topic không xuất hiện, kiểm tra log Gazebo để xác nhận generated collision name của hai finger khớp với sensor trong [`panda_hand_contact_sensors.gazebo.xacro`](../my_robot_arm_description/urdf/panda_hand_contact_sensors.gazebo.xacro). Khi cần kiểm tra stack không chuyển động, dùng `autorun:=false`.
