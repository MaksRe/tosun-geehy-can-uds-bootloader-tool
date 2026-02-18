# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'bootloader_tab_ui.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QToolButton,
    QVBoxLayout, QWidget)
import feather_rc

class Ui_BootloaderTabWidget(object):
    def setupUi(self, BootloaderTabWidget):
        if not BootloaderTabWidget.objectName():
            BootloaderTabWidget.setObjectName(u"BootloaderTabWidget")
        BootloaderTabWidget.resize(618, 433)
        self.gridLayout = QGridLayout(BootloaderTabWidget)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(1, 1, 1, 1)
        self.frame_4 = QFrame(BootloaderTabWidget)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.frame_4)
        self.gridLayout_3.setSpacing(2)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setContentsMargins(1, 1, 1, 1)
        self.btn_upload = QPushButton(self.frame_4)
        self.btn_upload.setObjectName(u"btn_upload")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_upload.sizePolicy().hasHeightForWidth())
        self.btn_upload.setSizePolicy(sizePolicy)
        self.btn_upload.setToolTipDuration(2000)
        icon = QIcon()
        icon.addFile(u":/icons/feather/upload.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_upload.setIcon(icon)

        self.gridLayout_3.addWidget(self.btn_upload, 0, 2, 1, 1)

        self.tool_btn_reset = QToolButton(self.frame_4)
        self.tool_btn_reset.setObjectName(u"tool_btn_reset")
        icon1 = QIcon()
        icon1.addFile(u":/icons/feather/refresh-cw.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.tool_btn_reset.setIcon(icon1)
        self.tool_btn_reset.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.tool_btn_reset.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonFollowStyle)
        self.tool_btn_reset.setArrowType(Qt.ArrowType.NoArrow)

        self.gridLayout_3.addWidget(self.tool_btn_reset, 0, 3, 1, 1)

        self.btn_clear = QPushButton(self.frame_4)
        self.btn_clear.setObjectName(u"btn_clear")
        icon2 = QIcon()
        icon2.addFile(u":/icons/feather/trash-2.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_clear.setIcon(icon2)

        self.gridLayout_3.addWidget(self.btn_clear, 0, 6, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.horizontalSpacer, 0, 5, 1, 1)

        self.btn_check_state = QPushButton(self.frame_4)
        self.btn_check_state.setObjectName(u"btn_check_state")
        self.btn_check_state.setMaximumSize(QSize(30, 16777215))
        self.btn_check_state.setToolTipDuration(2000)
        icon3 = QIcon()
        icon3.addFile(u":/icons/feather/info.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.btn_check_state.setIcon(icon3)

        self.gridLayout_3.addWidget(self.btn_check_state, 0, 4, 1, 1)


        self.gridLayout.addWidget(self.frame_4, 2, 0, 1, 1)

        self.frame_3 = QFrame(BootloaderTabWidget)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_3)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(1, 1, 1, 2)
        self.list_process = QListWidget(self.frame_3)
        self.list_process.setObjectName(u"list_process")

        self.horizontalLayout.addWidget(self.list_process)


        self.gridLayout.addWidget(self.frame_3, 4, 0, 1, 1)

        self.frame_2 = QFrame(BootloaderTabWidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(1, 1, 1, 2)
        self.progress_loading = QProgressBar(self.frame_2)
        self.progress_loading.setObjectName(u"progress_loading")
        self.progress_loading.setValue(0)
        self.progress_loading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_loading.setTextVisible(True)
        self.progress_loading.setOrientation(Qt.Orientation.Horizontal)
        self.progress_loading.setTextDirection(QProgressBar.Direction.TopToBottom)

        self.verticalLayout.addWidget(self.progress_loading)


        self.gridLayout.addWidget(self.frame_2, 6, 0, 1, 1)

        self.frame = QFrame(BootloaderTabWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setSpacing(2)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(1, 1, 1, 1)
        self.line_path_to_file = QLineEdit(self.frame)
        self.line_path_to_file.setObjectName(u"line_path_to_file")
        self.line_path_to_file.setReadOnly(True)

        self.gridLayout_2.addWidget(self.line_path_to_file, 0, 1, 1, 2)

        self.btn_open_file = QPushButton(self.frame)
        self.btn_open_file.setObjectName(u"btn_open_file")
        self.btn_open_file.setMinimumSize(QSize(0, 0))
        self.btn_open_file.setMaximumSize(QSize(40, 16777215))
        self.btn_open_file.setAutoFillBackground(False)

        self.gridLayout_2.addWidget(self.btn_open_file, 0, 3, 1, 1)


        self.gridLayout.addWidget(self.frame, 1, 0, 1, 1)


        self.retranslateUi(BootloaderTabWidget)

        QMetaObject.connectSlotsByName(BootloaderTabWidget)
    # setupUi

    def retranslateUi(self, BootloaderTabWidget):
        BootloaderTabWidget.setWindowTitle(QCoreApplication.translate("BootloaderTabWidget", u"Form", None))
#if QT_CONFIG(tooltip)
        self.btn_upload.setToolTip(QCoreApplication.translate("BootloaderTabWidget", u"Загрузка", None))
#endif // QT_CONFIG(tooltip)
        self.btn_upload.setText("")
        self.tool_btn_reset.setText(QCoreApplication.translate("BootloaderTabWidget", u"Тип сброса", None))
        self.btn_clear.setText("")
#if QT_CONFIG(tooltip)
        self.btn_check_state.setToolTip(QCoreApplication.translate("BootloaderTabWidget", u"Статус", None))
#endif // QT_CONFIG(tooltip)
        self.btn_check_state.setText("")
        self.btn_open_file.setText(QCoreApplication.translate("BootloaderTabWidget", u"...", None))
    # retranslateUi

