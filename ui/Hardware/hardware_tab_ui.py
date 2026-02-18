# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'hardware_tab_ui.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QGridLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
import feather_rc

class Ui_HardwareTabWidget(object):
    def setupUi(self, HardwareTabWidget):
        if not HardwareTabWidget.objectName():
            HardwareTabWidget.setObjectName(u"HardwareTabWidget")
        HardwareTabWidget.resize(875, 317)
        HardwareTabWidget.setStyleSheet(u"")
        self.gridLayout = QGridLayout(HardwareTabWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.frame_3 = QFrame(HardwareTabWidget)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setMinimumSize(QSize(0, 0))
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_4 = QGridLayout(self.frame_3)
        self.gridLayout_4.setSpacing(1)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout_4.setContentsMargins(1, 1, 1, 1)
        self.label_device_handle = QLabel(self.frame_3)
        self.label_device_handle.setObjectName(u"label_device_handle")

        self.gridLayout_4.addWidget(self.label_device_handle, 1, 4, 1, 1)

        self.label_serial = QLabel(self.frame_3)
        self.label_serial.setObjectName(u"label_serial")

        self.gridLayout_4.addWidget(self.label_serial, 1, 3, 1, 1)

        self.line_serial = QLineEdit(self.frame_3)
        self.line_serial.setObjectName(u"line_serial")
        self.line_serial.setReadOnly(True)

        self.gridLayout_4.addWidget(self.line_serial, 2, 3, 1, 1)

        self.label_manufacturer = QLabel(self.frame_3)
        self.label_manufacturer.setObjectName(u"label_manufacturer")

        self.gridLayout_4.addWidget(self.label_manufacturer, 1, 1, 1, 1)

        self.label_product = QLabel(self.frame_3)
        self.label_product.setObjectName(u"label_product")

        self.gridLayout_4.addWidget(self.label_product, 1, 2, 1, 1)

        self.line_device_handler = QLineEdit(self.frame_3)
        self.line_device_handler.setObjectName(u"line_device_handler")
        self.line_device_handler.setReadOnly(True)

        self.gridLayout_4.addWidget(self.line_device_handler, 2, 4, 1, 1)

        self.line_manufacturer = QLineEdit(self.frame_3)
        self.line_manufacturer.setObjectName(u"line_manufacturer")
        self.line_manufacturer.setReadOnly(True)

        self.gridLayout_4.addWidget(self.line_manufacturer, 2, 1, 1, 1)

        self.line_product = QLineEdit(self.frame_3)
        self.line_product.setObjectName(u"line_product")
        self.line_product.setReadOnly(True)

        self.gridLayout_4.addWidget(self.line_product, 2, 2, 1, 1)


        self.gridLayout.addWidget(self.frame_3, 1, 0, 1, 2)

        self.frame_4 = QFrame(HardwareTabWidget)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame_4)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.btn_connect = QPushButton(self.frame_4)
        self.btn_connect.setObjectName(u"btn_connect")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_connect.sizePolicy().hasHeightForWidth())
        self.btn_connect.setSizePolicy(sizePolicy)
        self.btn_connect.setToolTipDuration(5)
        icon = QIcon()
        icon.addFile(u":/icons/feather/arrow-right-circle.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_connect.setIcon(icon)
        self.btn_connect.setIconSize(QSize(16, 16))
        self.btn_connect.setCheckable(False)
        self.btn_connect.setAutoRepeat(False)
        self.btn_connect.setAutoExclusive(False)

        self.verticalLayout_2.addWidget(self.btn_connect)


        self.gridLayout.addWidget(self.frame_4, 1, 2, 1, 1, Qt.AlignmentFlag.AlignBottom)

        self.btn_scan_devices = QPushButton(HardwareTabWidget)
        self.btn_scan_devices.setObjectName(u"btn_scan_devices")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.btn_scan_devices.sizePolicy().hasHeightForWidth())
        self.btn_scan_devices.setSizePolicy(sizePolicy1)
        self.btn_scan_devices.setMinimumSize(QSize(160, 0))
        self.btn_scan_devices.setMaximumSize(QSize(100, 16777215))
        self.btn_scan_devices.setToolTipDuration(5)
        self.btn_scan_devices.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.btn_scan_devices.setAutoFillBackground(False)
        icon1 = QIcon()
        icon1.addFile(u":/icons/feather/search.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_scan_devices.setIcon(icon1)
        self.btn_scan_devices.setIconSize(QSize(16, 16))

        self.gridLayout.addWidget(self.btn_scan_devices, 0, 2, 1, 1)

        self.combo_box_devices = QComboBox(HardwareTabWidget)
        self.combo_box_devices.setObjectName(u"combo_box_devices")

        self.gridLayout.addWidget(self.combo_box_devices, 0, 0, 1, 2)

        self.frame_2 = QFrame(HardwareTabWidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_trace = QPushButton(self.frame_2)
        self.btn_trace.setObjectName(u"btn_trace")
        self.btn_trace.setToolTipDuration(5)
        icon2 = QIcon()
        icon2.addFile(u":/icons/feather/zap.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_trace.setIcon(icon2)
        self.btn_trace.setIconSize(QSize(16, 16))

        self.verticalLayout.addWidget(self.btn_trace)


        self.gridLayout.addWidget(self.frame_2, 2, 2, 1, 1, Qt.AlignmentFlag.AlignBottom)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 3, 0, 1, 1)

        self.frame = QFrame(HardwareTabWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setMinimumSize(QSize(0, 0))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setSpacing(1)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(1, 1, 1, 1)
        self.combo_box_channel = QComboBox(self.frame)
        self.combo_box_channel.addItem("")
        self.combo_box_channel.addItem("")
        self.combo_box_channel.addItem("")
        self.combo_box_channel.addItem("")
        self.combo_box_channel.setObjectName(u"combo_box_channel")

        self.gridLayout_2.addWidget(self.combo_box_channel, 2, 2, 1, 1)

        self.combo_box_baud_rate = QComboBox(self.frame)
        self.combo_box_baud_rate.addItem("")
        self.combo_box_baud_rate.addItem("")
        self.combo_box_baud_rate.addItem("")
        self.combo_box_baud_rate.addItem("")
        self.combo_box_baud_rate.setObjectName(u"combo_box_baud_rate")

        self.gridLayout_2.addWidget(self.combo_box_baud_rate, 3, 2, 1, 1)

        self.check_box_terminator = QCheckBox(self.frame)
        self.check_box_terminator.setObjectName(u"check_box_terminator")

        self.gridLayout_2.addWidget(self.check_box_terminator, 1, 2, 1, 1)

        self.label_baud_rate = QLabel(self.frame)
        self.label_baud_rate.setObjectName(u"label_baud_rate")

        self.gridLayout_2.addWidget(self.label_baud_rate, 3, 1, 1, 1)

        self.label_channel = QLabel(self.frame)
        self.label_channel.setObjectName(u"label_channel")
        self.label_channel.setMaximumSize(QSize(70, 16777215))

        self.gridLayout_2.addWidget(self.label_channel, 2, 1, 1, 1)


        self.gridLayout.addWidget(self.frame, 2, 0, 1, 2)


        self.retranslateUi(HardwareTabWidget)

        QMetaObject.connectSlotsByName(HardwareTabWidget)
    # setupUi

    def retranslateUi(self, HardwareTabWidget):
        HardwareTabWidget.setWindowTitle(QCoreApplication.translate("HardwareTabWidget", u"Form", None))
        self.label_device_handle.setText(QCoreApplication.translate("HardwareTabWidget", u"device handle", None))
        self.label_serial.setText(QCoreApplication.translate("HardwareTabWidget", u"serial", None))
        self.label_manufacturer.setText(QCoreApplication.translate("HardwareTabWidget", u"manufacturer", None))
        self.label_product.setText(QCoreApplication.translate("HardwareTabWidget", u"product", None))
#if QT_CONFIG(tooltip)
        self.btn_connect.setToolTip(QCoreApplication.translate("HardwareTabWidget", u"Подключиться к выбранному устройству", None))
#endif // QT_CONFIG(tooltip)
        self.btn_connect.setText(QCoreApplication.translate("HardwareTabWidget", u"Подключиться", None))
#if QT_CONFIG(shortcut)
        self.btn_connect.setShortcut("")
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(tooltip)
        self.btn_scan_devices.setToolTip(QCoreApplication.translate("HardwareTabWidget", u"Сканирование CAN-устройств", None))
#endif // QT_CONFIG(tooltip)
        self.btn_scan_devices.setText(QCoreApplication.translate("HardwareTabWidget", u"Поиск", None))
#if QT_CONFIG(tooltip)
        self.btn_trace.setToolTip(QCoreApplication.translate("HardwareTabWidget", u"Запустить отслеживание", None))
#endif // QT_CONFIG(tooltip)
        self.btn_trace.setText(QCoreApplication.translate("HardwareTabWidget", u"Применить настройки", None))
        self.combo_box_channel.setItemText(0, QCoreApplication.translate("HardwareTabWidget", u"1", None))
        self.combo_box_channel.setItemText(1, QCoreApplication.translate("HardwareTabWidget", u"2", None))
        self.combo_box_channel.setItemText(2, QCoreApplication.translate("HardwareTabWidget", u"3", None))
        self.combo_box_channel.setItemText(3, QCoreApplication.translate("HardwareTabWidget", u"4", None))

        self.combo_box_baud_rate.setItemText(0, QCoreApplication.translate("HardwareTabWidget", u"125", None))
        self.combo_box_baud_rate.setItemText(1, QCoreApplication.translate("HardwareTabWidget", u"250", None))
        self.combo_box_baud_rate.setItemText(2, QCoreApplication.translate("HardwareTabWidget", u"500", None))
        self.combo_box_baud_rate.setItemText(3, QCoreApplication.translate("HardwareTabWidget", u"1000", None))

        self.check_box_terminator.setText(QCoreApplication.translate("HardwareTabWidget", u"terminator", None))
        self.label_baud_rate.setText(QCoreApplication.translate("HardwareTabWidget", u"baud rate", None))
        self.label_channel.setText(QCoreApplication.translate("HardwareTabWidget", u"channel", None))
    # retranslateUi

