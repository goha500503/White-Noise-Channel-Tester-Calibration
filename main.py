import sys
import numpy as np
import sounddevice as sd
import json
from PyQt5 import QtWidgets, QtCore, QtGui
import matplotlib
import functools
import scipy.signal
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

CONFIG_FILE = "settings.json"

class WhiteNoiseTester(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

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
                "show_fr": "Show FR",
                "wasapi_not_found": "WASAPI devices not found.",
                "Error": "Error",
                "overall_fr": "Overall Frequency Response",
                "channel_fr": "Channel {i} Frequency Response",
                "channel_not_tested": "Channel {i} not tested yet.",
                "frequency_ticks": "Frequency Ticks (Hz):",
                "apply": "Apply",
                "show_overall_fr": "Show Overall FR",
                "Frequency ticks updated.": "Frequency ticks updated.",
                "Invalid frequency ticks input.": "Invalid frequency ticks input.",
                "No data to display overall frequency response.": "No data to display overall frequency response.",
                "Play Channel {i} ({name})": "Play Channel {i} ({name})",
                "Channel {i}: {status}": "Channel {i}: {status}",
                "Channel {i}: {rms:.2f} dB ({suggestion})": "Channel {i}: {rms:.2f} dB ({suggestion})",
                "auto_show_fr": "Auto Show FR after test",
                "test_duration": "Test Duration (s):",
                "Raw FR": "Raw FR",
                "Smoothed FR": "Smoothed FR",
                "Filtered FR": "Filtered FR",
                "Frequency (Hz)": "Frequency (Hz)",
                "Amplitude (dB)": "Amplitude (dB)",
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
                "show_fr": "Показать АЧХ",
                "wasapi_not_found": "Устройства WASAPI не найдены.",
                "Error": "Ошибка",
                "overall_fr": "Общая АЧХ",
                "channel_fr": "АЧХ канала {i}",
                "channel_not_tested": "Канал {i} еще не протестирован.",
                "frequency_ticks": "Метки частот (Гц):",
                "apply": "Применить",
                "show_overall_fr": "Показать общую АЧХ",
                "Frequency ticks updated.": "Метки частот обновлены.",
                "Invalid frequency ticks input.": "Неверный ввод меток частот.",
                "No data to display overall frequency response.": "Нет данных для отображения общей АЧХ.",
                "Play Channel {i} ({name})": "Тестировать канал {i} ({name})",
                "Channel {i}: {status}": "Канал {i}: {status}",
                "Channel {i}: {rms:.2f} dB ({suggestion})": "Канал {i}: {rms:.2f} дБ ({suggestion})",
                "auto_show_fr": "Авто показ АЧХ после теста",
                "test_duration": "Длительность теста (с):",
                "Raw FR": "Сырой АЧХ",
                "Smoothed FR": "Сглаженный АЧХ",
                "Filtered FR": "Отфильтрованный АЧХ",
                "Frequency (Hz)": "Частота (Гц)",
                "Amplitude (dB)": "Амплитуда (дБ)",
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
        self.error_margin_spinbox.setValue(self.settings.get("error_margin", 1.0))

        # Метки частот и кнопка применения
        self.frequency_ticks_label = QtWidgets.QLabel(self.tr("frequency_ticks"))
        self.frequency_ticks_input = QtWidgets.QLineEdit(self.settings.get("frequency_ticks_input", "32,64,125,250,500,1000,2000,4000,8000,16000"))
        self.frequency_ticks_apply_button = QtWidgets.QPushButton(self.tr("apply"))
        self.frequency_ticks_apply_button.clicked.connect(self.apply_frequency_ticks)
        self.frequency_ticks = [float(f.strip()) for f in self.frequency_ticks_input.text().split(',')]

        # Чекбокс для автоматического отображения АЧХ после теста
        self.auto_show_fr_checkbox = QtWidgets.QCheckBox(self.tr("auto_show_fr"))
        self.auto_show_fr_checkbox.setChecked(self.settings.get("auto_show_fr", True))

        # Элемент для выбора длительности теста
        self.test_duration_label = QtWidgets.QLabel(self.tr("test_duration"))
        self.test_duration_spinbox = QtWidgets.QDoubleSpinBox()
        self.test_duration_spinbox.setRange(1.5, 10.0)
        self.test_duration_spinbox.setSingleStep(0.1)
        self.test_duration_spinbox.setValue(self.settings.get("test_duration", 2.0))  # Значение по умолчанию

        # Генерация интерфейса
        self.channel_buttons = []
        self.channel_labels = []
        self.channel_fr_buttons = []
        self.measured_rms_levels = {}  # Словарь для хранения измеренных уровней
        self.channel_fr_data = {}  # Словарь для хранения данных АЧХ каналов
        self.channel_fr_windows = {}  # Словарь для хранения окон АЧХ каналов

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

        # Добавление настроек меток частот
        freq_layout = QtWidgets.QHBoxLayout()
        freq_layout.addWidget(self.frequency_ticks_label)
        freq_layout.addWidget(self.frequency_ticks_input)
        freq_layout.addWidget(self.frequency_ticks_apply_button)
        self.layout.addLayout(freq_layout)

        # Добавление выбора длительности теста
        duration_layout = QtWidgets.QHBoxLayout()
        duration_layout.addWidget(self.test_duration_label)
        duration_layout.addWidget(self.test_duration_spinbox)
        self.layout.addLayout(duration_layout)

        # Добавление чекбокса для автоматического отображения АЧХ
        self.layout.addWidget(self.auto_show_fr_checkbox)

        # Layout для каналов
        self.channels_layout = QtWidgets.QGridLayout()
        self.layout.addLayout(self.channels_layout)

        # Кнопки для тестирования
        buttons_layout = QtWidgets.QHBoxLayout()
        self.test_all_button = QtWidgets.QPushButton(self.tr("test_all_channels"))
        self.test_all_button.clicked.connect(self.test_all_channels)
        buttons_layout.addWidget(self.test_all_button)

        # Кнопка для отображения общей АЧХ
        self.show_overall_fr_button = QtWidgets.QPushButton(self.tr("show_overall_fr"))
        self.show_overall_fr_button.clicked.connect(self.show_overall_fr)
        buttons_layout.addWidget(self.show_overall_fr_button)

        self.layout.addLayout(buttons_layout)

        # Placeholder для схемы динамиков
        self.schematic_label = QtWidgets.QLabel()
        self.schematic_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.schematic_label)

        # Установить основной макет
        self.setLayout(self.layout)

        # Автоматическое обновление кнопок каналов
        self.update_channel_buttons()

        # Инициализация данных для общей АЧХ
        self.overall_fr_data = None
        self.overall_fr_window = None  # Окно для общей АЧХ

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
        self.frequency_ticks_label.setText(self.tr("frequency_ticks"))
        self.frequency_ticks_apply_button.setText(self.tr("apply"))
        self.show_overall_fr_button.setText(self.tr("show_overall_fr"))
        self.auto_show_fr_checkbox.setText(self.tr("auto_show_fr"))
        self.test_duration_label.setText(self.tr("test_duration"))

        # Обновление кнопок и меток каналов без очистки данных
        self.update_channel_buttons(clear_data=False)

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
        self.settings["error_margin"] = self.error_margin_spinbox.value()
        self.settings["frequency_ticks_input"] = self.frequency_ticks_input.text()
        self.settings["auto_show_fr"] = self.auto_show_fr_checkbox.isChecked()
        self.settings["test_duration"] = self.test_duration_spinbox.value()
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.settings, f)

    def load_saved_device(self):
        """Установка сохранённых устройств при наличии"""
        if "input_device" in self.settings and self.settings["input_device"] < len(self.input_devices):
            self.input_select.setCurrentIndex(self.settings["input_device"])
        if "output_device" in self.settings and self.settings["output_device"] < len(self.output_devices):
            self.output_select.setCurrentIndex(self.settings["output_device"])

    def update_channel_buttons(self, clear_data=True):
        """Обновляет количество кнопок каналов в зависимости от выбранного устройства вывода"""
        # Очистка предыдущих элементов
        while self.channels_layout.count():
            item = self.channels_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.channel_buttons.clear()
        self.channel_labels.clear()
        self.channel_fr_buttons.clear()

        if clear_data:
            self.measured_rms_levels.clear()  # Очистка измеренных значений
            self.channel_fr_data.clear()      # Очистка данных АЧХ
        # Не очищаем self.channel_fr_windows, чтобы окна оставались открытыми

        # Получение информации об устройстве
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
            # Используем functools.partial для корректного захвата переменной i
            button.clicked.connect(functools.partial(self.test_channel, i))
            if i in self.measured_rms_levels:
                rms_level = self.measured_rms_levels[i]
                suggestion = self.tr("channel_ok")
                label_text = self.tr("Channel {i}: {rms:.2f} dB ({suggestion})").format(
                    i=i + 1, rms=rms_level, suggestion=suggestion)
            else:
                label_text = self.tr("Channel {i} ({name}): {status}").format(
                    i=i + 1, name=self.channel_mapping.get(i, self.tr("unknown")), status=self.tr("not_tested"))
            label = QtWidgets.QLabel(label_text)

            # Добавляем кнопку для отображения АЧХ канала
            fr_button = QtWidgets.QPushButton(self.tr("show_fr"))
            # Используем functools.partial
            fr_button.clicked.connect(functools.partial(self.show_channel_fr, i))
            self.channel_fr_buttons.append(fr_button)

            self.channel_buttons.append(button)
            self.channel_labels.append(label)
            self.channels_layout.addWidget(button, i, 0)
            self.channels_layout.addWidget(label, i, 1)
            self.channels_layout.addWidget(fr_button, i, 2)

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

    def test_channel(self, channel, from_autotest=False):
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

        # Получаем длительность теста из спинбокса
        duration = self.test_duration_spinbox.value()

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

            # Обрезаем запись, чтобы начать с 0.25 сек и закончить за 0.25 сек до конца
            start_sample = int(0.25 * fs)
            end_sample = int((duration - 0.25) * fs)
            if end_sample > start_sample:
                recording = recording[start_sample:end_sample]
            else:
                print("Recording duration too short after trimming.")
                return

            # Расчёт уровня громкости (RMS)
            if recording.size > 0:
                rms_level = 20 * np.log10(np.sqrt(np.mean(recording ** 2)) + 1e-10)
                self.measured_rms_levels[channel] = rms_level  # Сохранение измеренного уровня

                # Сохранение данных АЧХ
                self.channel_fr_data[channel] = (recording.flatten(), fs)

                # Пересчет рекомендаций для всех протестированных каналов
                self.update_recommendations()

                self.save_settings()  # Сохранение настроек

                # Отображение АЧХ текущего канала, если включено и не из автотеста
                if self.auto_show_fr_checkbox.isChecked() and not from_autotest:
                    self.show_channel_fr(channel)

            else:
                self.channel_labels[channel].setText(self.tr("Channel {i}: {status}").format(
                    i=channel + 1, status=self.tr("no_data")))
                self.channel_labels[channel].setStyleSheet("color: black;")

            # Сброс выделения динамика после тестирования
            self.draw_speaker_schematic(num_channels, self.channel_mapping)
            QtWidgets.QApplication.processEvents()

        except Exception as e:
            print(self.tr("Error in test_channel for channel {channel}: {error}").format(channel=channel, error=e))

    def apply_frequency_ticks(self):
        """Применение пользовательских меток частот"""
        try:
            ticks = [float(f.strip()) for f in self.frequency_ticks_input.text().split(',')]
            if not ticks:
                raise ValueError
            self.frequency_ticks = ticks
            QtWidgets.QMessageBox.information(self, self.tr("app_title"), self.tr("Frequency ticks updated."))
            self.save_settings()  # Сохранение настроек
        except ValueError:
            QtWidgets.QMessageBox.warning(self, self.tr("app_title"), self.tr("Invalid frequency ticks input."))

    def resample_spectrum(self, freqs, spectrum, num_points=1000):
        """Пересэмплирование спектра до фиксированного количества точек"""
        log_freqs = np.logspace(np.log10(freqs[1]), np.log10(freqs[-1]), num_points)
        interp_spectrum = np.interp(log_freqs, freqs, spectrum)
        return log_freqs, interp_spectrum

    def smooth_spectrum_variable(self, spectrum, freqs):
        """Сглаживание спектра с переменным размером окна на логарифмической шкале"""
        num_points = len(freqs)
        window_sizes = (np.log(freqs + 1e-10) * 5).astype(int)
        window_sizes = np.maximum(window_sizes | 1, 3)  # Обеспечиваем нечетность и минимум 3

        # Ограничим максимальный размер окна для ускорения
        max_window_size = 101
        window_sizes = np.minimum(window_sizes, max_window_size)

        smoothed = np.copy(spectrum)
        unique_window_sizes = np.unique(window_sizes)
        for ws in unique_window_sizes:
            indices = np.where(window_sizes == ws)[0]
            half_ws = ws // 2
            for idx in indices:
                start = max(0, idx - half_ws)
                end = min(num_points, idx + half_ws + 1)
                smoothed[idx] = np.mean(spectrum[start:end])
        return smoothed

    def savgol_filter_spectrum(self, spectrum):
        """Применение фильтра Савицкого-Гола к спектру"""
        polyorder = 3
        window_length = 101  # Должно быть нечетным и больше polyorder
        if window_length > len(spectrum):
            window_length = len(spectrum) - (1 - len(spectrum) % 2)
        filtered_spectrum = scipy.signal.savgol_filter(spectrum, window_length, polyorder)
        return filtered_spectrum

    def compute_fr(self, data, fs):
        """Вычисление АЧХ"""
        N = len(data)
        window = np.hanning(N)
        data_windowed = data * window
        spectrum = np.abs(np.fft.rfft(data_windowed)) / np.sum(window)
        freqs = np.fft.rfftfreq(N, 1 / fs)
        return freqs, spectrum

    def map_frequencies(self, freqs, freq_ticks):
        """Маппинг частот на позиции оси X с равными интервалами между метками частот."""
        freq_ticks = np.array(freq_ticks)
        positions = np.arange(len(freq_ticks))
        n = len(freq_ticks) - 1  # Количество интервалов

        x_positions = np.zeros_like(freqs, dtype=float)
        indices = np.searchsorted(freq_ticks, freqs, side='right') - 1

        # Ограничиваем индексы допустимым диапазоном
        indices = np.clip(indices, 0, n - 1)

        fi = freq_ticks[indices]
        fi1 = freq_ticks[indices + 1]
        xi = positions[indices]
        xi1 = positions[indices + 1]

        # Избегаем деления на ноль в случаях, когда fi == fi1
        valid = fi1 > fi
        x_positions[valid] = xi[valid] + (freqs[valid] - fi[valid]) / (fi1[valid] - fi[valid]) * (xi1[valid] - xi[valid])
        x_positions[~valid] = xi[~valid]  # Для недопустимых интервалов присваиваем xi

        return x_positions

    def show_channel_fr(self, channel, temporary=False):
        """Отображение АЧХ канала в отдельном окне с равными интервалами между метками частот."""
        if channel not in self.channel_fr_data:
            QtWidgets.QMessageBox.information(self, self.tr("app_title"),
                                              self.tr("channel_not_tested").format(i=channel + 1))
            return

        data, fs = self.channel_fr_data[channel]
        freqs, spectrum = self.compute_fr(data, fs)

        # Включаем 0 и 20000 Гц в список меток частот
        freq_ticks = [0] + sorted(set(self.frequency_ticks)) + [20000]

        # Маппинг частот на позиции оси X
        x_positions = self.map_frequencies(freqs, freq_ticks)

        # Сглаживание и фильтрация спектра
        smoothed_spectrum = self.smooth_spectrum_variable(spectrum, freqs)
        filtered_spectrum = self.savgol_filter_spectrum(smoothed_spectrum)

        # Обеспечиваем, что спектры не содержат отрицательных значений
        spectrum = np.abs(spectrum)
        smoothed_spectrum = np.abs(smoothed_spectrum)
        filtered_spectrum = np.abs(filtered_spectrum)

        # Создание нового окна
        fr_window = QtWidgets.QWidget()
        fr_window.setWindowTitle(self.tr("channel_fr").format(i=channel + 1))
        layout = QtWidgets.QVBoxLayout()
        canvas = FigureCanvas(Figure(figsize=(6, 4)))
        layout.addWidget(canvas)
        fr_window.setLayout(layout)

        # Отрисовка графика
        ax = canvas.figure.add_subplot(111)
        ax.plot(x_positions, 20 * np.log10(spectrum + 1e-10), label=self.tr('Raw FR'))
        ax.plot(x_positions, 20 * np.log10(smoothed_spectrum + 1e-10), label=self.tr('Smoothed FR'), linewidth=2)
        ax.plot(x_positions, 20 * np.log10(filtered_spectrum + 1e-10), label=self.tr('Filtered FR'), linewidth=2)
        ax.set_title(self.tr("channel_fr").format(i=channel + 1))
        ax.set_xlabel(self.tr("Frequency (Hz)"))
        ax.set_ylabel(self.tr("Amplitude (dB)"))
        ax.grid(True, which='both', ls='--', lw=0.5)
        ax.legend()

        # Устанавливаем метки оси X в соответствии с частотами
        positions = np.arange(len(freq_ticks))
        ax.set_xticks(positions)
        ax.set_xticklabels([str(int(f)) for f in freq_ticks])

        # Устанавливаем пределы по оси X
        ax.set_xlim(positions[0], positions[-1])

        # Автоматическая настройка оси амплитуды
        all_data_dB = 20 * np.log10(np.concatenate([spectrum, smoothed_spectrum, filtered_spectrum]) + 1e-10)
        y_min = np.nanmin(all_data_dB)
        y_max = np.nanmax(all_data_dB)
        y_margin = (y_max - y_min) * 0.1  # 10% запас
        ax.set_ylim(y_min - y_margin, y_max + y_margin)

        canvas.draw()

        fr_window.show()

        # Сохранение ссылки на окно, чтобы оно не закрывалось
        self.channel_fr_windows[channel] = fr_window

        if temporary:
            # Закрытие окна через 2 секунды
            QtCore.QTimer.singleShot(2000, lambda: self.close_temporary_fr_window(channel))

    def show_overall_fr(self):
        """Отображение общей АЧХ в отдельном окне с равными интервалами между метками частот."""
        if not self.channel_fr_data:
            QtWidgets.QMessageBox.information(self, self.tr("app_title"),
                                              self.tr("No data to display overall frequency response."))
            return

        # Собираем все данные
        all_data = []
        for data, fs in self.channel_fr_data.values():
            all_data.append(data)
        all_data = np.concatenate(all_data)

        # Вычисляем АЧХ
        freqs, spectrum = self.compute_fr(all_data, fs)

        # Включаем 0 и 20000 Гц в список меток частот
        freq_ticks = [0] + sorted(set(self.frequency_ticks)) + [20000]

        # Маппинг частот на позиции оси X
        x_positions = self.map_frequencies(freqs, freq_ticks)

        # Сглаживание и фильтрация спектра
        smoothed_spectrum = self.smooth_spectrum_variable(spectrum, freqs)
        filtered_spectrum = self.savgol_filter_spectrum(smoothed_spectrum)

        # Обеспечиваем, что спектры не содержат отрицательных значений
        spectrum = np.abs(spectrum)
        smoothed_spectrum = np.abs(smoothed_spectrum)
        filtered_spectrum = np.abs(filtered_spectrum)

        # Создание нового окна
        fr_window = QtWidgets.QWidget()
        fr_window.setWindowTitle(self.tr("overall_fr"))
        layout = QtWidgets.QVBoxLayout()
        canvas = FigureCanvas(Figure(figsize=(6, 4)))
        layout.addWidget(canvas)
        fr_window.setLayout(layout)

        # Отрисовка графика
        ax = canvas.figure.add_subplot(111)
        ax.plot(x_positions, 20 * np.log10(spectrum + 1e-10), label=self.tr('Raw FR'))
        ax.plot(x_positions, 20 * np.log10(smoothed_spectrum + 1e-10), label=self.tr('Smoothed FR'), linewidth=2)
        ax.plot(x_positions, 20 * np.log10(filtered_spectrum + 1e-10), label=self.tr('Filtered FR'), linewidth=2)
        ax.set_title(self.tr("overall_fr"))
        ax.set_xlabel(self.tr("Frequency (Hz)"))
        ax.set_ylabel(self.tr("Amplitude (dB)"))
        ax.grid(True, which='both', ls='--', lw=0.5)
        ax.legend()

        # Устанавливаем метки оси X в соответствии с частотами
        positions = np.arange(len(freq_ticks))
        ax.set_xticks(positions)
        ax.set_xticklabels([str(int(f)) for f in freq_ticks])

        # Устанавливаем пределы по оси X
        ax.set_xlim(positions[0], positions[-1])

        # Автоматическая настройка оси амплитуды
        all_data_dB = 20 * np.log10(np.concatenate([spectrum, smoothed_spectrum, filtered_spectrum]) + 1e-10)
        y_min = np.nanmin(all_data_dB)
        y_max = np.nanmax(all_data_dB)
        y_margin = (y_max - y_min) * 0.1  # 10% запас
        ax.set_ylim(y_min - y_margin, y_max + y_margin)

        canvas.draw()

        fr_window.show()
        self.overall_fr_window = fr_window  # Сохранение ссылки на окно

    def close_temporary_fr_window(self, channel):
        """Закрывает временное окно АЧХ канала"""
        if channel in self.channel_fr_windows:
            self.channel_fr_windows[channel].close()
            del self.channel_fr_windows[channel]

    def update_recommendations(self):
        """Обновляет рекомендации для всех протестированных каналов"""
        # Получение допустимой погрешности
        error_margin = self.error_margin_spinbox.value()

        # Поиск канала сабвуфера
        subwoofer_channel = None
        for ch_index, name in self.channel_mapping.items():
            if self.tr('subwoofer').lower() in name.lower():
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
            self.test_channel(i, from_autotest=True)

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        self.save_settings()
        event.accept()

def main():
    app = QtWidgets.QApplication(sys.argv)
    tester = WhiteNoiseTester()
    tester.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
