import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from camera_manager import CameraManager
from eye_tracker import EyeTracker
from ear_detector import EarBlinkDetector
from gesture_controller import BlinkGestureController


class OptiCareTask7Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptiCare - Task 7: Gesture Recognition & Navigation")
        self.resize(1120, 720)
        self.setStyleSheet("background-color: #1e272e;")

        # 1. تهيئة أدوات الإيماءات والرصد المتوافقة مع الكود الجديد
        self.gesture_ctrl = BlinkGestureController(timeout=0.5, cooldown=0.6)
        self.ear_detector = EarBlinkDetector(ear_threshold=0.19, min_blink_duration=0.20, long_blink_duration=1.2)

        # 2. هيكل القوائم الأصلي
        self.menu_hierarchy = {
            "Food": ["Water", "Juice", "Meal", "Back"],
            "Devices": ["Television", "Light", "Air Conditioner", "Back"],
            "Help": ["Call Family", "Call Nurse", "Pain", "Back"],
            "Emergency": ["SOS Doctor", "Emergency Alert", "Back", "Back"],
            "_SubSub": {
                "Television": ["Power", "Volume Up", "Volume Down", "Back"],
                "Light": ["Room Light", "Night Light", "Dim Up", "Back"],
                "Call Family": ["Call Mom", "Call Dad", "Call Brother", "Back"],
            }
        }
        self.main_menu_items = ["Food", "Devices", "Help", "Emergency"]
        self.slot_codes = ["LR", "RL", "RR", "LL"]

        self.current_menu = "Main"
        self.nav_history = []

        # 3. إعدادات مؤقت النظر (Dwell Time = 2.0s للقائمة الرئيسية فقط)
        self.dwell_target_ms = 2000
        self.dwell_step_ms = 50
        self.current_dwell_ms = 0
        self.active_gaze_index = None

        self.dwell_timer = QTimer(self)
        self.dwell_timer.setInterval(self.dwell_step_ms)
        self.dwell_timer.timeout.connect(self.update_dwell_progress)

        self.last_action_time = time.time()
        self.action_cooldown = 1.5

        # بناء عناصر الواجهة
        self.init_ui()

        # إعداد الكاميرا والتتبع
        self.camera_mgr = CameraManager()
        self.eye_tracker = EyeTracker()
        self.camera_mgr.start_camera()

        self.camera_timer = QTimer(self)
        self.camera_timer.setInterval(33)
        self.camera_timer.timeout.connect(self.process_camera_frame)
        self.camera_timer.start()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 20, 30, 20)
        self.main_layout.setSpacing(14)

        # الشريط العلوي
        header_box = QHBoxLayout()
        self.status_header = QLabel("Status: System Ready")
        self.status_header.setFont(QFont("Arial", 13, QFont.Bold))
        self.status_header.setAlignment(Qt.AlignCenter)
        self.status_header.setStyleSheet("background-color: #00b894; color: white; padding: 10px; border-radius: 8px;")

        self.level_header = QLabel("Level: Main Menu")
        self.level_header.setFont(QFont("Arial", 13, QFont.Bold))
        self.level_header.setAlignment(Qt.AlignCenter)
        self.level_header.setStyleSheet("background-color: #0984e3; color: white; padding: 10px; border-radius: 8px;")

        header_box.addWidget(self.status_header, 3)
        header_box.addWidget(self.level_header, 1)
        self.main_layout.addLayout(header_box)

        # شريط التعليمات
        self.instructions = QLabel(
            "MAIN MENU: Hold gaze for 2.0s to select.\n"
            "SUBMENUS: Blink LR=1st, RL=2nd, RR=3rd, LL=4th | Long Left Blink (1.2s) = Back"
        )
        self.instructions.setAlignment(Qt.AlignCenter)
        self.instructions.setFont(QFont("Arial", 11, QFont.Bold))
        self.instructions.setStyleSheet("color: #dcdde1; padding: 2px;")
        self.main_layout.addWidget(self.instructions)
        # شريط التقدم الزمني
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.dwell_target_ms)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background-color: #485460; border-radius: 6px; }
            QProgressBar::chunk { background-color: #fbc531; border-radius: 6px; }
        """)
        self.main_layout.addWidget(self.progress_bar)

        # شبكة الأزرار الأربعة
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(18)
        self.buttons = []

        for i in range(4):
            btn = QPushButton()
            btn.setFont(QFont("Arial", 18, QFont.Bold))
            btn.setMinimumHeight(260)
            btn.clicked.connect(lambda checked, idx=i: self.trigger_selection(idx))
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)

        self.main_layout.addLayout(self.buttons_layout)

        # أشرطة التغذية الراجعة السفلية
        self.current_label = QLabel("Current Target: None")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.current_label.setStyleSheet("background-color: #2f3640; color: #fbc531; padding: 10px; border-radius: 8px;")
        self.main_layout.addWidget(self.current_label)

        self.selected_label = QLabel("Selected Action: None")
        self.selected_label.setAlignment(Qt.AlignCenter)
        self.selected_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.selected_label.setStyleSheet("background-color: #00cec9; color: black; padding: 10px; border-radius: 8px;")
        self.main_layout.addWidget(self.selected_label)

        self.render_menu("Main")

    def render_menu(self, menu_name):
        self.current_menu = menu_name
        self.reset_dwell()
        self.gesture_ctrl.reset_sequence()
        self.last_action_time = time.time()

        if menu_name == "Main":
            items = self.main_menu_items
            self.level_header.setText("Level: Main Menu")
            is_sub = False
        elif menu_name in self.menu_hierarchy:
            items = self.menu_hierarchy[menu_name]
            self.level_header.setText(f"Level: {menu_name}")
            is_sub = True
        elif menu_name in self.menu_hierarchy.get("_SubSub", {}):
            items = self.menu_hierarchy["_SubSub"][menu_name]
            self.level_header.setText(f"Level: {menu_name}")
            is_sub = True
        else:
            items = ["Back", "Back", "Back", "Back"]
            is_sub = True

        for i in range(4):
            if i < len(items):
                base_text = str(items[i])
                display_text = f"{base_text}\n\n[{self.slot_codes[i]}]" if is_sub else base_text
                self.buttons[i].setText(display_text)
                self.buttons[i].setProperty("raw_text", base_text)
                self.buttons[i].setVisible(True)
                self.set_button_style(i, is_focused=False)
            else:
                self.buttons[i].setVisible(False)

        self.current_label.setText(f"Current Target: {menu_name}")

    def set_button_style(self, index, is_focused=False):
        raw = self.buttons[index].property("raw_text") or ""
        if raw == "Back":
            bg = "#636e72"
            border = "#fbc531" if is_focused else "#718093"
        else:
            bg = "#e17055" if is_focused else "#0984e3"
            border = "#ffeaa7" if is_focused else "#74b9ff"

        style = (
            f"QPushButton {{"
            f"background-color: {bg};"
            f"color: #ffffff;"
            f"font-size: 20px;"
            f"font-weight: bold;"
            f"border: 4px solid {border};"
            f"border-radius: 16px;"
            f"text-align: center;"
            f"}}"
        )
        self.buttons[index].setStyleSheet(style)

    def process_camera_frame(self):
        frame = self.camera_mgr.get_frame()
        if frame is None:
            return

        left_ear, right_ear, ear, blinks, gaze = self.eye_tracker.process_frame(frame)
        # التحقق من وجود الوجه والعينين
        if left_ear is None or right_ear is None or left_ear < 0.08 or right_ear < 0.08:
            if self.active_gaze_index is not None:
                self.reset_dwell()
            self.status_header.setText("Status: Face / Eyes Not Detected")
            self.status_header.setStyleSheet("background-color: #d63031; color: white; padding: 10px; border-radius: 8px;")
            return

        self.status_header.setText("Status: Tracking Active")
        self.status_header.setStyleSheet("background-color: #00b894; color: white; padding: 10px; border-radius: 8px;")

        # 1. القائمة الرئيسية: تثبيت النظر (Gaze Dwell)
        if self.current_menu == "Main":
            target_idx = None
            if gaze == "Looking Right":
                target_idx = 0  # Food
            elif gaze == "Looking Center":
                target_idx = 1  # Devices
            elif gaze == "Looking Left":
                target_idx = 2  # Help

            if target_idx is not None:
                if self.active_gaze_index != target_idx:
                    self.start_dwell(target_idx)
            else:
                if self.active_gaze_index is not None:
                    self.reset_dwell()

        # 2. القوائم الفرعية: الرمشات فقط
        else:
            if time.time() - self.last_action_time > self.action_cooldown:
                res = self.ear_detector.process_frame(left_ear, right_ear, self.gesture_ctrl)
                if res:
                    self.handle_gesture_result(res)

    def start_dwell(self, index):
        if self.current_menu != "Main" or self.active_gaze_index == index:
            return

        self.reset_dwell()
        self.active_gaze_index = index
        self.current_dwell_ms = 0
        raw = self.buttons[index].property("raw_text") or ""
        self.current_label.setText(f"Current Target: {raw} (Hold 2s...)")
        self.set_button_style(index, is_focused=True)
        self.dwell_timer.start()

    def update_dwell_progress(self):
        self.current_dwell_ms += self.dwell_step_ms
        self.progress_bar.setValue(min(self.current_dwell_ms, self.dwell_target_ms))

        if self.current_dwell_ms >= self.dwell_target_ms:
            selected_idx = self.active_gaze_index
            self.reset_dwell()
            if selected_idx is not None and (time.time() - self.last_action_time) > self.action_cooldown:
                self.trigger_selection(selected_idx)

    def reset_dwell(self):
        self.dwell_timer.stop()
        self.current_dwell_ms = 0
        self.progress_bar.setValue(0)
        if self.active_gaze_index is not None and self.active_gaze_index < len(self.buttons):
            self.set_button_style(self.active_gaze_index, is_focused=False)
        self.active_gaze_index = None

    def go_back(self):
        self.reset_dwell()
        self.gesture_ctrl.reset_sequence()
        prev = self.nav_history.pop() if self.nav_history else "Main"
        self.render_menu(prev)
        self.selected_label.setText("Selected Action: Returned Back")

    def handle_gesture_result(self, result):
        if not result:
            return

        # أمر الرمشة الطويلة للرجوع
        if result.get("type") == "COMMAND" and result.get("action") == "BACK":
            self.selected_label.setText("Gesture: Long Left Blink -> Back")
            self.go_back()
        elif result.get("type") == "BUFFER":
            self.current_label.setText(f"Blink Buffer: [{result.get('current_sequence')}]")
        elif result.get("type") == "SELECTION":
            seq = result.get("sequence")
            self.selected_label.setText(f"Executed: [{seq}]")
            mapping = {"LR": 0, "RL": 1, "RR": 2, "LL": 3}
            if seq in mapping:
                self.trigger_selection(mapping[seq])

    def trigger_selection(self, index):
        self.reset_dwell()
        self.gesture_ctrl.reset_sequence()
        self.last_action_time = time.time()
        raw = self.buttons[index].property("raw_text")

        if not raw or raw == "Back":
            self.go_back()
            return

        if self.current_menu == "Main":
            if raw in self.menu_hierarchy:
                self.nav_history.append("Main")
                self.render_menu(raw)
                self.selected_label.setText(f"Selected: {raw}")

        elif self.current_menu in self.menu_hierarchy:
            if raw in self.menu_hierarchy.get("_SubSub", {}):
                self.nav_history.append(self.current_menu)
                self.render_menu(raw)
                self.selected_label.setText(f"Selected: {raw}")
            else:
                self.selected_label.setText(f"Action Executed: {raw}")

        elif self.current_menu in self.menu_hierarchy.get("_SubSub", {}):
            self.selected_label.setText(f"Action Executed: {raw}")

    def closeEvent(self, event):
        self.camera_timer.stop()
        self.camera_mgr.release_camera()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OptiCareTask7Window()
    window.show()
    sys.exit(app.exec_())