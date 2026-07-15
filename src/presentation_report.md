# Kịch bản & Nội dung Slide Thuyết trình (10 Phút)
## Dự án: Robot Arm Pick & Place (ROS 2 Jazzy)

Tài liệu này được thiết kế theo cấu trúc slide-by-slide kèm theo lời thoại (Speaker Notes) chi tiết để bạn có thể thuyết trình trong vòng **10 phút** cho đối tượng người nghe phổ thông (chỉ cần có kiến thức cơ bản).

---

### Slide 1: Giới thiệu chung (Thời gian: 1 phút)
* **Tiêu đề Slide:** HỆ THỐNG GẮP THẢ VẬT THỂ TỰ ĐỘNG BẰNG CÁNH TAY ROBOT (ROS 2 & Gazebo)
* **Nội dung hiển thị:**
  - **Robot thực hiện:** Franka Emika Panda (Cánh tay 7 khớp + Bộ kẹp).
  - **Môi trường thử nghiệm:** Giả lập 3D Gazebo Sim.
  - **Công nghệ cốt lõi:** ROS 2 Jazzy & MoveIt 2.
  - **Người trình bày:** [Tên của bạn]
* **Lời thoại người nói (Speaker Notes):**
  > *"Xin chào thầy cô và các bạn. Hôm nay tôi xin phép trình bày về dự án phát triển hệ thống tự động hóa gắp và đặt vật thể (Pick & Place) sử dụng cánh tay robot Franka Emika Panda. Trong dự án này, chúng ta sẽ mô phỏng cánh tay robot di chuyển hoàn toàn tự động, gắp một khối hộp từ bàn gỗ và đặt chính xác vào vị trí đích mà không cần sự can thiệp thủ công, sử dụng những công nghệ robotics tiên tiến nhất hiện nay là ROS 2 Jazzy và bộ công cụ MoveIt 2."*

---

### Slide 2: Đặt vấn đề & Mục tiêu (Thời gian: 1 phút)
* **Tiêu đề Slide:** ĐẶT VẤN ĐỀ & MỤC TIÊU DỰ ÁN
* **Nội dung hiển thị:**
  - **Thực tế:** Trong nhà máy sản xuất, việc gắp thả linh kiện chiếm 70% công việc thủ công.
  - **Yêu cầu hệ thống:**
    - Định vị vị trí vật cần gắp và nơi cần đặt.
    - Tính toán đường đi an toàn, không va chạm vào bàn ghế, chướng ngại vật hay chính thân robot.
    - Kẹp giữ vật chắc chắn và thả đúng hồng tâm.
* **Lời thoại người nói (Speaker Notes):**
  > *"Tại sao chúng ta cần dự án này? Trong công nghiệp, công việc gắp một sản phẩm từ dây chuyền này đặt sang dây chuyền khác cực kỳ lặp đi lặp lại và tốn nhân công. Mục tiêu của chúng ta là làm sao cho một cánh tay robot có thể thay thế con người làm việc này một cách chính xác. Thách thức ở đây là robot không chỉ đơn giản là đưa tay ra, mà nó phải 'nghĩ' xem làm thế nào để đi tới vật mà không đập tay vào cạnh bàn, không làm rơi vật, và đặt đúng điểm đích đã định."*

---

### Slide 3: Thiết lập Mô hình Robot (Thời gian: 1.5 phút)
* **Tiêu đề Slide:** THIẾT LẬP MÔ HÌNH HÌNH HỌC (URDF/XACRO)
* **Nội dung hiển thị:**
  - **URDF/Xacro:** Định nghĩa cấu trúc khung xương kỹ thuật số của robot (độ dài các khâu, góc xoay tối đa của các khớp).
  - **Khớp robot:** 7 khớp xoay linh hoạt (tương tự cánh tay người) + 1 bộ kẹp (gripper) 2 ngón song song.
  - **Hình ảnh/Meshes:** File đồ họa 3D giúp robot có ngoại hình trực quan trong phần mềm điều khiển.
