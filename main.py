import sys
import time
import numpy as np
import sounddevice as sd
import json
from PyQt5 import QtWidgets, QtCore, QtGui

CONFIG_FILE = "settings.json"

class WhiteNoiseTester(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.running = False  # Флаг для управления автоматической калибровкой

        # Загрузка настроек
        self.settings = self.load_settings()

        # Языковые настройки
        self.languages = ["English", "Русский"]
        self.current_language = self.settings.get("language", "Русский")
        self.translations = {
            "English": {
                "app_title": "White Noise Channel Tester",
                "input_device": "Input Device:",
                "output_device": "Output Device:",
                "error_margin": "Allowed Error (dB):",
                "test_all_channels": "Test All Channels",
                "not_tested": "Not Tested",
                "channel": "Channel",
                "increase_volume": "Increase Volume",
                "decrease_volume": "Decrease Volume",
                "channel_ok": "Channel is calibrated",
                "no_data": "No data",
                "language": "Language:",
                "frequency_mismatch": "Sample rate mismatch between input and output devices ({input_fs} != {fs}).",
                "device_error": "Device access error: {error}",
                "channel_not_exist": "Channel {channel} does not exist on the selected device.",
                "left_front": "Left Front",
                "right_front": "Right Front",
                "center": "Center",
                "subwoofer": "Subwoofer",
                "left_rear": "Left Rear",
                "right_rear": "Right Rear",
                "left_side": "Left Side",
                "right_side": "Right Side",
                "unknown": "Unknown",
            },
            "Русский": {
                "app_title": "Тестер каналов с белым шумом",
                "input_device": "Устройство ввода:",
                "output_device": "Устройство вывода:",
                "error_margin": "Допустимая погрешность (дБ):",
                "test_all_channels": "Тестировать все каналы",
                "not_tested": "Не тестирован",
                "channel": "Канал",
                "increase_volume": "Увеличьте громкость",
                "decrease_volume": "Уменьшите громкость",
                "channel_ok": "Канал настроен",
                "no_data": "Нет данных",
                "language": "Язык:",
                "frequency_mismatch": "Частоты дискретизации входного и выходного устройств не совпадают ({input_fs} != {fs}).",
                "device_error": "Ошибка доступа к информации об устройстве: {error}",
                "channel_not_exist": "Канал {channel} не существует на выбранном устройстве.",
                "left_front": "Левый фронтальный",
                "right_front": "Правый фронтальный",
                "center": "Центральный",
                "subwoofer": "Сабвуфер",
                "left_rear": "Левый тыловой",
                "right_rear": "Правый тыловой",
                "left_side": "Левый боковой",
                "right_side": "Правый боковой",
                "unknown": "Неизвестно",
            },
        }

        # Установка заголовка окна
        self.setWindowTitle(self.tr("app_title"))
        self.resize(800, 600)

        # Получение списка устройств ввода и вывода, фильтруя по WASAPI
        self.all_devices = sd.query_devices()
        self.hostapis = sd.query_hostapis()
        self.wasapi_hostapi_index = self.get_wasapi_hostapi_index()
        self.input_devices = [(dev['name'], dev['hostapi'], i) for i, dev in enumerate(self.all_devices)
                              if dev['max_input_channels'] > 0 and dev['hostapi'] == self.wasapi_hostapi_index]
        self.output_devices = [(dev['name'], dev['hostapi'], i) for i, dev in enumerate(self.all_devices)
                               if dev['max_output_channels'] > 0 and dev['hostapi'] == self.wasapi_hostapi_index]

        # Проверка наличия WASAPI устройств
        if not self.input_devices or not self.output_devices:
            QtWidgets.QMessageBox.critical(self, self.tr("Error"), self.tr("wasapi_not_found"))
            sys.exit(1)

        # Сортировка устройств по имени
        self.input_devices.sort(key=lambda x: x[0])
        self.output_devices.sort(key=lambda x: x[0])

        # Выбор языка
        self.language_select = QtWidgets.QComboBox()
        self.language_select.addItems(self.languages)
        self.language_select.setCurrentText(self.current_language)
        self.language_select.currentIndexChanged.connect(self.change_language)

        # Выбор устройств
        self.input_select = QtWidgets.QComboBox()
        self.input_select.addItems([self.get_device_display_name(dev) for dev in self.input_devices])
        self.output_select = QtWidgets.QComboBox()
        self.output_select.addItems([self.get_device_display_name(dev) for dev in self.output_devices])

        # Загрузка сохранённых устройств, если они существуют
        self.load_saved_device()

        self.output_select.currentIndexChanged.connect(self.update_channel_buttons)

        # Элемент для выбора допустимой погрешности
        self.error_margin_label = QtWidgets.QLabel(self.tr("error_margin"))
        self.error_margin_spinbox = QtWidgets.QDoubleSpinBox()
        self.error_margin_spinbox.setRange(0.1, 10.0)
        self.error_margin_spinbox.setSingleStep(0.1)
        self.error_margin_spinbox.setValue(0.5)

        # Генерация интерфейса
        self.channel_buttons = []
        self.channel_labels = []
        self.measured_rms_levels = {}  # Словарь для хранения измеренных уровней

        self.layout = QtWidgets.QVBoxLayout()
        language_layout = QtWidgets.QHBoxLayout()
        language_layout.addWidget(QtWidgets.QLabel(self.tr("language")))
        language_layout.addWidget(self.language_select)
        self.layout.addLayout(language_layout)

        self.input_device_label = QtWidgets.QLabel(self.tr("input_device"))
        self.output_device_label = QtWidgets.QLabel(self.tr("output_device"))

        self.layout.addWidget(self.input_device_label)
        self.layout.addWidget(self.input_select)
        self.layout.addWidget(self.output_device_label)
        self.layout.addWidget(self.output_select)

        # Добавление выбора погрешности
        error_layout = QtWidgets.QHBoxLayout()
        error_layout.addWidget(self.error_margin_label)
        error_layout.addWidget(self.error_margin_spinbox)
        self.layout.addLayout(error_layout)

        # Layout для каналов
        self.channels_layout = QtWidgets.QGridLayout()
        self.layout.addLayout(self.channels_layout)

        # Кнопки для тестирования
        buttons_layout = QtWidgets.QHBoxLayout()
        self.test_all_button = QtWidgets.QPushButton(self.tr("test_all_channels"))
        self.test_all_button.clicked.connect(self.test_all_channels)
        buttons_layout.addWidget(self.test_all_button)

        self.layout.addLayout(buttons_layout)

        # Placeholder для схемы динамиков
        self.schematic_label = QtWidgets.QLabel()
        self.schematic_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.schematic_label)

        # Установить основной макет
        self.setLayout(self.layout)

        # Автоматическое обновление кнопок каналов
        self.update_channel_buttons()

    def tr(self, key):
        """Перевод строки в соответствии с текущим языком"""
        return self.translations[self.current_language].get(key, key)

    def change_language(self):
        """Изменение языка интерфейса"""
        self.current_language = self.language_select.currentText()
        self.settings["language"] = self.current_language
        self.save_settings()
        self.update_ui_language()

    def update_ui_language(self):
        """Обновление текста интерфейса при смене языка"""
        self.setWindowTitle(self.tr("app_title"))
        self.error_margin_label.setText(self.tr("error_margin"))
        self.test_all_button.setText(self.tr("test_all_channels"))
        self.input_device_label.setText(self.tr("input_device"))
        self.output_device_label.setText(self.tr("output_device"))
        self.layout.itemAt(0).layout().itemAt(0).widget().setText(self.tr("language"))

        # Обновление кнопок и меток каналов
        self.update_channel_buttons()

    def get_wasapi_hostapi_index(self):
        """Возвращает индекс HostAPI для WASAPI"""
        for i, hostapi in enumerate(self.hostapis):
            if 'wasapi' in hostapi['name'].lower():
                return i
        return None

    def get_device_display_name(self, dev):
        """Возвращает отображаемое имя устройства с типом драйвера"""
        hostapi_info = self.hostapis[dev[1]]
        hostapi_name = hostapi_info['name']
        return f"{dev[0]} ({hostapi_name}) [Index {dev[2]}]"

    def load_settings(self):
        """Загрузка сохранённых настроек"""
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_settings(self):
        """Сохранение текущих настроек"""
        self.settings["input_device"] = self.input_select.currentIndex()
        self.settings["output_device"] = self.output_select.currentIndex()
        self.settings["language"] = self.current_language
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.settings, f)

    def load_saved_device(self):
        """Установка сохранённых устройств при наличии"""
        if "input_device" in self.settings and self.settings["input_device"] < len(self.input_devices):
            self.input_select.setCurrentIndex(self.settings["input_device"])
        if "output_device" in self.settings and self.settings["output_device"] < len(self.output_devices):
            self.output_select.setCurrentIndex(self.settings["output_device"])

    def update_channel_buttons(self):
        """Обновляет количество кнопок каналов в зависимости от выбранного устройства вывода"""
        # Очистка предыдущих элементов
        while self.channels_layout.count():
            item = self.channels_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.channel_buttons.clear()
        self.channel_labels.clear()
        self.measured_rms_levels.clear()  # Очистка измеренных значений

        # Получение информации о количестве каналов
        output_device_index = self.output_select.currentIndex()
        output_device = self.output_devices[output_device_index]
        device_info = sd.query_devices(output_device[2])
        num_channels = device_info['max_output_channels']

        # Сопоставление каналов с позициями динамиков
        self.channel_mapping = self.get_channel_mapping(num_channels)

        for i in range(num_channels):
            button_text = self.tr("Play Channel {i} ({name})").format(
                i=i + 1, name=self.channel_mapping.get(i, self.tr("unknown")))
            button = QtWidgets.QPushButton(button_text)
            button.clicked.connect(lambda _, ch=i: self.test_channel(ch))
            label_text = self.tr("Channel {i} ({name}): {status}").format(
                i=i + 1, name=self.channel_mapping.get(i, self.tr("unknown")), status=self.tr("not_tested"))
            label = QtWidgets.QLabel(label_text)
            self.channel_buttons.append(button)
            self.channel_labels.append(label)
            self.channels_layout.addWidget(button, i, 0)
            self.channels_layout.addWidget(label, i, 1)

        # Обновление схемы динамиков
        self.draw_speaker_schematic(num_channels, self.channel_mapping)

    def get_channel_mapping(self, num_channels):
        """Возвращает сопоставление индексов каналов с позициями динамиков"""
        standard_mappings = {
            2: {
                0: self.tr('left_front'),
                1: self.tr('right_front'),
            },
            6: {
                0: self.tr('left_front'),
                1: self.tr('right_front'),
                2: self.tr('center'),
                3: self.tr('subwoofer'),
                4: self.tr('left_rear'),
                5: self.tr('right_rear'),
            },
            8: {
                0: self.tr('left_front'),
                1: self.tr('right_front'),
                2: self.tr('center'),
                3: self.tr('subwoofer'),
                4: self.tr('left_side'),
                5: self.tr('right_side'),
                6: self.tr('left_rear'),
                7: self.tr('right_rear'),
            },
        }
        return standard_mappings.get(num_channels, {i: self.tr('Channel {i}').format(i=i + 1) for i in range(num_channels)})

    def draw_speaker_schematic(self, num_channels, channel_mapping, current_channel=None):
        """Рисует схему расположения динамиков"""
        pixmap_width = 500  # Уменьшен размер изображения
        pixmap_height = 375
        pixmap = QtGui.QPixmap(pixmap_width, pixmap_height)
        pixmap.fill(QtCore.Qt.white)
        painter = QtGui.QPainter(pixmap)
        font = painter.font()
        font.setPointSize(8)  # Уменьшен размер шрифта
        painter.setFont(font)

        # Позиции динамиков (координаты нормализованы от 0 до 1)
        positions = {
            self.tr('left_front'): (0.3, 0.3),
            self.tr('right_front'): (0.7, 0.3),
            self.tr('center'): (0.5, 0.2),
            self.tr('subwoofer'): (0.5, 0.6),
            self.tr('left_rear'): (0.2, 0.7),
            self.tr('right_rear'): (0.8, 0.7),
            self.tr('left_side'): (0.2, 0.5),
            self.tr('right_side'): (0.8, 0.5),
        }

        for ch_index, speaker in channel_mapping.items():
            pos = positions.get(speaker)
            if pos:
                x = pos[0] * pixmap_width
                y = pos[1] * pixmap_height
            else:
                # Для неизвестных позиций
                x = 0.5 * pixmap_width
                y = 0.85 * pixmap_height

            # Определение цвета динамика
            if ch_index == current_channel:
                painter.setBrush(QtCore.Qt.blue)
            else:
                painter.setBrush(QtCore.Qt.gray)

            painter.setPen(QtCore.Qt.black)
            painter.drawEllipse(QtCore.QPointF(x, y), 10, 10)  # Уменьшен размер динамика
            painter.drawText(int(x + 12), int(y + 5), f"{speaker} ({ch_index + 1})")

        painter.end()
        self.schematic_label.setPixmap(pixmap)

    def generate_white_noise(self, duration, fs):
        """Генерация белого шума"""
        samples = int(duration * fs)
        noise = np.random.normal(0, 0.1, samples).astype(np.float32)
        return noise

    def test_channel(self, channel):
        """Тестирование отдельного канала"""
        input_device_index = self.input_select.currentIndex()
        output_device_index = self.output_select.currentIndex()
        input_device_id = self.input_devices[input_device_index][2]
        output_device_id = self.output_devices[output_device_index][2]

        # Получение информации об устройстве и частоте дискретизации
        try:
            output_device_info = sd.query_devices(output_device_id)
            num_channels = output_device_info['max_output_channels']
            # Установим общую частоту дискретизации
            fs = int(output_device_info['default_samplerate'])
            # Проверим, что частота дискретизации входного устройства совпадает
            input_device_info = sd.query_devices(input_device_id)
            input_fs = int(input_device_info['default_samplerate'])
            if fs != input_fs:
                QtWidgets.QMessageBox.warning(self, self.tr("app_title"),
                                              self.tr("frequency_mismatch").format(input_fs=input_fs, fs=fs))
                return
        except Exception as e:
            print(self.tr("device_error").format(error=e))
            return

        duration = 2.0  # Длительность в секундах

        # Генерация белого шума
        noise = self.generate_white_noise(duration, fs)

        # Подготовка выходного буфера
        outdata = np.zeros((len(noise), num_channels), dtype=np.float32)
        if channel < num_channels:
            outdata[:, channel] = noise
        else:
            print(self.tr("channel_not_exist").format(channel=channel))
            return

        # Обновление схемы динамиков с выделением текущего канала
        self.draw_speaker_schematic(num_channels, self.channel_mapping, current_channel=channel)
        QtWidgets.QApplication.processEvents()

        # Запись и воспроизведение
        try:
            # Используем playrec для одновременного воспроизведения и записи
            recording = sd.playrec(outdata, samplerate=fs, device=(input_device_id, output_device_id),
                                   channels=1, blocking=True, dtype='float32')

            # Расчёт уровня громкости (RMS)
            if recording.size > 0:
                rms_level = 20 * np.log10(np.sqrt(np.mean(recording**2)) + 1e-10)
                self.measured_rms_levels[channel] = rms_level  # Сохранение измеренного уровня

                # Пересчет рекомендаций для всех протестированных каналов
                self.update_recommendations()

                self.save_settings()  # Сохранение настроек

            else:
                self.channel_labels[channel].setText(self.tr("Channel {i}: {status}").format(
                    i=channel + 1, status=self.tr("no_data")))
                self.channel_labels[channel].setStyleSheet("color: black;")

            # Сброс выделения динамика после тестирования
            self.draw_speaker_schematic(num_channels, self.channel_mapping)
            QtWidgets.QApplication.processEvents()

        except Exception as e:
            print(self.tr("Error in test_channel for channel {channel}: {error}").format(channel=channel, error=e))

    def update_recommendations(self):
        """Обновляет рекомендации для всех протестированных каналов"""
        # Получение допустимой погрешности
        error_margin = self.error_margin_spinbox.value()

        # Поиск канала сабвуфера
        subwoofer_channel = None
        for ch_index, name in self.channel_mapping.items():
            if self.tr('subwoofer') in name:
                subwoofer_channel = ch_index
                break

        # Вычисление средней громкости по измеренным каналам (исключая сабвуфер)
        rms_values = [level for ch, level in self.measured_rms_levels.items()
                      if ch != subwoofer_channel]

        if rms_values:
            average_rms = sum(rms_values) / len(rms_values)
        else:
            return  # Нет данных для обновления

        # Обновление рекомендаций для каждого канала
        for ch in self.measured_rms_levels:
            rms_level = self.measured_rms_levels[ch]
            difference = rms_level - average_rms

            if abs(difference) <= error_margin:
                suggestion = self.tr("channel_ok")
                color = "green"
            elif difference < -error_margin:
                suggestion = self.tr("increase_volume")
                color = "red"
            else:
                suggestion = self.tr("decrease_volume")
                color = "red"

            label_text = self.tr("Channel {i}: {rms:.2f} dB ({suggestion})").format(
                i=ch + 1, rms=rms_level, suggestion=suggestion)
            self.channel_labels[ch].setText(label_text)
            self.channel_labels[ch].setStyleSheet(f"color: {color};")

    def test_all_channels(self):
        """Тестирование всех каналов по очереди"""
        for i in range(len(self.channel_buttons)):
            self.test_channel(i)

def main():
    app = QtWidgets.QApplication(sys.argv)
    tester = WhiteNoiseTester()
    tester.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
