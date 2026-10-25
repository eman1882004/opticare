import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class OptiCareWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OptiCare - Patient Control Interface")
        self.resize(1050, 650)

        # هيكل القوائم ثلاثي المستويات
        self.menu_hierarchy = {
            "Main": ["Food", "Devices", "Help", "Emergency"],
            "Sub": {
                "Food": ["Water", "Juice", "Meal", "Back"],
                "Devices": ["Television", "Light", "Air Conditioner", "Back"],
                "Help": ["Call Family", "Call Nurse", "Pain", "Back"],
                "Emergency": ["SOS Doctor", "Emergency Alert", "Back", "Back"],
            },
            "SubSub": {
                "Television": ["Power", "Volume Up", "Volume Down", "Back"],
                "Light": ["Room Light", "Night Light", "Dim Up", "Back"],
                "Call Family": ["Call Mom", "Call Dad", "Call Brother", "Back"],
            }
        }

        self.current_menu = "Main"
        self.nav_history = []
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 25, 30, 25)
        self.main_layout.setSpacing(15)

        # 1. الشريط العلوي
        header_box = QHBoxLayout()
        self.status_header = QLabel("Status: Ready - 3-Level Menu System")
        self.status_header.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_header.setStyleSheet("background-color: #00b894; color: white; padding: 10px; border-radius: 6px;")

        self.level_header = QLabel("Level: Main Menu")
        self.level_header.setFont(QFont("Arial", 14, QFont.Bold))
        self.level_header.setStyleSheet("background-color: #6c5ce7; color: white; padding: 10px; border-radius: 6px;")

        header_box.addWidget(self.status_header, 3)
        header_box.addWidget(self.level_header, 1)
        self.main_layout.addLayout(header_box)

        # 2. شريط التعليمات
        instructions = QLabel("LEVEL 1: 2s Gaze  |  LEVEL 2/3: Blink Gestures  |  BACK: Long Left Blink (1.2s)")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setFont(QFont("Arial", 11, QFont.Bold))
        instructions.setStyleSheet("color: #636e72; padding: 4px;")
        self.main_layout.addWidget(instructions)

        # 3. الأزرار الأربعة الأفقية
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(20)
        self.buttons = []

        for i in range(4):
            btn = QPushButton("")
            btn.setFont(QFont("Arial", 18, QFont.Bold))
            btn.setMinimumHeight(240)
            btn.clicked.connect(lambda checked, idx=i: self.handle_button_click(idx))
            self.buttons_layout.addWidget(btn)
            self.buttons.append(btn)

        self.main_layout.addLayout(self.buttons_layout)

        # 4. أشرطة الحالة السفلية
        self.current_label = QLabel("Current: None")
        self.current_label.setAlignment(Qt.AlignCenter)
        self.current_label.setFont(QFont("Arial", 15, QFont.Bold))
        self.current_label.setStyleSheet("background-color: #2d3436; color: white; padding: 10px; border-radius: 6px;")
        self.main_layout.addWidget(self.current_label)

        self.selected_label = QLabel("Selected: None")
        self.selected_label.setAlignment(Qt.AlignCenter)
        self.selected_label.setFont(QFont("Arial", 15, QFont.Bold))
        self.selected_label.setStyleSheet("background-color: #0984e3; color: white; padding: 10px; border-radius: 6px;")
        self.main_layout.addWidget(self.selected_label)

        # عرض القائمة الأولى
        self.render_menu("Main")

    def render_menu(self, menu_name):
        self.current_menu = menu_name
        if menu_name == "Main":
            items = self.menu_hierarchy["Main"]
            self.level_header.setText("Level: Main Menu")
        elif menu_name in self.menu_hierarchy["Sub"]:
            items = self.menu_hierarchy["Sub"][menu_name]
            self.level_header.setText(f"Level: Sub Menu ({menu_name})")
        elif menu_name in self.menu_hierarchy["SubSub"]:
            items = self.menu_hierarchy["SubSub"][menu_name]
            self.level_header.setText(f"Level: Action Menu ({menu_name})")
        else:
            items = ["Back", "Back", "Back", "Back"]

        for i in range(4):
            if i < len(items):
                text = items[i]
                self.buttons[i].setText(text)
                self.buttons[i].setVisible(True)

                if text == "Back":
                    self.buttons[i].setStyleSheet("""
                        QPushButton {
                            background-color: #636e72;
                            color: white;
                            border: 4px solid #b2bec3;
                            border-radius: 15px;
                        }
                    """)
                else:
                    self.buttons[i].setStyleSheet("""
                        QPushButton {
                            background-color: #0984e3;
                            color: white;
                            border: 4px solid #74b9ff;
                            border-radius: 15px;
                        }
                        QPushButton:hover {
                            background-color: #00b894;
                            border: 4px solid #55efc4;
                        }
                    """)
            else:
                self.buttons[i].setVisible(False)

    def handle_button_click(self, index):
        if self.current_menu == "Main":
            items = self.menu_hierarchy["Main"]
            selected_item = items[index]
            if selected_item in self.menu_hierarchy["Sub"]:
                self.nav_history.append(self.current_menu)
                self.render_menu(selected_item)
                self.selected_label.setText(f"Selected: {selected_item}")

        elif self.current_menu in self.menu_hierarchy["Sub"]:
            items = self.menu_hierarchy["Sub"][self.current_menu]
            selected_item = items[index]

            if selected_item == "Back":
                prev = self.nav_history.pop() if self.nav_history else "Main"
                self.render_menu(prev)
                self.selected_label.setText("Selected: Back")
            elif selected_item in self.menu_hierarchy["SubSub"]:
                self.nav_history.append(self.current_menu)
                self.render_menu(selected_item)
                self.selected_label.setText(f"Selected: {selected_item}")
            else:
                self.selected_label.setText(f"Action Executed: {selected_item}")

        elif self.current_menu in self.menu_hierarchy["SubSub"]:
            items = self.menu_hierarchy["SubSub"][self.current_menu]
            selected_item = items[index]

            if selected_item == "Back":
                prev = self.nav_history.pop() if self.nav_history else "Main"
                self.render_menu(prev)
                self.selected_label.setText("Selected: Back")
            else:
                self.selected_label.setText(f"Action Executed: {selected_item}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OptiCareWindow()
    window.show()
    sys.exit(app.exec_())