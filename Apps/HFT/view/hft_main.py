# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'hft_main.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 450)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.centralWidget)
        self.horizontalLayout_4.setContentsMargins(11, 11, 11, 11)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.table_widget = QtWidgets.QTableWidget(self.centralWidget)
        self.table_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table_widget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table_widget.setShowGrid(True)
        self.table_widget.setRowCount(5)
        self.table_widget.setColumnCount(7)
        self.table_widget.setObjectName("table_widget")
        item = QtWidgets.QTableWidgetItem()
        self.table_widget.setVerticalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        item.setFont(font)
        self.table_widget.setHorizontalHeaderItem(6, item)
        self.table_widget.horizontalHeader().setVisible(True)
        self.table_widget.horizontalHeader().setSortIndicatorShown(True)
        self.table_widget.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.table_widget)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.centralWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.duration_label = QtWidgets.QLabel(self.centralWidget)
        self.duration_label.setObjectName("duration_label")
        self.horizontalLayout_2.addWidget(self.duration_label)
        self.label_2 = QtWidgets.QLabel(self.centralWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.profit_label = QtWidgets.QLabel(self.centralWidget)
        self.profit_label.setObjectName("profit_label")
        self.horizontalLayout_2.addWidget(self.profit_label)
        self.horizontalLayout_3.addLayout(self.horizontalLayout_2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.start_button = QtWidgets.QPushButton(self.centralWidget)
        self.start_button.setMinimumSize(QtCore.QSize(113, 32))
        self.start_button.setMaximumSize(QtCore.QSize(113, 32))
        self.start_button.setObjectName("start_button")
        self.horizontalLayout.addWidget(self.start_button)
        self.stop_button = QtWidgets.QPushButton(self.centralWidget)
        self.stop_button.setMinimumSize(QtCore.QSize(113, 32))
        self.stop_button.setMaximumSize(QtCore.QSize(113, 32))
        self.stop_button.setObjectName("stop_button")
        self.horizontalLayout.addWidget(self.stop_button)
        self.cancel_orders_button = QtWidgets.QPushButton(self.centralWidget)
        self.cancel_orders_button.setMinimumSize(QtCore.QSize(113, 32))
        self.cancel_orders_button.setMaximumSize(QtCore.QSize(113, 32))
        self.cancel_orders_button.setObjectName("cancel_orders_button")
        self.horizontalLayout.addWidget(self.cancel_orders_button)
        self.horizontalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralWidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "OKEx HFT Tool"))
        self.table_widget.setSortingEnabled(True)
        item = self.table_widget.verticalHeaderItem(0)
        item.setText(_translate("MainWindow", "新建行,1,1,1,1,1"))
        item = self.table_widget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Pair"))
        item = self.table_widget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Profit"))
        item = self.table_widget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "Profit(CNY)"))
        item = self.table_widget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "Side"))
        item = self.table_widget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "Count"))
        item = self.table_widget.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "Amount"))
        item = self.table_widget.horizontalHeaderItem(6)
        item.setText(_translate("MainWindow", "Total Amount"))
        self.label.setText(_translate("MainWindow", "Duration:"))
        self.duration_label.setText(_translate("MainWindow", "00:00:00"))
        self.label_2.setText(_translate("MainWindow", "Profit:"))
        self.profit_label.setText(_translate("MainWindow", "￥12345.87"))
        self.start_button.setText(_translate("MainWindow", "Start"))
        self.stop_button.setText(_translate("MainWindow", "Stop"))
        self.cancel_orders_button.setText(_translate("MainWindow", "Cancel Orders"))