* **Lời thoại người nói (Speaker Notes):**
  > *"Để máy tính có thể điều khiển được robot, bước đầu tiên chúng ta phải khai báo cho nó biết hình dáng của robot ra sao. Chúng tôi sử dụng các file URDF và Xacro để mô tả robot. Bạn có thể tưởng tượng URDF giống như bản vẽ thiết kế kỹ thuật số: cánh tay này dài bao nhiêu, khớp này có thể quay tối đa bao nhiêu độ, và tay kẹp rộng bao nhiêu. Chúng tôi chọn cánh tay Panda có 7 khớp xoay, tương đương với sự linh hoạt của khớp vai, khớp khuỷu và khớp cổ tay của con người, giúp robot tiếp cận vật thể từ nhiều góc độ khác nhau."*

---

### Slide 4: Giả lập Môi trường ảo với Gazebo Sim (Thời gian: 1.5 phút)
* **Tiêu đề Slide:** GIẢ LẬP TRỰC QUAN (GAZEBO SIMULATION)
* **Nội dung hiển thị:**
  - **Tại sao cần mô phỏng?** Thử nghiệm thuật toán an toàn, không lo va chạm gây hỏng hóc robot thật giá trị cao.
  - **Thành phần môi trường giả lập:**
    - Bàn gỗ phẳng đặt vật thể.
    - Khối hộp màu đỏ (vật cần gắp).
    - Vùng màu xanh lá cây (đích đặt vật).
  - Tích hợp động lực học vật lý (trọng lực, lực ma sát để kẹp giữ vật).
* **Lời thoại người nói (Speaker Notes):**
  > *"Trước khi nạp code vào một con robot thật đắt tiền, chúng ta bắt buộc phải chạy thử trên môi trường mô phỏng để nếu có lỗi va đập xảy ra, chúng ta chỉ cần chỉnh sửa code mà không làm hỏng thiết bị. Chúng tôi sử dụng phần mềm Gazebo Sim để dựng lên một thế giới ảo 3D. Trong thế giới này có bàn gỗ, khối hộp màu đỏ cần gắp và vùng màu xanh để đặt. Gazebo mô phỏng cả trọng lực và ma sát lực, nghĩa là nếu ngón kẹp không ép đủ chặt, khối hộp đỏ sẽ trượt và rơi tự do đúng như thực tế."*

---

### Slide 5: Bộ não của Robot - Lập kế hoạch chuyển động (Thời gian: 2 phút)
* **Tiêu đề Slide:** BỘ NÃO ĐIỀU KHIỂN & LẬP KẾ HOẠCH (MOVEIT 2)
* **Nội dung hiển thị:**
  - **MoveIt 2:** Nền tảng trung tâm tính toán quỹ đạo chuyển động.
  - **Động học ngược (IK):** Tự động tính toán góc quay của 7 khớp từ vị trí mong muốn của tay kẹp.
  - **Lập kế hoạch tránh va chạm (OMPL):** Sử dụng các thuật toán như RRT để tự vẽ đường đi an toàn vòng qua vật cản.
  - **ros2_control:** Cầu nối gửi lệnh điều khiển mượt mà tới các mô tơ khớp.
* **Lời thoại người nói (Speaker Notes):**
  > *"Bộ não của hệ thống này là MoveIt 2. Khi ta nói 'Hãy gắp vật ở tọa độ X, Y, Z', MoveIt 2 thực hiện hai nhiệm vụ cực kỳ khó: thứ nhất là giải Động học ngược (IK) - tức là dịch từ tọa độ đó ra xem 7 motor khớp của robot phải xoay cụ thể bao nhiêu độ. Thứ hai là Lập kế hoạch chuyển động (Motion Planning) - thuật toán sẽ tìm kiếm hàng ngàn đường đi khả thi trong không gian tự do, chọn ra một đường đi ngắn nhất mà hoàn toàn không va quẹt vào bàn hay va vào chính thân robot. Sau đó, các lệnh điều khiển khớp mượt mà này sẽ được truyền xuống motor thông qua khung phần cứng `ros2_control`."*

---

