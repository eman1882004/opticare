import os
from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap


class ImageButton(QPushButton):
    """زر كبير ومخصص للمريض يجمع بين الصورة والنص بشكل واضح"""
    def init(self, text="", image_path=None, parent=None):
        super().init(parent)
        self.text_label = text
        self.image_path = image_path
        self.setMinimumSize(180, 220)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # مساحة الصورة
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        if self.image_path and os.path.exists(self.image_path):
            pix = QPixmap(self.image_path).scaled(140, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(pix)
        else:
            self.img_label.setText("[No Image]")
            self.img_label.setStyleSheet("color: #b2bec3; font-size: 13px;")
        layout.addWidget(self.img_label)

        # مساحة النص
        self.lbl = QLabel(self.text_label)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl.setStyleSheet("color: white;")
        layout.addWidget(self.lbl)

        self.update_style(False)

    def update_style(self, is_hovered):
        if is_hovered:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #00b894;
                    border: 4px solid #55efc4;
                    border-radius: 15px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0984e3;
                    border: 4px solid #74b9ff;
                    border-radius: 15px;
                }
            """)

    def set_hover(self, active=True):
        self.update_style(active)