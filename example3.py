import sys
import os
from PyQt5.QtWidgets import (QApplication,
                             QWidget, QLabel,
                             QVBoxLayout,
                             QHBoxLayout,
                             QPushButton,
                             QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
import random


global WIDTH
global HEIGHT
WIDTH = 800
HEIGHT = 500


class PuzzlePiece(QLabel):
    def __init__(self, pixmap, piece_number, parent=None):
        super().__init__(parent)
        self.piece_number = piece_number
        self.original_pixmap = pixmap
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)

        # Стили для визуального оформления
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #34495e;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
            QLabel:hover {
                border: 3px solid #e74c3c;
                background-color: #fff;
            }
        """)

        self.setCursor(Qt.OpenHandCursor)
        self.old_position = None
        self.is_in_target_area = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_position = self.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.raise_()  # Поднимаем элемент на передний план

    def mouseMoveEvent(self, event):
        if self.old_position is None:
            return

        # Вычисляем смещение и перемещаем элемент
        current_pos = self.mapToParent(event.pos())
        new_x = current_pos.x() - self.width() // 2
        new_y = current_pos.y() - self.height() // 2

        # Ограничиваем перемещение в пределах родительского виджета
        parent_rect = self.parent().rect()
        new_x = max(0, min(new_x, parent_rect.width() - self.width()))
        new_y = max(0, min(new_y, parent_rect.height() - self.height()))

        self.move(new_x, new_y)

    def mouseReleaseEvent(self, event):
        self.setCursor(Qt.OpenHandCursor)
        self.old_position = None
        self.parent().check_puzzle_completion()


class PuzzleGame(QWidget):
    def __init__(self):
        super().__init__()
        self.pieces = []
        self.target_positions = []
        self.tolerance = 15  # Допустимое отклонение для совпадения
        self.piece_size = (200, 200)  # Размер каждого кусочка
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Capcha')
        self.setGeometry(100, 100, WIDTH, HEIGHT)
        self.setStyleSheet("background-color: #2c3e50;")

        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel('Для успешного выполнения соберите пазл')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 15px;
                background-color: rgba(52, 152, 219, 0.8);
                border-radius: 10px;
            }
        """)
        title.setFont(QFont('Arial', 16, QFont.Bold))

        # Область сборки (целевая область)
        self.assembly_area = QFrame()
        self.assembly_area.setFixedSize(400, 400)
        self.assembly_area.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 3px dashed #7f8c8d;
                border-radius: 10px;
            }
        """)

        # Контейнер для области сборки
        assembly_container = QHBoxLayout()
        assembly_container.addStretch()
        assembly_container.addWidget(self.assembly_area)
        assembly_container.addStretch()

        # Кнопки управления
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        check_button = QPushButton('Проверить')
        check_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)
        check_button.clicked.connect(self.check_puzzle_completion)

        reset_button = QPushButton('Сбросить')
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_button.clicked.connect(self.reset_puzzle)

        button_layout.addStretch()
        button_layout.addWidget(check_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()

        # Статусная строка
        self.status_label = QLabel('Перетащите части картинки')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-size: 14px;
                padding: 10px;
                background-color: rgba(52, 73, 94, 0.8);
                border-radius: 8px;
            }
        """)

        # Сборка layout
        main_layout.addWidget(title)
        main_layout.addLayout(assembly_container)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # Загружаем уже разрезанные изображения
        self.load_precut_images()

        # Располагаем кусочки вокруг области сборки
        self.arrange_pieces_around_assembly_area()

    def load_precut_images(self):
        # """Загружает уже разрезанные изображения из папки"""
        image_dir = "images"

        # Ищем файлы с частями изображения
        image_files = []
        for i in range(1, 5):
            for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                filename = f"{i}{ext}"
                filepath = os.path.join(image_dir, filename)
                if os.path.exists(filepath):
                    image_files.append((i, filepath))
                    break

        # Если нашли все 4 части
        if len(image_files) == 4:
            # Сортируем по номеру
            image_files.sort(key=lambda x: x[0])

            for piece_number, filepath in image_files:
                try:
                    pixmap = QPixmap(filepath)
                    if pixmap.isNull():
                        raise ValueError("Не удалось загрузить изображение")

                    # Масштабируем если нужно
                    if pixmap.width() != self.piece_size[0] or pixmap.height(
                    ) != self.piece_size[1]:
                        pixmap = pixmap.scaled(
                            self.piece_size[0],
                            self.piece_size[1],
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation)

                    piece = PuzzlePiece(pixmap, piece_number, self)
                    self.pieces.append(piece)

                except Exception as e:
                    print(f"Ошибка загрузки {filepath}: {e}")
                    self.create_fallback_pieces()
                    return
        else:
            self.status_label.setText(
                f"Найдено {len(image_files)}/4 частей в папке 'images'")
            self.create_fallback_pieces()
            return

        # Устанавливаем целевые позиции
        self.set_target_positions()

    def set_target_positions(self):
        # """Устанавливает целевые позиции для кусочков"""
        assembly_x = self.assembly_area.x()
        assembly_y = self.assembly_area.y()

        self.target_positions = [
            # верхний левый (1)
            (assembly_x + WIDTH - 600, assembly_y + 100),
            # верхний правый (2)
            (assembly_x + self.piece_size[0] + WIDTH - 600, assembly_y + 100),
            (assembly_x + WIDTH - 600, assembly_y +
             self.piece_size[1] + 100),  # нижний левый (3)
            # нижний правый (4)
            (assembly_x + self.piece_size[0] + WIDTH -
             600, assembly_y + self.piece_size[1] + 100)
        ]
        print(assembly_x, self.piece_size[0])
        print(assembly_y)
        print(self.target_positions)

    def create_fallback_pieces(self):
        # """Создает запасные кусочки если не удалось загрузить изображения"""
        colors = [QColor(231, 76, 60), QColor(241, 196, 15),
                  QColor(46, 204, 113), QColor(52, 152, 219)]

        for i in range(4):
            # Создаем цветной квадрат с номером
            pixmap = QPixmap(self.piece_size[0], self.piece_size[1])
            pixmap.fill(colors[i])

            # Рисуем номер на квадрате
            painter = QPainter(pixmap)
            painter.setPen(Qt.white)
            painter.setFont(QFont('Arial', 48, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, str(i + 1))
            painter.end()

            piece = PuzzlePiece(pixmap, i + 1, self)
            self.pieces.append(piece)

        self.set_target_positions()

    def arrange_pieces_around_assembly_area(self):
        # """Располагает кусочки вокруг области сборки"""
        positions = [
            (random.randint(1, 600), random.randint(1, 300)),
            (random.randint(1, 600), random.randint(1, 300)),
            (random.randint(1, 600), random.randint(1, 300)),
            (random.randint(1, 600), random.randint(1, 300))
        ]

        for i, piece in enumerate(self.pieces):
            if i < len(positions):
                piece.move(*positions[i])
                piece.show()

    def check_puzzle_completion(self):
        # """Проверяет, правильно ли собрана картинка"""
        correct_count = 0

        for i, piece in enumerate(self.pieces):
            if i < len(self.target_positions):
                target_x, target_y = self.target_positions[i]
                current_x, current_y = piece.x(), piece.y()

                # Проверяем, находится ли кусочек близко к целевой позиции
                if (abs(current_x - target_x) <= self.tolerance and
                        abs(current_y - target_y) <= self.tolerance):
                    correct_count += 1
                    piece.setStyleSheet("border: 3px solid #27ae60;")
                else:
                    piece.setStyleSheet("border: 2px solid #34495e;")

        if correct_count == 4:
            self.status_label.setText("Картинка собрана правильно!")
            # self.show_victory_message()
        else:
            self.status_label.setText(
                f"Собрано: {correct_count}/4 частей. Продолжайте!")

    def reset_puzzle(self):
        # """Сбрасывает пазл в начальное состояние"""
        self.arrange_pieces_around_assembly_area()
        for piece in self.pieces:
            piece.setStyleSheet("""
                QLabel {
                    border: 2px solid #34495e;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                }
                QLabel:hover {
                    border: 3px solid #e74c3c;
                    background-color: #fff;
                }
            """)
        self.status_label.setText("Пазл сброшен. Начните заново!")

    def paintEvent(self, event):
        # """Рисует фон и дополнительные элементы"""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(44, 62, 80))

        # Рисуем подсказки целевых позиций
        painter.setPen(QColor(127, 140, 141, 100))
        painter.setFont(QFont('Arial', 12))

        for i, (target_x, target_y) in enumerate(self.target_positions):
            if i < len(self.target_positions):
                painter.drawRect(target_x, target_y,
                                 self.piece_size[0], self.piece_size[1])
                painter.drawText(target_x +
                                 self.piece_size[0] //
                                 2 -
                                 10, target_y +
                                 self.piece_size[1] //
                                 2 +
                                 5, str(i +
                                        1))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    game = PuzzleGame()
    game.show()
    sys.exit(app.exec_())
    
