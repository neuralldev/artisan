#
# ABOUT
# Artisan serial, error and message logs

# LICENSE
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

# AUTHOR
# Marko Luther, 2023


from typing import Optional, TYPE_CHECKING, Final

if TYPE_CHECKING:
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from artisanlib.serialport import serialport # type: ignore # @UnusedImport # NOUVELLE IMPORTATION
    from PyQt6.QtWidgets import QWidget # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

from artisanlib import __version__

from artisanlib.dialogs import ArtisanDialog

try:
    from PyQt6.QtCore import pyqtSlot # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QLabel, QCheckBox, QTextEdit, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout) # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import pyqtSlot # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QLabel, QCheckBox, QTextEdit, QVBoxLayout) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport


##########################################################################
#####################  VIEW SERIAL LOG DLG  ##############################
##########################################################################

class serialLogDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Serial Log'))

        # Récupérer les paramètres du port série via self.aw.ser
        serial_params = self.aw.ser
        
        # Créer un message récapitulatif des paramètres
        summary_text = (
            f"<b>{QApplication.translate('Label', 'Serial port')} :</b> {serial_params.comport} | "
            f"<b>{QApplication.translate('Label', 'Baudrate')} :</b> {serial_params.baudrate} | "
            f"<b>{QApplication.translate('Label', 'Parity')} :</b> {serial_params.parity} | "
            f"<b>{QApplication.translate('Label', 'Stopbits')} :</b> {serial_params.stopbits}"
        )
        self.summaryLabel = QLabel(summary_text)
        self.summaryLabel.setWordWrap(True)

        self.serialcheckbox = QCheckBox(QApplication.translate('CheckBox','Serial Log ON/OFF'))
        self.serialcheckbox.setToolTip(QApplication.translate('Tooltip', 'ON/OFF logs serial communication'))
        self.serialcheckbox.setChecked(self.aw.seriallogflag)
        self.serialcheckbox.stateChanged.connect(self.serialcheckboxChanged)
        
        self.serialEdit = QTextEdit()
        self.serialEdit.setReadOnly(True)
        self.serialEdit.setHtml(self.getstring())

        self.messageInput = QLineEdit()
        self.messageInput.setPlaceholderText(QApplication.translate('Placeholder', "Enter a command to send..."))
        self.messageInput.textChanged.connect(self.updateHexInput)

        self.hexInput = QLineEdit()
        self.hexInput.setReadOnly(True) # Le champ est en lecture seule
    
        self.sendButton = QPushButton(QApplication.translate('Button', "Send"))
        self.sendButton.setToolTip(QApplication.translate('Tooltip', "Send a message to serial port"))
        self.sendButton.clicked.connect(self.sendMessage)


        input_layout = QHBoxLayout()
        input_layout.addWidget(self.messageInput)
        input_layout.addWidget(self.sendButton)

        hex_layout = QHBoxLayout()
        hex_label = QLabel(QApplication.translate('Label', "Hex : "))
        hex_layout.addWidget(hex_label)
        hex_layout.addWidget(self.hexInput)

        layout = QVBoxLayout()
        layout.addWidget(self.summaryLabel, 0)
        layout.addWidget(self.serialcheckbox, 0)
        layout.addWidget(self.serialEdit, 1)
        layout.addLayout(input_layout)
        layout.addLayout(hex_layout)
        self.setLayout(layout)

    @pyqtSlot(str)
    def updateHexInput(self, text: str) -> None:
        try:
            # Convertir le texte en hexadécimal.
            # L'encodage en UTF-8 est le plus commun pour les caractères.
            hex_string = text.encode('utf-8').hex().upper()
            
            # Formater la chaîne avec des espaces pour une meilleure lisibilité
            formatted_hex = ' '.join([hex_string[i:i+2] for i in range(0, len(hex_string), 2)])
            
            self.hexInput.setText(formatted_hex)
        except Exception:
            self.hexInput.setText("conversion error")

    @pyqtSlot()
    def sendMessage(self) -> None:
        message = self.messageInput.text()
        if not message:
            return

        # Utiliser self.aw.ser.SP pour accéder à l'instance du port série
        # (self.aw est l'instance d'ApplicationWindow, self.aw.ser est l'instance de serialport)
        if hasattr(self.aw.ser, 'SP') and self.aw.ser.SP.is_open:
            try:
                command = (message + '\n').encode('utf-8')
                self.aw.ser.SP.write(command)
                self.messageInput.clear()
                
                self.aw.seriallog.append(f"SENT: {message}")
                self.update_log()
                
            except Exception as e:
                self.aw.seriallog.append(f"ERROR: Failed to send message - {e}")
                self.update_log()
                
        else:
            self.aw.seriallog.append("ERROR: Serial port not open. Cannot send message.")
            self.update_log()
 
    def getstring(self) -> str:
        #convert list of serial comm an html string
        htmlserial = 'version = ' +__version__ +'<br><br>'
        lenl = len(self.aw.seriallog)
        for i in range(len(self.aw.seriallog)):
            htmlserial += str(lenl-i) + '\t'+ self.aw.seriallog[-i-1] + '<br>'
        return htmlserial

    def update_log(self) -> None:
        if self.aw.seriallogflag:
            self.serialEdit.setText(self.getstring())

    @pyqtSlot(int)
    def serialcheckboxChanged(self, _:int) -> None:
        if self.serialcheckbox.isChecked():
            self.aw.seriallogflag = True
        else:
            self.aw.seriallogflag = False

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.close()
        self.aw.serial_dlg = None

##########################################################################
#####################  VIEW ERROR LOG DLG  ###############################
##########################################################################

class errorDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Error Log'))
        self.elabel = QLabel()
        self. errorEdit = QTextEdit()
        self.errorEdit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.elabel,0)
        layout.addWidget(self.errorEdit,1)
        self.setLayout(layout)
        self.update_log()

    def update_log(self) -> None:
        #convert list of errors to an html string
        lenl = len(self.aw.qmc.errorlog)
        htmlerr = ''.join([f'<b>{lenl-i}</b> {m}<br><br>' for i,m in enumerate(reversed(self.aw.qmc.errorlog))])

        enumber = len(self.aw.qmc.errorlog)
        labelstr =  '<b>'+ QApplication.translate('Label','Number of errors found {0}').format(str(enumber)) + '</b>'
        self.elabel.setText(labelstr)
        self.errorEdit.setHtml('version = ' +__version__ +'<br><br>' + htmlerr)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.close()
        self.aw.error_dlg = None


##########################################################################
#####################  MESSAGE HISTORY DLG  ##############################
##########################################################################

class messageDlg(ArtisanDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate('Form Caption','Message History'))
        self.messageEdit = QTextEdit()
        self.messageEdit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.messageEdit,0)
        self.setLayout(layout)
        self.update_log()

    def update_log(self) -> None:
        #convert list of messages to an html string
        lenl = len(self.aw.messagehist)
        htmlmessage = ''.join([f'{lenl-i} {m}<br><br>' for i,m in enumerate(reversed(self.aw.messagehist))])
        self.messageEdit.setHtml(htmlmessage)

    @pyqtSlot('QCloseEvent')
    def closeEvent(self, _:Optional['QCloseEvent'] = None) -> None:
        self.close()
        self.aw.message_dlg = None
