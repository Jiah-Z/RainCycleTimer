import sys
import os
import time
import json
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QSystemTrayIcon, QMenu,
                             QFileDialog, QLabel, QInputDialog,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QByteArray
from PyQt5.QtGui import QPixmap, QImage, QIcon
import pygame.mixer
import keyboard

import ClockData
import Project
from Project import Interval

from localization import localization, SUPPORTED_LANGUAGES

Language = ""

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

CONFIG_FILE = "config.json"

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
tick_sound = pygame.mixer.Sound(resource_path("./resources/tick.wav"))
tock_sound = pygame.mixer.Sound(resource_path("./resources/tock.wav"))
swoosh_sound = pygame.mixer.Sound(resource_path("./resources/Pre.wav"))
boom_sound = pygame.mixer.Sound(resource_path("./resources/Hit.wav"))


class ClockWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.current_size = int(ClockData.CANVAS_SIZE * Project.SCALE)
        self.setFixedSize(self.current_size, self.current_size)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.current_size, self.current_size)
        self.label.setScaledContents(True)
        self.label.setStyleSheet("QLabel { image-rendering: pixelated; }")

        self.hide()
        self.drag_position = None
        self.main_controller = None

    def set_controller(self, controller):
        self.main_controller = controller

    def update_image(self, image_data: bytes):
        qimg = QImage.fromData(QByteArray(image_data))
        if not qimg.isNull():
            pixmap = QPixmap.fromImage(qimg)
            pixmap = pixmap.scaled(self.current_size, self.current_size,
                                   Qt.KeepAspectRatio, Qt.FastTransformation)
            self.label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            if self.main_controller:
                self.show_context_menu(event.globalPos())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.main_controller:
            self.main_controller.toggle_show()
            event.accept()

    def set_scale(self, new_scale):
        Project.SCALE = max(0.5, min(3.0, new_scale))
        new_size = int(ClockData.CANVAS_SIZE * Project.SCALE)
        self.current_size = new_size
        self.setFixedSize(new_size, new_size)
        self.label.setGeometry(0, 0, new_size, new_size)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        ctrl = self.main_controller

        action1 = menu.addAction(localization(Language, "Set Countdown (seconds)..."))
        action1.triggered.connect(ctrl.set_countdown)

        action2 = menu.addAction(localization(Language, "Load JSON..."))
        action2.triggered.connect(ctrl.load_file)

        action3 = menu.addAction(localization(Language, "Set Karma Level (1-10)..."))
        action3.triggered.connect(ctrl.set_karma_level)

        zoom_menu = menu.addMenu(localization(Language, "Zoom"))
        zoom_in = zoom_menu.addAction(localization(Language, "Zoom In (+0.2)"))
        zoom_in.triggered.connect(lambda: ctrl.zoom_change(0.2))
        zoom_out = zoom_menu.addAction(localization(Language, "Zoom Out (-0.2)"))
        zoom_out.triggered.connect(lambda: ctrl.zoom_change(-0.2))
        reset_zoom = zoom_menu.addAction(localization(Language, "Reset Zoom (1.0)"))
        reset_zoom.triggered.connect(lambda: ctrl.zoom_change(1.0, absolute=True))

        settings_menu = menu.addMenu(localization(Language, "Settings"))
        Lang = settings_menu.addAction(localization(Language, "Set Language..."))
        Lang.triggered.connect(ctrl.set_Language)
        hotkey_action = settings_menu.addAction(localization(Language, "Set Show Hotkey..."))
        hotkey_action.triggered.connect(ctrl.set_hotkey)
        quit_hotkey_action = settings_menu.addAction(localization(Language, "Set Quit Hotkey..."))
        quit_hotkey_action.triggered.connect(ctrl.set_quit_hotkey)
        settings_menu.addSeparator()

        sound_action = settings_menu.addAction(f"{localization(Language, 'Sound:')} {localization(Language, 'ON') if ctrl.sound_enabled else localization(Language, 'OFF')}")
        sound_action.triggered.connect(ctrl.toggle_sound)

        top_status = localization(Language, "ON") if ctrl.always_on_top else localization(Language, "OFF")
        action_top = menu.addAction(f"{localization(Language, 'Toggle Always on Top')} ({top_status})")
        action_top.triggered.connect(ctrl.toggle_always_on_top)

        menu.addSeparator()
        action_hide = menu.addAction(localization(Language, "Toggle Show/Hide"))
        action_hide.triggered.connect(ctrl.toggle_show)
        action_quit = menu.addAction(localization(Language, "Quit"))
        action_quit.triggered.connect(ctrl.quit_app)

        menu.exec_(pos)


