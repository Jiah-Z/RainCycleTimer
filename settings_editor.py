import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QDoubleSpinBox, QCheckBox, QFileDialog,
                             QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from localization import localization

# ---- 资源路径辅助函数 ----
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

CONFIG_FILE = "config.json"

class SettingsEditor(QWidget):
    def __init__(self):
        self.load_config()

        super().__init__()
        self.setWindowTitle(localization(self.config["Language"], "Rain Cycle Timer - Settings Editor"))
        self.setMinimumSize(600, 500)

        # 尝试加载窗口图标（如果 icon.ico 存在则显示）
        icon_path = resource_path("./resources/icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.init_ui()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = {}
        else:
            self.config = {}

        default_wave = {
            "wave_duration": 3.0,
            "shrink_amount": 0.05,
            "shrink_dur": 0.06,
            "recover_dur": 0.06,
            "max_radius_ratio": 0.8
        }
        self.wave_params = self.config.get("wave_params", default_wave)
        self.intervals = self.config.get("intervals", [])
        self.Language = self.config.get("Language", "en-us")
        self.config["Language"] = self.Language
        self.hotkey = self.config.get("hotkey", "ctrl+shift+f")
        self.quit_hotkey = self.config.get("quit_hotkey", "ctrl+shift+q")
        self.sound_enabled = self.config.get("sound_enabled", True)
        self.scale = self.config.get("scale", 1.0)
        self.ticktock = self.config.get("ticktock", 3.2)

    def save_config(self):
        self.collect_table_data()
        self.Language = self.Language_edit.text()
        self.hotkey = self.hotkey_edit.text()
        self.quit_hotkey = self.quit_hotkey_edit.text()
        self.scale = self.scale_spin.value()
        self.sound_enabled = self.sound_check.isChecked()
        self.ticktock = self.ticktock_spin.value()
        self.wave_params = {
            "wave_duration": self.wave_duration.value(),
            "shrink_amount": self.shrink_amount.value(),
            "shrink_dur": self.shrink_dur.value(),
            "recover_dur": self.recover_dur.value(),
            "max_radius_ratio": self.max_radius_ratio.value()
        }

        self.config["wave_params"] = self.wave_params
        self.config["intervals"] = self.intervals
        self.config["Language"] = self.Language
        self.config["hotkey"] = self.hotkey
        self.config["quit_hotkey"] = self.quit_hotkey
        self.config["sound_enabled"] = self.sound_enabled
        self.config["scale"] = self.scale
        self.config["ticktock"] = self.ticktock
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, localization(self.config["Language"], "Error"), f"{localization(self.config['Language'], 'Failed to save:')} {e}")
            return False

    def init_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        tabs.addTab(self.create_wave_tab(), localization(self.config["Language"], "Wave & Vibration"))
        tabs.addTab(self.create_intervals_tab(), localization(self.config["Language"], "Intervals"))
        tabs.addTab(self.create_general_tab(), localization(self.config["Language"], "General"))
        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton(localization(self.config["Language"], "Save to config.json"))
        save_btn.clicked.connect(self.save_and_show)
        export_btn = QPushButton(localization(self.config["Language"], "Export as JSON file..."))
        export_btn.clicked.connect(self.export_json)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def save_and_show(self):
        if self.save_config():
            QMessageBox.information(self, localization(self.config["Language"], "Saved"), localization(self.config["Language"], "Configuration saved successfully."))

    def closeEvent(self, event):
        if self.save_config():
            event.accept()
        else:
            reply = QMessageBox.question(self, localization(self.config["Language"], "Save Failed"),
                                         localization(self.config["Language"], "Failed to save configuration. Close anyway?"),
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    # ---------- Wave Tab ----------
    def create_wave_tab(self):
        widget = QWidget()
        layout = QFormLayout()

        self.wave_duration = QDoubleSpinBox()
        self.wave_duration.setRange(0.5, 10.0)
        self.wave_duration.setSingleStep(0.1)
        self.wave_duration.setValue(self.wave_params.get("wave_duration", 3.0))
        self.wave_duration.setToolTip(localization(self.config["Language"], "Total duration of wave in seconds"))
        layout.addRow(localization(self.config["Language"], "Wave Duration (s):"), self.wave_duration)

        self.shrink_amount = QDoubleSpinBox()
        self.shrink_amount.setRange(0.01, 0.3)
        self.shrink_amount.setSingleStep(0.01)
        self.shrink_amount.setValue(self.wave_params.get("shrink_amount", 0.05))
        self.shrink_amount.setToolTip(localization(self.config["Language"], "Shrink amount (0.05 = scale to 0.95)"))
        layout.addRow(localization(self.config["Language"], "Shrink Amount:"), self.shrink_amount)

        self.shrink_dur = QDoubleSpinBox()
        self.shrink_dur.setRange(0.01, 0.5)
        self.shrink_dur.setSingleStep(0.01)
        self.shrink_dur.setValue(self.wave_params.get("shrink_dur", 0.06))
        self.shrink_dur.setToolTip(localization(self.config["Language"], "Shrink duration ratio of total wave time"))
        layout.addRow(localization(self.config["Language"], "Shrink Duration Ratio:"), self.shrink_dur)

        self.recover_dur = QDoubleSpinBox()
        self.recover_dur.setRange(0.01, 0.5)
        self.recover_dur.setSingleStep(0.01)
        self.recover_dur.setValue(self.wave_params.get("recover_dur", 0.06))
        self.recover_dur.setToolTip(localization(self.config["Language"], "Recover duration ratio of total wave time"))
        layout.addRow(localization(self.config["Language"], "Recover Duration Ratio:"), self.recover_dur)

        self.max_radius_ratio = QDoubleSpinBox()
        self.max_radius_ratio.setRange(0.1, 1.5)
        self.max_radius_ratio.setSingleStep(0.05)
        self.max_radius_ratio.setValue(self.wave_params.get("max_radius_ratio", 0.8))
        self.max_radius_ratio.setToolTip(localization(self.config["Language"], "Max wave radius ratio (clamped to 0.75 to avoid edge clipping)"))
        layout.addRow(localization(self.config["Language"], "Max Radius Ratio:"), self.max_radius_ratio)

        self.info_label = QLabel()
        self.update_info()
        self.wave_duration.valueChanged.connect(self.update_info)
        self.shrink_dur.valueChanged.connect(self.update_info)
        self.recover_dur.valueChanged.connect(self.update_info)
        layout.addRow("", self.info_label)

        widget.setLayout(layout)
        return widget

    def update_info(self):
        dur = self.wave_duration.value()
        shrink = self.shrink_dur.value()
        recover = self.recover_dur.value()
        total_vib = shrink + recover
        wave_start = total_vib * dur
        info = f"{localization(self.config['Language'], 'Vibration total:')} {total_vib*100:.1f}%  ({total_vib*dur:.2f}s)   {localization(self.config['Language'], 'Wave starts at:')} {wave_start:.2f}s"
        self.info_label.setText(info)

    # ---------- Intervals Tab ----------
    def create_intervals_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([localization(self.config["Language"], "Pips"), localization(self.config["Language"], "Time(s)"), localization(self.config["Language"], "Karma"), localization(self.config["Language"], "Reinf."), localization(self.config["Language"], "MaxKarma")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.populate_table()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton(localization(self.config["Language"], "Add Row"))
        add_btn.clicked.connect(self.add_row)
        remove_btn = QPushButton(localization(self.config["Language"], "Remove Selected"))
        remove_btn.clicked.connect(self.remove_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)

        widget.setLayout(layout)
        return widget

    def populate_table(self):
        self.table.setRowCount(len(self.intervals))
        for row, interval in enumerate(self.intervals):
            self.table.setItem(row, 0, QTableWidgetItem(str(interval.get("totalPip", 20))))
            self.table.setItem(row, 1, QTableWidgetItem(str(interval.get("totalTime", 600))))
            self.table.setItem(row, 2, QTableWidgetItem(str(interval.get("karmaSymbol", 1))))
            reinforced = interval.get("karmaReinforced", False)
            self.table.setItem(row, 3, QTableWidgetItem("Yes" if reinforced else "No"))
            self.table.setItem(row, 4, QTableWidgetItem(str(interval.get("maxKarma", 5))))

    def add_row(self):
        self.intervals.append({
            "totalPip": 20,
            "totalTime": 600,
            "karmaSymbol": 1,
            "karmaReinforced": False,
            "maxKarma": 5
        })
        self.populate_table()

    def remove_row(self):
        selected = self.table.currentRow()
        if selected >= 0:
            self.intervals.pop(selected)
            self.populate_table()

    # ---------- General Tab ----------
    def create_general_tab(self):
        widget = QWidget()
        layout = QFormLayout()

        self.Language_edit = QLineEdit(self.Language)
        self.Language_edit.setToolTip(localization(self.config["Language"], "changes of Language made will be applied after this program restarting."))
        layout.addRow(localization(self.config["Language"], "Language:"), self.Language_edit)

        self.hotkey_edit = QLineEdit(self.hotkey)
        layout.addRow(localization(self.config["Language"], "Show Hotkey:"), self.hotkey_edit)

        self.quit_hotkey_edit = QLineEdit(self.quit_hotkey)
        layout.addRow(localization(self.config["Language"], "Quit Hotkey:"), self.quit_hotkey_edit)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.3, 5.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setValue(self.scale)
        layout.addRow(localization(self.config["Language"], "Zoom Scale:"), self.scale_spin)

        self.sound_check = QCheckBox()
        self.sound_check.setChecked(self.sound_enabled)
        layout.addRow(localization(self.config["Language"], "Sound Enabled:"), self.sound_check)

        self.ticktock_spin = QDoubleSpinBox()
        self.ticktock_spin.setRange(0.1, 999999999.0)
        self.ticktock_spin.setSingleStep(0.1)
        self.ticktock_spin.setValue(self.ticktock)
        self.ticktock_spin.setToolTip(localization(self.config["Language"], "Interval between tick and tock sounds (seconds)"))
        layout.addRow(localization(self.config["Language"], "Ticktock (s):"), self.ticktock_spin)

        widget.setLayout(layout)
        return widget

    # ---------- Export JSON ----------
    def export_json(self):
        self.collect_table_data()
        self.Language = self.Language_edit.text()
        self.hotkey = self.hotkey_edit.text()
        self.quit_hotkey = self.quit_hotkey_edit.text()
        self.scale = self.scale_spin.value()
        self.sound_enabled = self.sound_check.isChecked()
        self.ticktock = self.ticktock_spin.value()
        self.wave_params = {
            "wave_duration": self.wave_duration.value(),
            "shrink_amount": self.shrink_amount.value(),
            "shrink_dur": self.shrink_dur.value(),
            "recover_dur": self.recover_dur.value(),
            "max_radius_ratio": self.max_radius_ratio.value()
        }

        data = {
            "ticktock": self.ticktock,
            "intervals": self.intervals
        }
        file_path, _ = QFileDialog.getSaveFileName(
            self, localization(self.config["Language"], "Export JSON"), "", localization(self.config["Language"], "JSON files (*.json)")
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, localization(self.config["Language"], "Exported"), f"{localization(self.config['Language'], 'JSON exported to')} {file_path}")
            except Exception as e:
                QMessageBox.critical(self, localization(self.config["Language"], "Error"), f"{localization(self.config['Language'], 'Failed to export')}: {e}")

    def collect_table_data(self):
        self.intervals = []
        for row in range(self.table.rowCount()):
            try:
                item0 = self.table.item(row, 0)
                item1 = self.table.item(row, 1)
                item2 = self.table.item(row, 2)
                item3 = self.table.item(row, 3)
                item4 = self.table.item(row, 4)
                if item0 and item1 and item2 and item4:
                    interval = {
                        "totalPip": int(item0.text()),
                        "totalTime": float(item1.text()),
                        "karmaSymbol": int(item2.text()),
                        "karmaReinforced": item3.text() == "Yes",
                        "maxKarma": int(item4.text())
                    }
                    self.intervals.append(interval)
            except Exception as e:
                QMessageBox.warning(self, localization(self.config["Language"], "Data Error"), f"{localization(self.config['Language'], 'Row')} {row+1} {localization(self.config['Language'], 'has invalid data:')} {e}")
                return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsEditor()
    window.show()
    sys.exit(app.exec_())