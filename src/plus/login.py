#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# login.py
#
# Copyright (c) 2018, Paul Holleis, Marko Luther
# All rights reserved.
# 
# 
# ABOUT
# This module connects to the artisan.plus inventory management service

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later versison. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from PyQt5.QtWidgets import QApplication,QDialog,QCheckBox,QGroupBox,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QPushButton
from PyQt5.QtCore import Qt

from plus import config

class Login(QDialog):
    def __init__(self, parent=None,email=None,remember_credentials=True):
        super(Login, self).__init__(parent)
        
        self.login = None
        self.passwd = None
        self.remember = remember_credentials
        
        self.linkRegister = QLabel('<small><a href="' + config.register_url + '">' + QApplication.translate("Plus","Register",None) + '</a></small>')
        self.linkRegister.setOpenExternalLinks(True)
        self.linkResetPassword = QLabel('<small><a href="' + config.reset_passwd_url + '">' + QApplication.translate("Plus","Reset Password",None) + '</a></small>')
        self.linkResetPassword.setOpenExternalLinks(True)
        
        self.textName = QLineEdit(self)
        self.textName.setPlaceholderText(QApplication.translate("Plus","Email",None))
        if email is not None:
            self.textName.setText(email)
        self.textName.textChanged.connect(self.textChanged)
        self.textPass = QLineEdit(self)
        self.textPass.setEchoMode(QLineEdit.Password)
        self.textPass.setPlaceholderText(QApplication.translate("Plus","Password",None))
        self.textPass.textChanged.connect(self.textChanged)
                
        self.rememberCheckbox = QCheckBox(QApplication.translate("Plus","Remember", None))
        self.rememberCheckbox.setChecked(self.remember)
        self.rememberCheckbox.stateChanged.connect(self.rememberCheckChanged)
        
        self.buttonCancel = QPushButton(QApplication.translate("Button","Cancel",None), self)
        self.buttonCancel.clicked.connect(lambda _:self.reject())
        self.buttonLogin = QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.setCredentials)
        self.buttonLogin.setEnabled(False)
                
        credentialsLayout = QVBoxLayout(self)
        credentialsLayout.addWidget(self.textName)
        credentialsLayout.addWidget(self.textPass)
        credentialsLayout.addWidget(self.rememberCheckbox)
        
        credentialsGroup = QGroupBox()
        credentialsGroup.setLayout(credentialsLayout)
        
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.buttonCancel)
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.buttonLogin)
        
        linkLayout = QHBoxLayout()
        linkLayout.addStretch()
        linkLayout.addWidget(self.linkRegister)
        linkLayout.addStretch()
        linkLayout.addWidget(self.linkResetPassword)
        linkLayout.addStretch()
        
        layout = QVBoxLayout(self)
        layout.addWidget(credentialsGroup)
        layout.addLayout(linkLayout)
        layout.addLayout(buttonLayout)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
    def rememberCheckChanged(self,s):
        self.remember = bool(s)
        
    def textChanged(self,_):
        login = self.textName.text()
        passwd = self.textPass.text()
        # TODO: activate valid credential condition
        if len(passwd) >= config.min_passwd_len and len(login) >= config.min_login_len and "@" in login and "." in login:
            self.buttonLogin.setEnabled(True)
            self.buttonLogin.setDefault(True)
        else:
            self.buttonLogin.setEnabled(False)
            self.buttonCancel.setDefault(True)

    def setCredentials(self):
        self.login = self.textName.text()
        self.passwd = self.textPass.text()
        self.accept()

def plus_login(window,email=None,remember_credentials=True):
    l = Login(window,email,remember_credentials)
    l.setWindowFlags(Qt.Sheet)
    l.setAttribute(Qt.WA_DeleteOnClose, True)
    l.exec_()
    return l.login,l.passwd,l.remember