class RainWorldClock:
    def __init__(self, app):
        self.app = app
        self.window = ClockWindow()
        self.window.set_controller(self)

        self.load_config()
        self.window.set_scale(self.scale)

        self.start_time = time.time()
        self.interval_start = self.start_time
        self.last_frame = self.start_time
        self.fading_power = 0.0
        self.current_interval = Interval()
        if self.saved_karma_symbol != 0:
            self.current_interval.karmaSymbol = self.saved_karma_symbol
            self.current_interval.maxKarma = self.saved_max_karma
        self.intervals = []
        self.fn_down = False
        self.gonna_quit = False
        self.is_tick = True
        self.last_tick = 0
        self.prepared = False
        self.always_on_top = True

        self.wave_start_time = 0.0
        self.wave_active = False

        self.tray = QSystemTrayIcon(self.app)
        icon_path = resource_path("./resources/icon.ico")
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = QIcon()
        self.tray.setIcon(icon)
        self.tray.setToolTip("Rain Cycle Timer")

        tray_menu = QMenu()
        t1 = tray_menu.addAction(localization(Language, "Set Countdown (seconds)..."))
        t1.triggered.connect(self.set_countdown)
        t2 = tray_menu.addAction(localization(Language, "Load JSON..."))
        t2.triggered.connect(self.load_file)
        t3 = tray_menu.addAction(localization(Language, "Set Karma Level (1-10)..."))
        t3.triggered.connect(self.set_karma_level)

        tray_zoom = tray_menu.addMenu(localization(Language, "Zoom"))
        tray_zoom_in = tray_zoom.addAction(localization(Language, "Zoom In (+0.2)"))
        tray_zoom_in.triggered.connect(lambda: self.zoom_change(0.2))
        tray_zoom_out = tray_zoom.addAction(localization(Language, "Zoom Out (-0.2)"))
        tray_zoom_out.triggered.connect(lambda: self.zoom_change(-0.2))
        tray_reset = tray_zoom.addAction(localization(Language, "Reset Zoom (1.0)"))
        tray_reset.triggered.connect(lambda: self.zoom_change(1.0, absolute=True))

        tray_settings = tray_menu.addMenu(localization(Language, "Settings"))
        Lang = tray_settings.addAction(localization(Language, "Set Language..."))
        Lang.triggered.connect(self.set_Language)
        hk = tray_settings.addAction(localization(Language, "Set Show Hotkey..."))
        hk.triggered.connect(self.set_hotkey)
        qhk = tray_settings.addAction(localization(Language, "Set Quit Hotkey..."))
        qhk.triggered.connect(self.set_quit_hotkey)
        tray_settings.addSeparator()

        tray_sound = tray_settings.addAction(f"{localization(Language, 'Sound:')} {localization(Language, 'ON') if self.sound_enabled else localization(Language, 'OFF')}")
        tray_sound.triggered.connect(self.toggle_sound)

        top_status = localization(Language, "ON") if self.always_on_top else localization(Language, "OFF")
        t4 = tray_menu.addAction(f"{localization(Language, 'Toggle Always on Top')} ({top_status})")
        t4.triggered.connect(self.toggle_always_on_top)
        tray_menu.addSeparator()
        t5 = tray_menu.addAction(localization(Language, "Toggle Show/Hide"))
        t5.triggered.connect(self.toggle_show)
        t6 = tray_menu.addAction(localization(Language, "Quit"))
        t6.triggered.connect(self.quit_app)
        self.tray.setContextMenu(tray_menu)
        self.tray.show()
        self.tray.activated.connect(self.on_tray_click)

        self.timer = QTimer()
        self.timer.timeout.connect(self.logic)
        self.timer.start(1000 // 60)

        self.register_hotkey()
        self.register_quit_hotkey()

        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.window.width() - Project.POSITION[0]
        y = screen.height() - self.window.height() - Project.POSITION[1]
        self.window.move(x, y)

        self.fn_down = True

    def load_config(self):
        global Language
        default = {
            "Language": "en-us",
            "hotkey": "ctrl+shift+f",
            "quit_hotkey": "ctrl+shift+q",
            "sound_enabled": True,
            "scale": 1.0,
            "karma_symbol": 0,
            "max_karma": 5
        }
        Language = default["Language"]
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    Language = data.get("Language", default["Language"])
                    self.hotkey = data.get("hotkey", default["hotkey"])
                    self.quit_hotkey = data.get("quit_hotkey", default["quit_hotkey"])
                    self.sound_enabled = data.get("sound_enabled", default["sound_enabled"])
                    self.scale = data.get("scale", default["scale"])
                    self.saved_karma_symbol = data.get("karma_symbol", default["karma_symbol"])
                    self.saved_max_karma = data.get("max_karma", default["max_karma"])
                    self.intervals = data.get("intervals", [])
                    Project.INTERVALS = self.intervals
                    # 【修复】读取 ticktock 并应用到 Project.settings
                    ticktock = data.get("ticktock", 3.2)
                    Project.settings["ticktock"] = ticktock
                    wave_params = data.get("wave_params", {})
                    Project.WAVE_PARAMS = wave_params
            except:
                self.hotkey = default["hotkey"]
                self.quit_hotkey = default["quit_hotkey"]
                self.sound_enabled = default["sound_enabled"]
                self.scale = default["scale"]
                self.saved_karma_symbol = default["karma_symbol"]
                self.saved_max_karma = default["max_karma"]
                self.intervals = []
                Project.INTERVALS = []
                Project.WAVE_PARAMS = {}
                Project.settings["ticktock"] = 3.2
        else:
            self.hotkey = default["hotkey"]
            self.quit_hotkey = default["quit_hotkey"]
            self.sound_enabled = default["sound_enabled"]
            self.scale = default["scale"]
            self.saved_karma_symbol = default["karma_symbol"]
            self.saved_max_karma = default["max_karma"]
            self.intervals = []
            Project.INTERVALS = []
            Project.WAVE_PARAMS = {}
            Project.settings["ticktock"] = 3.2

    def save_config(self):
        if self.current_interval and self.current_interval.karmaSymbol != 0:
            karma = self.current_interval.karmaSymbol
            maxk = self.current_interval.maxKarma
        else:
            karma = self.saved_karma_symbol
            maxk = self.saved_max_karma
        data = {
            "Language": Language,
            "hotkey": self.hotkey,
            "sound_enabled": self.sound_enabled,
            "scale": Project.SCALE,
            "karma_symbol": karma,
            "max_karma": maxk,
            "wave_params": getattr(Project, 'WAVE_PARAMS', {}),
            "intervals": getattr(Project, 'INTERVALS', {}),
            "ticktock": Project.settings.get("ticktock", 3.2),
            "quit_hotkey": self.quit_hotkey,
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.save_config()

    def register_hotkey(self):
        try:
            keyboard.remove_hotkey(self.hotkey)
        except:
            pass
        keyboard.add_hotkey(self.hotkey, self.toggle_show)

    def set_Language(self):
        global Language
        new_Language, ok = QInputDialog.getText(
            None, localization(Language, "Set Language"),
            localization(Language, "Enter the language you want to change to."),
            text=Language
        )
        if ok and new_Language.strip():
            new_Language = new_Language.strip().lower()
            if new_Language not in SUPPORTED_LANGUAGES:
                QMessageBox.critical(
                    None, localization(Language, "Error"),
                    f"{localization(Language, 'Unsupported language:')} {new_Language}\n"
                    f"{localization(Language, 'Available:')} {', '.join(SUPPORTED_LANGUAGES)}"
                )
                return
            Language = new_Language
            self.save_config()

    def set_hotkey(self):
        new_key, ok = QInputDialog.getText(
            None, localization(Language, "Set Show Hotkey"),
            localization(Language, "Enter new hotkey combination (e.g. 'ctrl+shift+f' or 'alt+x'):"),
            text=self.hotkey
        )
        if ok and new_key.strip():
            try:
                test_key = new_key.strip().lower()
                parts = test_key.split('+')
                mods = ['ctrl', 'shift', 'alt', 'win']
                non_mods = [p for p in parts if p not in mods]
                if not non_mods:
                    raise ValueError(localization(Language, "Need at least one non-modifier key"))
                try:
                    keyboard.remove_hotkey(self.hotkey)
                except:
                    pass
                self.hotkey = test_key
                keyboard.add_hotkey(self.hotkey, self.toggle_show)
                self.save_config()
                self.tray.showMessage(localization(Language, "Hotkey"), f"{localization(Language, 'Show hotkey set to')} {self.hotkey}", QSystemTrayIcon.Information, 1500)
            except Exception as e:
                QMessageBox.critical(None, localization(Language, "Error"), f"{localization(Language, 'Invalid hotkey:')} {e}\n{localization(Language, 'Please try again.')}")
                self.load_config()
                try:
                    keyboard.remove_hotkey(self.hotkey)
                except:
                    pass
                keyboard.add_hotkey(self.hotkey, self.toggle_show)

    def register_quit_hotkey(self):
        try:
            keyboard.remove_hotkey(self.quit_hotkey)
        except:
            pass
        keyboard.add_hotkey(self.quit_hotkey, self.quit_app)

    def set_quit_hotkey(self):
        new_key, ok = QInputDialog.getText(
            None, localization(Language, "Set Quit Hotkey"),
            localization(Language, "Enter new quit hotkey combination (e.g. 'ctrl+shift+q' or 'alt+q'):"),
            text=self.quit_hotkey
        )
        if ok and new_key.strip():
            try:
                test_key = new_key.strip().lower()
                parts = test_key.split('+')
                mods = ['ctrl', 'shift', 'alt', 'win']
                non_mods = [p for p in parts if p not in mods]
                if not non_mods:
                    raise ValueError(localization(Language, "Need at least one non-modifier key"))
                try:
                    keyboard.remove_hotkey(self.quit_hotkey)
                except:
                    pass
                self.quit_hotkey = test_key
                keyboard.add_hotkey(self.quit_hotkey, self.quit_app)
                self.save_config()
                self.tray.showMessage(localization(Language, "Hotkey"), f"{localization(Language, 'Quit hotkey set to')} {self.quit_hotkey}", QSystemTrayIcon.Information, 1500)
            except Exception as e:
                QMessageBox.critical(None, localization(Language, "Error"), f"{localization(Language, 'Invalid quit hotkey:')} {e}\n{localization(Language, 'Please try again.')}")
                self.load_config()
                try:
                    keyboard.remove_hotkey(self.quit_hotkey)
                except:
                    pass
                keyboard.add_hotkey(self.quit_hotkey, self.quit_app)

    def zoom_change(self, delta, absolute=False):
        if absolute:
            new_scale = delta
        else:
            new_scale = Project.SCALE + delta
        self.window.set_scale(new_scale)
        self.save_config()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_show()

    def toggle_show(self):
        self.fn_down = not self.fn_down

    def set_karma_level(self):
        current = self.current_interval.karmaSymbol or 1
        level, ok = QInputDialog.getInt(
            None, localization(Language, "Set Karma Level"),
            localization(Language, "Enter Karma level (1-10):\n(6-10 auto-set maxKarma=10)"),
            value=current, min=1, max=10, step=1
        )
        if ok:
            self.current_interval.karmaSymbol = level
            self.current_interval.maxKarma = 10 if level > 5 else 5
            # 同步更新缓存，确保新建倒计时使用新等级
            self.saved_karma_symbol = self.current_interval.karmaSymbol
            self.saved_max_karma = self.current_interval.maxKarma
            self.save_config()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        flags = self.window.windowFlags()
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        was_visible = self.window.isVisible()
        self.window.setWindowFlags(flags)
        if was_visible:
            self.window.show()
        self.tray.showMessage(localization(Language, "Always on Top"), f"{localization(Language, 'Set to')} {localization(Language, 'ON') if self.always_on_top else localization(Language, 'OFF')}", QSystemTrayIcon.Information, 1500)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, localization(Language, "Select JSON file"), "", localization(Language, "JSON files (*.json)")
        )
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                result = Project.loadData(data)
                if isinstance(result, str):
                    QMessageBox.critical(None, "Error", "Load error: " + result)
                    return
                self.intervals = result
                self.current_interval = Interval(totalTime=0)
                self.interval_start = time.time()
                self.last_tick = 0
            except Exception as e:
                QMessageBox.critical(None, "Error", "Load error: " + str(e))

    def set_countdown(self):
        seconds, ok = QInputDialog.getInt(
            None, localization(Language, "Set Countdown"), localization(Language, "Enter total seconds (e.g. 300 = 5min):"),
            value=600, min=1, max=86400, step=10
        )
        if ok:
            karma = self.saved_karma_symbol if self.saved_karma_symbol != 0 else 1
            max_karma = self.saved_max_karma if self.saved_karma_symbol != 0 else 5
            interval = Interval(
                totalPip=20,
                totalTime=seconds,
                karmaSymbol=karma,
                karmaReinforced=False,
                maxKarma=max_karma
            )
            self.intervals = [interval]
            self.current_interval = Interval(totalTime=0)
            self.interval_start = time.time()
            self.last_tick = 0
            self.fn_down = True

    def quit_app(self):
        self.gonna_quit = True
        if self.sound_enabled:
            swoosh_sound.play()
        QTimer.singleShot(1000, self.app.quit)

    def logic(self):
        current = time.time()

        if self.fading_power <= 0.01 and self.gonna_quit:
            self.app.quit()
            return

        if (not self.gonna_quit and
            current - self.interval_start + 0.02 > self.current_interval.totalTime):
            if self.sound_enabled:
                boom_sound.play()
            self.wave_start_time = current
            self.wave_active = True

            self.interval_start = current
            self.last_tick = 0
            if self.intervals:
                self.current_interval = self.intervals.pop(0)
            else:
                self.current_interval = Interval()
                if self.saved_karma_symbol != 0:
                    self.current_interval.karmaSymbol = self.saved_karma_symbol
                    self.current_interval.maxKarma = self.saved_max_karma

        wave_time = 0.0
        if self.wave_active:
            wave_time = current - self.wave_start_time
            wave_duration = getattr(Project, 'WAVE_PARAMS', {}).get("wave_duration", 3.0)
            if wave_time > wave_duration:
                self.wave_active = False
                wave_time = 0.0

        halftime = self.current_interval.totalTime / 2
        in_halftime = (halftime > 10 and
                       halftime - 0.75 <= current - self.interval_start <= halftime + 1.55)
        endtime = (self.current_interval.totalTime * (1 - 1/self.current_interval.totalPip)
                   if self.current_interval.totalPip > 0 else float("inf"))
        in_endtime = (endtime - 2.15 <= current - self.interval_start <=
                      min(endtime + 1.2, self.current_interval.totalTime - 0.65))
        should_display = (not self.gonna_quit and
                          (self.fn_down or in_halftime or in_endtime or
                           current - self.start_time <= 2))

        tick_interval = Project.settings["ticktock"]
        if tick_interval > 0:
            elapsed = current - self.interval_start
            if (elapsed >= (self.last_tick + 0.5) * tick_interval and
                    not self.prepared):
                if self.sound_enabled:
                    threading.Thread(target=lambda: self.play_sound(self.is_tick, stop=True)).start()
                self.prepared = True
            if elapsed >= (self.last_tick + 1) * tick_interval:
                if (self.fading_power >= 0.99 and
                    not in_halftime and not in_endtime and
                    self.current_interval.totalPip > 0 and
                    elapsed <= endtime):
                    if self.sound_enabled:
                        threading.Thread(target=lambda: self.play_sound(self.is_tick, stop=False)).start()
                    self.is_tick = not self.is_tick
                    self.prepared = False
                self.last_tick = max(self.last_tick + 1,
                                     int(elapsed // tick_interval))

        dt = min(current - self.last_frame, 1/20)
        if should_display:
            self.fading_power += dt
            self.fading_power = min(self.fading_power, 1)
        else:
            self.fading_power -= dt / 0.7
            self.fading_power = max(self.fading_power, 0)

        if should_display:
            fade_param = self.fading_power
        else:
            fade_param = (self.fading_power - 1) * 0.7

        clock = ClockData.computeClock(
            self.current_interval.totalTime,
            current - self.interval_start,
            self.current_interval.totalPip,
            self.current_interval.karmaSymbol,
            self.current_interval.karmaReinforced,
            self.current_interval.maxKarma,
            fade_param,
            wave_time
        )

        if clock.alpha > 0:
            img_data = clock.render()
            self.window.update_image(img_data)
            self.window.setWindowOpacity(clock.alpha)
            if not self.window.isVisible():
                self.window.show()
        else:
            if self.window.isVisible():
                self.window.hide()

        self.last_frame = current

    @staticmethod
    def play_sound(is_tick, stop=False):
        sound = tick_sound if is_tick else tock_sound
        if stop:
            sound.set_volume(0.0)
            sound.play()
            pygame.mixer.stop()
        else:
            sound.set_volume(1.0)
            sound.play()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    clock_app = RainWorldClock(app)
    sys.exit(app.exec_())