### Slide 6: Chu trình Gắp - Đặt 11 bước tự động (Thời gian: 1.5 phút)
* **Tiêu đề Slide:** CHU TRÌNH GẮP ĐẶT TUẦN TỰ (11 BƯỚC)
* **Nội dung hiển thị:**
  - **Chuẩn bị:** [1] Về Home $\rightarrow$ [2] Mở kẹp tối đa.
  - **Gắp (Pick):** [3] Tiếp tiếp cận trên vật $\rightarrow$ [4] Hạ xuống gắp vật $\rightarrow$ [5] Đóng kẹp $\rightarrow$ [6] Nhấc lên cao.
  - **Thả (Place):** [7] Di chuyển tới trên điểm đích $\rightarrow$ [8] Hạ xuống điểm đặt $\rightarrow$ [9] Mở kẹp thả vật.
  - **Kết thúc:** [10] Rút tay lên cao $\rightarrow$ [11] Trở về Home để lặp lại chu kỳ.
* **Lời thoại người nói (Speaker Notes):**
  > *"Để việc gắp thả diễn ra an toàn, chúng tôi chia hành động thành chuỗi 11 bước tuần tự khép kín. Robot xuất phát từ vị trí nghỉ (Home), mở tay kẹp sẵn sàng. Robot không lao thẳng vào vật mà đi tới một điểm nằm ngay phía trên vật trước (Pre-grasp) để tránh đâm trực diện, sau đó mới hạ nhẹ xuống để đóng kẹp giữ chặt vật thể. Tương tự khi đặt vật xuống vị trí đích màu xanh, robot hạ vật xuống, mở tay kẹp để thả ra, nhấc cánh tay lên cao rồi mới quay trở lại vị trí nghỉ. Chu trình này giúp robot luôn hoạt động ổn định và tránh được mọi sự va chạm bất ngờ."*

---

### Slide 7: Kết quả đạt được & Demo (Thời gian: 1 phút)
* **Tiêu đề Slide:** KẾT QUẢ ĐẠT ĐƯỢC
* **Nội dung hiển thị:**
  - Hệ thống chạy mượt mà trên môi trường ảo và ảo hóa phần cứng (Mock Hardware).
  - Tích hợp thành công nút thiết lập tọa độ tùy chỉnh qua tệp YAML (`pick_place_params.yaml`).
  - Hệ thống tự động thiết lập lại môi trường (Reset World) để chạy chu kỳ tiếp theo liên tục.
* **Lời thoại người nói (Speaker Notes):**
  > *"Kết quả là chúng tôi đã xây dựng thành công hệ thống gắp thả tự động. Robot hoạt động rất mượt mà. Chúng tôi cũng cấu hình một file YAML đơn giản bên ngoài để người dùng không biết lập trình cũng có thể đổi vị trí gắp hoặc vị trí đặt chỉ bằng cách gõ tọa độ số mới. Hơn nữa, sau mỗi chu kỳ gắp thả thành công, Gazebo tự động reset thế giới ảo để robot có thể chạy liên tục không ngừng nghỉ nhằm phục vụ mục đích kiểm thử độ bền."*

---

### Slide 8: Hỏi & Đáp / Kết luận (Thời gian: 0.5 phút)
* **Tiêu đề Slide:** KẾT LUẬN & HỎI ĐÁP
* **Nội dung hiển thị:**
  - **Ưu điểm:** Độ chính xác cao, tính toán đường đi thông minh tránh va chạm tốt.
  - **Hướng phát triển:** Tích hợp camera AI nhận diện vật thể thay vị nhập tọa độ tĩnh.
  - Cảm ơn thầy cô và các bạn đã lắng nghe!
* **Lời thoại người nói (Speaker Notes):**
  > *"Tóm lại, dự án đã chứng minh được tính khả thi và an toàn của hệ thống tự động hóa gắp thả. Hướng phát triển tiếp theo là chúng tôi sẽ lắp thêm một chiếc camera AI ở đầu gắp để robot tự nhìn và nhận biết vị trí của khối hộp đỏ khi nó bị dịch chuyển tự do, thay vì nhập tọa độ cứng bằng tay như hiện nay. Cảm ơn thầy cô và các bạn đã chú ý lắng nghe, sau đây tôi xin nhận các câu hỏi đóng ý kiến của mọi người."*
