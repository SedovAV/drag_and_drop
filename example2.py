import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QPoint

# Целевые позиции — теперь соответствуют твоему расположению
TARGET_POS = {
    "Label 1": (50, 50),
    "Label 3": (50, 100),
    "Label 2": (150, 50),
    "Label 4": (150, 100)
}

TOLERANCE = 15


class DraggableLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(100, 50)
        self.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                text-align: center;
            }
        """)
        self.setAlignment(Qt.AlignCenter)
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        # Вызываем проверку после отпускания
        self.parent().check_position()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Собери квадрат!")
        self.setGeometry(300, 300, 600, 400)
        self.setStyleSheet("background-color: #f0f0f0;")

        # Создаём 4 метки
        self.labels = {}
        for i in range(1, 5):
            label = DraggableLabel(f"Label {i}", self)
            # Позиционируем начально
            x = 50 + ((i % 2) * 100)
            y = 50 + (((i - 1) // 2) * 50)
            label.move(x, y)
            self.labels[f"Label {i}"] = label

    def check_position(self):
        positions = {}
        for name, label in self.labels.items():
            positions[name] = (label.x(), label.y())

        correct = True
        for name, (target_x, target_y) in TARGET_POS.items():
            x, y = positions[name]
            if abs(x - target_x) > TOLERANCE or abs(y - target_y) > TOLERANCE:
                correct = False
                break

        if correct:
            print("🎉 Поздравляем! Вы собрали квадрат!")
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
