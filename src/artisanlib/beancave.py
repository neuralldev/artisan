# simple bean cave management 
# mod programmed by Tilau (2025) 
# manage a json file with a list of green beans and associate roasts to them by name
# manage stock in grams and use them in roast properties to enter basic information on beans
# decrease stock in g when they are selected from roast properties
# this mod does not replace Artisan plus bean management but is a simple inteface for enthousiasts

import sys
import platform
import logging
import json
from typing import Final, List, Optional, Any, cast, TYPE_CHECKING
import os
import ast  # Import de la bibliothèque ast
import qrcode # Import de la bibliothèque qrcode

from PIL.ImageQt import ImageQt # Import pour convertir l'image PIL en QImage

if TYPE_CHECKING:
    from artisanlib.atypes import Palette
    from artisanlib.main import ApplicationWindow # noqa: F401 # pylint: disable=unused-import
    from PyQt6.QtGui import QCloseEvent # pylint: disable=unused-import

from artisanlib.dialogs import ArtisanResizeablDialog, ArtisanDialog
from artisanlib.widgets import MyQComboBox, MyQDoubleSpinBox


try:
    from PyQt6.QtCore import (Qt, pyqtSlot, QSettings, QTimer, QByteArray) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtGui import (QColor, QFont, QIntValidator, QAction, QPixmap) # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,  # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QWidget, QTabWidget, QDialogButtonBox, # @UnusedImport @Reimport  @UnresolvedImport
                                 QGridLayout, QGroupBox, QTableWidget, QHeaderView, QToolButton, QTableWidgetItem, QLayout, QAbstractItemView, QFileDialog, QMessageBox, QDialog) # @UnusedImport @Reimport  @UnresolvedImport
#    from PyQt6 import sip # @UnusedImport @Reimport  @UnresolvedImport
except ImportError:
    from PyQt5.QtCore import (Qt, pyqtSlot, QSettings, QTimer, QByteArray) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtGui import (QColor, QFont, QIntValidator, QPixmap) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
    from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QPushButton, QSpinBox, QWidget, QTabWidget, QDialogButtonBox, # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
                                 QGridLayout, QGroupBox, QTableWidget, QHeaderView, QToolButton, QTableWidgetItem, QLayout, QAbstractItemView, QFileDialog, QMessageBox, QDialog) # type: ignore # @UnusedImport @Reimport  @UnresolvedImport
#    try:
#        from PyQt5 import sip # type: ignore # @Reimport @UnresolvedImport @UnusedImport
#    except ImportError:
#        import sip  # type: ignore # @Reimport @UnresolvedImport @UnusedImport


_log: Final[logging.Logger] = logging.getLogger(__name__)

# List of major coffee-producing countries (in English)
coffee_producing_countries = [
    {"Country": "Brazil"},
    {"Country": "Vietnam"},
    {"Country": "Colombia"},
    {"Country": "Indonesia"},
    {"Country": "Ethiopia"},
    {"Country": "Honduras"},
    {"Country": "India"},
    {"Country": "Uganda"},
    {"Country": "Mexico"},
    {"Country": "Peru"},
    {"Country": "Guatemala"},
    {"Country": "Nicaragua"},
    {"Country": "Costa Rica"},
    {"Country": "Ivory Coast"},
    {"Country": "Tanzania"},
    {"Country": "Kenya"},
    {"Country": "Papua New Guinea"},
    {"Country": "El Salvador"},
    {"Country": "Rwanda"},
    {"Country": "Burundi"},
    {"Country": "Democratic Republic of the Congo"},
    {"Country": "Yemen"},
    {"Country": "Thailand"},
    {"Country": "Laos"},
    {"Country": "Cameroon"},
    {"Country": "Other"},
]

# list of varieties
coffee_beans_species = [
    {'Specy':'Arabica'},
    {'Specy':'Liberica'},
    {'Specy':'Robusta'},
]

# List of main coffee bean types (species and common varieties)
coffee_bean_types = [
   {"Specy": "Arabica", "Variety": "Typica"},
    {"Specy": "Arabica", "Variety": "Bourbon"},
    {"Specy": "Arabica", "Variety": "Caturra"},
    {"Specy": "Arabica", "Variety": "Catuai"},
    {"Specy": "Arabica", "Variety": "SL28"},
    {"Specy": "Arabica", "Variety": "SL34"},
    {"Specy": "Arabica", "Variety": "Heirloom (Ethiopian)"},
    {"Specy": "Arabica", "Variety": "Pacamara"},
    {"Specy": "Arabica", "Variety": "Pacas"},
    {"Specy": "Arabica", "Variety": "Geisha (Gesha)"},
    {"Specy": "Arabica", "Variety": "Maragogype"},
    {"Specy": "Arabica", "Variety": "Villa Sarchi"},
    {"Specy": "Arabica", "Variety": "Rume Sudan"},
    {"Specy": "Arabica", "Variety": "Java"},
    {"Specy": "Arabica", "Variety": "H1 (Centroamericano)"},
    {"Specy": "Arabica", "Variety": "Castillo"},
    {"Specy": "Arabica", "Variety": "Colombia"},
    {"Specy": "Arabica", "Variety": "Catimor"},
    {"Specy": "Arabica", "Variety": "Other"},
    {"Specy": "Arabica", "Variety": "Mundo Novo"},
    {"Specy": "Arabica", "Variety": "Timor Hybrid"},
    {"Specy": "Arabica", "Variety": "Pink Bourbon"},
    {"Specy": "Arabica", "Variety": "Sarchimor"},
    {"Specy": "Arabica", "Variety": "Kona Typica"},
    {"Specy": "Arabica", "Variety": "Blue Mountain"},
    {"Specy": "Arabica", "Variety": "Kent"},
    {"Specy": "Arabica", "Variety": "Sidamo (Ethiopian)"},
    {"Specy": "Arabica", "Variety": "Yirgacheffe (Ethiopian)"},
    {"Specy": "Arabica", "Variety": "Ruiru 11"},
    {"Specy": "Arabica", "Variety": "Batian"},
    {"Specy": "Arabica", "Variety": "Arusha"},
    {"Specy": "Arabica", "Variety": "Pache"},
    {"Specy": "Arabica", "Variety": "Villalobos"},
    {"Specy": "Arabica", "Variety": "Lempira"},
    {"Specy": "Arabica", "Variety": "Obata"},
    {"Specy": "Robusta", "Variety": "Nganda"},
    {"Specy": "Robusta", "Variety": "Kouillou"},
    {"Specy": "Liberica", "Variety": "Excelsa"},
]

# Liste des processus de séchage connus
coffee_processing_methods = [
    "Natural / Dry",
    "Washed / Wet",
    "Honey / Pulped Natural",
    "Anaerobic",
    "Carbonic Maceration",
    "Semi-Washed / Giling Basah",
    "Monsooned",
    "Other"
]


# Ajout de 'Process' et 'Count' à la liste des en-têtes
greencave_headers = [
            'Name', 'Farm', 'Country', 'Supplier', 'Process', 'Crop', 'Density',
            'Humidity', 'Water activity', 'Volume', 'Altitude', 'Specy', 'Variety',
            'Stock', 'Flavour Notes', 'SCA score', 'Count', 
        ]

# Path to the JSON file
BEANCAVE_FILE_NAME: Final[str] = "beancave.json"

class GreenBean:
    def __init__(self,
                 name: str = '',
                 farm: str = '',
                 country: str = '',
                 supplier: str = '',
                 process: str = '', # Nouvelle propriété 'process'
                 crop: int = 0,
                 density: float = 0.0,
                 last_humidity: float = 0.0,
                 water_activity: float = 0.0,
                 volume: float = 0.0,
                 altitude: int = 0,
                 species: str = "",
                 varieties: str = "",
                 weight_left: float = 0.0,
                 flavour_notes: str = '',
                 sca: float = 0.0,
                 count: int = 0) -> None: # Nouvelle propriété 'count'
        self.name = name
        self.farm = farm
        self.country = country
        self.supplier = supplier
        self.process = process # Initialisation de la nouvelle propriété
        self.crop = crop
        self.density = density
        self.last_humidity = last_humidity
        self.water_activity = water_activity
        self.volume = volume
        self.altitude = altitude
        self.species = species 
        self.varieties = varieties
        self.weight_left = weight_left
        self.flavour_notes = flavour_notes
        self.sca = sca
        self.count = count # Initialisation de la nouvelle propriété

    def to_dict(self) -> dict:
        return self.__dict__

    @staticmethod
    def from_dict(data: dict) -> 'GreenBean':
        return GreenBean(**data)
    
class BeanHelper:
    def __init__(self):
        self.green_beans = []
        self.load_green_beans()

    def isbeancave(self) -> bool:
        return len(self.green_beans)>0     

    def load_green_beans(self, selection:Optional[str] = None) -> None:
        settings = QSettings()
        self.alog_directory = settings.value('alogDirectory', "", str)
        self.beancave_directory = settings.value('beancaveDirectory', self.alog_directory, str)
        beancave_file_path = os.path.join(self.beancave_directory, BEANCAVE_FILE_NAME)
        if os.path.exists(beancave_file_path):
            try:
                with open(beancave_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.green_beans = [GreenBean.from_dict(d) for d in data.get('green_beans', [])]
            except json.JSONDecodeError as e:
                _log.error(f'Error reading beancave.json: {e}')
            except Exception as e:
                _log.error(f'Unexpected error while reading beancave.json: {e}')
                if selection is not None:
                    self.green_beans.insert(0, GreenBean(name=selection)) 
        else:
            self.green_beans = []
            if selection is not None:
                self.green_beans.insert(0, GreenBean(name=selection))

    def get_bean_list_for_combobox(self) -> List[str]:
        bean_list = []
        for bean in self.green_beans:
            # Assurer que les champs existent avant de les utiliser
            name = bean.name if hasattr(bean, 'name') else 'N/A'
            process = bean.process if hasattr(bean, 'process') else 'N/A'
            crop = str(bean.crop) if hasattr(bean, 'crop') and bean.crop != 0 else 'N/A'
            if bean.weight_left is not None and bean.weight_left > 0:
                left = "("+str(bean.weight_left)+"g)"
            else:
                left=""
            bean_list.append(f"{name} - {process} - {crop} {left}")
        return bean_list

    def get_bean_data_by_index(self, index: int) -> Optional[dict[str,Any]]:
        if 0 <= index < len(self.green_beans):
            return self.green_beans[index].to_dict()
        return None

class BeancaveDlg(ArtisanResizeablDialog):
    def __init__(self, parent:'QWidget', aw:'ApplicationWindow') -> None:
        super().__init__(parent, aw)
        self.app = self.aw.app
        self.green_beans: List[GreenBean] = []
        self.alog_directory = "" # Pour stocker le chemin du répertoire ALog
        self.beancave_directory = "" # Nouvelle variable pour le répertoire de beancave.json
        coffee_bean_types.sort(key=lambda x: (x["Specy"], x["Variety"]))
        coffee_producing_countries.sort(key=lambda x: (x["Country"]))
        self.load_settings()
        self.load_green_beans()
        self.last_sorted_column = -1
        self.sort_order = Qt.SortOrder.AscendingOrder
       
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Initialisation des QTableWidget
        self.datatable = QTableWidget()

        self.createdatatable()
        self.setup_ui()
        self.populate_table()
        
    def setup_ui(self) -> None:
        main_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        self.main_tab = QWidget()
        self.file_management_tab = QWidget()

        self.tab_widget.addTab(self.main_tab, "Green Beans")
        self.tab_widget.addTab(self.file_management_tab, "File Management")

        self.setup_main_tab_ui()
        self.setup_file_management_tab_ui()

        main_layout.addWidget(self.tab_widget)

        settings = QSettings()
        if settings.contains('BeanCaveGeometry'):
            self.restoreGeometry(settings.value('BeanCaveGeometry'))
        else:
            self.setGeometry(100, 100, 1200, 800)

        main_layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint) # type: ignore

        self.setLayout(main_layout)
        self.setWindowTitle(QApplication.translate('Form Caption','Green Beans management'))
        
        self.restore_table_state()
        self.update_directory_labels()
    
    def setup_main_tab_ui(self) -> None:
        main_tab_layout = QVBoxLayout()

        form_group_box = QGroupBox('Add/Modify')
        form_layout = QGridLayout()

        self.name_input = QLineEdit()
        self.farm_input = QLineEdit()
        self.farm_input.setMaxLength(64)
        self.country_combo = QComboBox()
        self.country_combo.addItems([c['Country'] for c in coffee_producing_countries])
        self.supplier_input = QLineEdit()
        self.supplier_input.setMaxLength(64)
        self.process_combo = QComboBox()
        self.process_combo.addItems(coffee_processing_methods)
        self.crop_input = MyQDoubleSpinBox()
        self.crop_input.setRange(2024, 2999)
        self.crop_input.setDecimals(0)
        self.density_input = MyQDoubleSpinBox()
        self.density_input.setRange(500, 800)
        self.density_input.setDecimals(0)
        self.density_input.setSuffix("g/l")
        self.last_humidity_input = MyQDoubleSpinBox()
        self.last_humidity_input.setRange(0.0, 100.0)
        self.last_humidity_input.setDecimals(1)
        self.last_humidity_input.setSingleStep(0.1)
        self.last_humidity_input.setSuffix("%")
        self.water_activity_input = MyQDoubleSpinBox()
        self.water_activity_input.setRange(0.0, 1.0)
        self.water_activity_input.setDecimals(2)
        self.water_activity_input.setSuffix("%")
        self.volume_input = MyQDoubleSpinBox()
        self.volume_input.setRange(0.0, 999.999)
        self.volume_input.setDecimals(3)
        self.volume_input.setSuffix("l")
        self.altitude_input = MyQDoubleSpinBox()
        self.altitude_input.setRange(0, 3000)
        self.altitude_input.setDecimals(0)
        self.altitude_input.setSuffix("m")
        self.species_combo = QComboBox()
        self.species_combo.addItems([s["Specy"] for s in coffee_beans_species])
        self.varieties_combo = QComboBox()
        self.varieties_combo.addItems([v["Variety"] for v in coffee_bean_types])
        self.weight_left_input = MyQDoubleSpinBox()
        self.weight_left_input.setRange(0.0, 9999.9)
        self.weight_left_input.setSingleStep(1)
        self.weight_left_input.setSuffix("g")
        self.weight_left_input.setDecimals(1)
        self.flavour_notes_input = QLineEdit()
        self.flavour_notes_input.setMaxLength(512)
        self.sca_input = MyQDoubleSpinBox()
        self.sca_input.setRange(0, 100)
        self.sca_input.setDecimals(1)

        form_layout.addWidget(QLabel(greencave_headers[0]), 0, 0)
        form_layout.addWidget(self.name_input, 0, 1 , 1, 4)
        form_layout.addWidget(QLabel(greencave_headers[1]), 1, 0)
        form_layout.addWidget(self.farm_input, 1, 1, 1, 4)
        form_layout.addWidget(QLabel(greencave_headers[2]), 2, 0)
        form_layout.addWidget(self.country_combo, 2, 1, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[3]), 3, 0)
        form_layout.addWidget(self.supplier_input, 3, 1, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[4]), 3, 3)
        form_layout.addWidget(self.process_combo, 3, 4, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[5]), 4, 0)
        form_layout.addWidget(self.crop_input, 4, 1, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[6]), 4, 3)
        form_layout.addWidget(self.density_input, 4, 4, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[7]), 5, 0)
        form_layout.addWidget(self.last_humidity_input, 5, 1, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[8]), 5, 3)
        form_layout.addWidget(self.water_activity_input, 5, 4, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[9]), 6, 0)
        form_layout.addWidget(self.volume_input, 6, 1, 1 , 1)
        form_layout.addWidget(QLabel(greencave_headers[10]), 6, 3)
        form_layout.addWidget(self.altitude_input, 6, 4, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[11]), 7, 0)
        form_layout.addWidget(self.species_combo, 7, 1)
        form_layout.addWidget(QLabel(greencave_headers[12]), 8, 0)
        form_layout.addWidget(self.varieties_combo, 8, 1)
        form_layout.addWidget(QLabel(greencave_headers[13]), 9, 0)
        form_layout.addWidget(self.weight_left_input, 9, 1, 1, 1)
        form_layout.addWidget(QLabel(greencave_headers[14]), 10, 0)
        form_layout.addWidget(self.flavour_notes_input, 10, 1, 1, 4)
        form_layout.addWidget(QLabel(greencave_headers[15]), 11, 0)
        form_layout.addWidget(self.sca_input, 11, 1)
        form_group_box.setLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton('Add')
        self.add_button.clicked.connect(self.add_new_row)
        self.update_button = QPushButton('Update')
        self.update_button.clicked.connect(self.update_selected_bean)
        remove_button = QPushButton('Delete')
        remove_button.clicked.connect(self.remove_green_bean)
        self.generate_qr_button = QPushButton("Generate QRCode")
        self.generate_qr_button.clicked.connect(self.generate_qr_code)

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(self.generate_qr_button)


        main_tab_layout.addWidget(form_group_box)
        main_tab_layout.addLayout(button_layout)
        main_tab_layout.addWidget(self.datatable)
        self.main_tab.setLayout(main_tab_layout)

    def setup_file_management_tab_ui(self) -> None:
        file_management_layout = QVBoxLayout()
        
        button_layout = QGridLayout()
        self.select_beancave_directory_button = QPushButton("Select Beancave directory")
        self.select_beancave_directory_button.clicked.connect(self.select_beancave_directory)
        self.beancave_directory_label = QLabel(f"Beancave directory: {self.beancave_directory}")
        button_layout.addWidget(self.select_beancave_directory_button, 0, 0)
        button_layout.addWidget(self.beancave_directory_label, 0, 1, 1, 3)

        self.select_alog_directory_button = QPushButton("Select ALog directory")
        self.select_alog_directory_button.clicked.connect(self.select_alog_directory)
        self.alog_directory_label = QLabel(f"ALog directory: {self.alog_directory}")
        button_layout.addWidget(self.select_alog_directory_button, 1, 0)
        button_layout.addWidget(self.alog_directory_label, 1, 1, 1, 3)

        self.update_alog_counts_button = QPushButton("Update Roast Sessions")
        self.update_alog_counts_button.clicked.connect(self.update_alog_counts)
        button_layout.addWidget(self.update_alog_counts_button, 2, 0)

        file_management_layout.addLayout(button_layout)
        file_management_layout.addStretch(1)

        self.file_management_tab.setLayout(file_management_layout)
    
    def get_bean_headers(self) -> List[str]:
        return greencave_headers

    def populate_table(self) -> None:
        self.datatable.setRowCount(len(self.green_beans))
        self.datatable.clearSelection() # Clear existing selection

        for row, bean in enumerate(self.green_beans):
            self.datatable.setItem(row, 0, QTableWidgetItem(bean.name)) # type: ignore
            self.datatable.setItem(row, 1, QTableWidgetItem(bean.farm)) # type: ignore
            self.datatable.setItem(row, 2, QTableWidgetItem(bean.country)) # type: ignore
            self.datatable.setItem(row, 3, QTableWidgetItem(bean.supplier)) # type: ignore
            self.datatable.setItem(row, 4, QTableWidgetItem(bean.process)) # Nouvelle colonne pour le process
            self.datatable.setItem(row, 5, QTableWidgetItem(str(int(bean.crop)))) # type: ignore
            self.datatable.setItem(row, 6, QTableWidgetItem(str(bean.density))) # type: ignore
            self.datatable.setItem(row, 7, QTableWidgetItem(str(bean.last_humidity))) # type: ignore
            self.datatable.setItem(row, 8, QTableWidgetItem(str(bean.water_activity))) # type: ignore
            self.datatable.setItem(row, 9, QTableWidgetItem(str(bean.volume))) # type: ignore
            self.datatable.setItem(row, 10, QTableWidgetItem(str(int(bean.altitude)))) # type: ignore
            self.datatable.setItem(row, 11, QTableWidgetItem(bean.species)) # type: ignore
            self.datatable.setItem(row, 12, QTableWidgetItem(bean.varieties)) # type: ignore
            self.datatable.setItem(row, 13, QTableWidgetItem(str(bean.weight_left))) # type: ignore
            self.datatable.setItem(row, 14, QTableWidgetItem(bean.flavour_notes)) # type: ignore
            self.datatable.setItem(row, 15, QTableWidgetItem(str(bean.sca))) # type: ignore
            self.datatable.setItem(row, 16, QTableWidgetItem(str(bean.count))) # Nouvelle colonne pour le count
        
        if len(self.green_beans) > 0:
            # Select the first row, which will trigger load_selected_bean_into_form
            self.datatable.selectRow(0)
            self.datatable.show()
        else:
            # If the table is empty, ensure the form is cleared
            self.clear_form()

    @pyqtSlot()
    def load_selected_bean_into_form(self) -> None:
        selected_rows = self.datatable.selectionModel().selectedRows() # type: ignore
        if not selected_rows:
            self.clear_form()
            return

        row = selected_rows[0].row() # Prend la première ligne sélectionnée
        if row < len(self.green_beans):
            bean = self.green_beans[row]
            self.name_input.setText(bean.name)
            self.farm_input.setText(bean.farm)
            self.country_combo.setCurrentText(bean.country)
            self.supplier_input.setText(bean.supplier)
            self.process_combo.setCurrentText(bean.process)
            self.crop_input.setValue(bean.crop)
            self.density_input.setValue(bean.density)
            self.last_humidity_input.setValue(bean.last_humidity)
            self.water_activity_input.setValue(bean.water_activity)
            self.volume_input.setValue(bean.volume)
            self.altitude_input.setValue(bean.altitude)
            # Pour les ComboBox qui supportent plusieurs valeurs (species, varieties), on prend la première ou vide
            self.species_combo.setCurrentText(bean.species if bean.species else "")
            self.varieties_combo.setCurrentText(bean.varieties if bean.varieties else "")
            self.weight_left_input.setValue(bean.weight_left)
            self.flavour_notes_input.setText(bean.flavour_notes)
            self.sca_input.setValue(bean.sca)
        else:
            # Si pour une raison quelconque la ligne sélectionnée est invalide, on efface le formulaire
            self.clear_form()

    @pyqtSlot()
    def add_new_row(self) -> None:
        """Crée une nouvelle ligne vide dans le tableau et la sélectionne."""
        new_bean_data = GreenBean(name='New Bean', crop=2024, count=0)
        self.green_beans.append(new_bean_data)
        self.save_green_beans()
        self.populate_table()
        
        # Sélectionne la nouvelle ligne et charge ses données dans le formulaire
        new_row_index = len(self.green_beans) - 1
        if new_row_index >= 0:
            self.datatable.selectRow(new_row_index)
            self.load_selected_bean_into_form()

    @pyqtSlot()
    def update_selected_bean(self) -> None:
        """Met à jour les données du grain sélectionné avec les valeurs du formulaire."""
        selected_row_index = self.datatable.currentRow()
        
        if selected_row_index == -1:
            _log.warning("No row selected for update.")
            return

        if selected_row_index < len(self.green_beans):
            # Create a new GreenBean object with the current form data
            current_count = self.green_beans[selected_row_index].count
            new_bean_data = GreenBean(
                name=self.name_input.text(),
                farm=self.farm_input.text(),
                country=self.country_combo.currentText(),
                supplier=self.supplier_input.text(),
                process=self.process_combo.currentText(),
                crop=int(self.crop_input.value()),
                density=self.density_input.value(),
                last_humidity=self.last_humidity_input.value(),
                water_activity=self.water_activity_input.value(),
                volume=self.volume_input.value(),
                altitude=int(self.altitude_input.value()),
                species=self.species_combo.currentText(),
                varieties=self.varieties_combo.currentText(),
                weight_left=self.weight_left_input.value(),
                flavour_notes=self.flavour_notes_input.text(),
                sca=self.sca_input.value(),
                count=current_count
            )
            self.green_beans[selected_row_index] = new_bean_data
            _log.info(f"Green bean updated at {selected_row_index}: {new_bean_data.name}")
            self.save_green_beans()
            self.populate_table()
            
            # Find the updated item and scroll to it
            updated_items = self.datatable.findItems(new_bean_data.name, Qt.MatchFlag.MatchExactly)
            if updated_items:
                updated_item = updated_items[0]
                self.datatable.scrollToItem(updated_item, QAbstractItemView.ScrollHint.PositionAtTop)
                self.datatable.selectRow(updated_item.row())
        else:
            _log.warning(f"Invalid row selected for update: {selected_row_index}")

    @pyqtSlot()
    def remove_green_bean(self) -> None:
        selected_rows = self.datatable.selectionModel().selectedRows() # type: ignore
        if not selected_rows:
            return

        for index in sorted(selected_rows, reverse=True):
            del self.green_beans[index.row()]
        self.save_green_beans()
        self.populate_table()
        self.clear_form()

    def sort_green_beans(self, key: str) -> None:
        self.green_beans.sort(key=lambda bean: getattr(bean, key))
        self.populate_table()
        self.save_green_beans()
        
    @pyqtSlot(int)
    def sort_by_column(self, column_index: int) -> None:
        """Trie la liste des grains de café en fonction de la colonne cliquée."""
        # Déterminer la clé de tri en fonction de l'index de la colonne
        sort_key_map = {
            0: 'name',
            1: 'farm',
            2: 'country',
            3: 'supplier',
            4: 'process',
            5: 'crop',
            6: 'density',
            7: 'last_humidity',
            8: 'water_activity',
            9: 'volume',
            10: 'altitude',
            11: 'species',
            12: 'varieties',
            13: 'weight_left',
            14: 'flavour_notes',
            15: 'sca',
            16: 'count'
        }
        
        sort_key = sort_key_map.get(column_index)
        if not sort_key:
            return

        # Basculer l'ordre de tri si la même colonne est cliquée à nouveau
        if self.last_sorted_column == column_index:
            if self.sort_order == Qt.SortOrder.AscendingOrder:
                self.sort_order = Qt.SortOrder.DescendingOrder
            else:
                self.sort_order = Qt.SortOrder.AscendingOrder
        else:
            self.sort_order = Qt.SortOrder.AscendingOrder
            
        self.last_sorted_column = column_index
        
        # Trier la liste des grains de café
        self.green_beans.sort(key=lambda bean: getattr(bean, sort_key), reverse=(self.sort_order == Qt.SortOrder.DescendingOrder))
        
        # Mettre à jour l'indicateur de tri sur l'en-tête
        self.datatable.horizontalHeader().setSortIndicator(column_index, self.sort_order) # type: ignore
        
        # Mettre à jour l'affichage de la table
        self.populate_table()
        self.save_green_beans()
        
    def load_green_beans(self) -> None:
        beancave_file_path = os.path.join(self.beancave_directory, BEANCAVE_FILE_NAME)
        if os.path.exists(beancave_file_path):
            try:
                with open(beancave_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # S'assurer que le champ 'count' et 'process' existent, sinon les créer
                    self.green_beans = [GreenBean.from_dict(d) for d in data.get('green_beans', [])]
                    for bean in self.green_beans:
                        if not hasattr(bean, 'count'):
                            bean.count = 0
                        if not hasattr(bean, 'process'):
                            bean.process = ""
            except json.JSONDecodeError as e:
                _log.error(f'Error reading beancave.json: {e}')
                QMessageBox.warning(self, "Read Error", f"Unable to read file '{beancave_file_path}'. The file might be corrupted.")
            except Exception as e:
                _log.error(f'Unexpected error while reading beancave.json: {e}')
                QMessageBox.warning(self, "Error", f"An unexpected error occurred: {e}")
        else:
            self.green_beans = []

    def save_green_beans(self) -> None:
        data = {'green_beans': [bean.to_dict() for bean in self.green_beans]}
        beancave_file_path = os.path.join(self.beancave_directory, BEANCAVE_FILE_NAME)
        try:
            # Créer le répertoire s'il n'existe pas
            os.makedirs(os.path.dirname(beancave_file_path), exist_ok=True)
            with open(beancave_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            _log.error(f'Error writing to beancave.json: {e}')
            QMessageBox.warning(self, "Save Error", f"Unable to save file '{beancave_file_path}'. Error: {e}")

    def clear_form(self) -> None:
        self.name_input.clear()
        self.farm_input.clear()
        self.country_combo.setCurrentIndex(0)
        self.supplier_input.clear()
        self.process_combo.setCurrentIndex(0)
        self.crop_input.setValue(0)
        self.density_input.setValue(0.0)
        self.last_humidity_input.setValue(0.0)
        self.water_activity_input.setValue(0.0)
        self.volume_input.setValue(0.0)
        self.altitude_input.setValue(0.0)
        self.species_combo.setCurrentIndex(0)
        self.varieties_combo.setCurrentIndex(0)
        self.weight_left_input.setValue(0.0)
        self.flavour_notes_input.clear()
        self.sca_input.setValue(0.0)

    def createdatatable(self) -> None:
        """
        Configure le QTableWidget (self.datatable) pour afficher les grains verts.
        """
        headers = self.get_bean_headers()
        self.datatable.setColumnCount(len(headers))
        self.datatable.setHorizontalHeaderLabels(headers)
        self.datatable.horizontalHeader().setSectionsMovable(True) # type: ignore
        # Permettre le redimensionnement interactif des colonnes
        self.datatable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)  # type: ignore
        self.datatable.itemSelectionChanged.connect(self.load_selected_bean_into_form)
        self.datatable.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # type: ignore
        self.datatable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # type: ignore
        # Permettre l'affichage de l'indicateur de tri
        self.datatable.setSortingEnabled(True)
        self.datatable.horizontalHeader().sectionClicked.connect(self.sort_by_column) # type: ignore

    def restore_table_state(self) -> None:
        """Restaure l'ordre et la largeur des colonnes depuis QSettings."""
        settings = QSettings()
        header:QHeaderView = self.datatable.horizontalHeader()
        
        # Restauration de l'ordre des colonnes
        order_str = settings.value('BeanCaveColumnOrder', None, str)
        if order_str:
            try:
                logical_indices = [int(i) for i in order_str.split(',')]
                # On s'assure que le nombre de colonnes correspond bien
                if len(logical_indices) == header.count():
                    for visual_index, logical_index in enumerate(logical_indices):
                        # Déplace la colonne avec l'index logique `logical_index` vers l'index visuel `visual_index`
                        header.moveSection(header.visualIndex(logical_index), visual_index)
                else:
                    _log.warning("Saved column order does not match current column count. Ignoring saved state.")
            except (ValueError, IndexError) as e:
                _log.error(f"Error restoring column order from settings: {e}")
        
        # Restauration des largeurs de colonnes (logique originale conservée)
        for i in range(header.count()):
            key = f'BeanCaveColumnWidth/{i}'
            if settings.contains(key):
                width = settings.value(key, header.sectionSize(i), type=int)
                header.resizeSection(i, width)
    
    def load_settings(self) -> None:
        settings = QSettings()
        self.alog_directory = settings.value('alogDirectory', "", str)
        self.beancave_directory = settings.value('beancaveDirectory', self.alog_directory, str)
               
    def save_settings(self) -> None:
        settings = QSettings()
        settings.setValue('alogDirectory', self.alog_directory)
        settings.setValue('beancaveDirectory', self.beancave_directory)

    def update_directory_labels(self) -> None:
        self.beancave_directory_label.setText(f"Beancave directory: {self.beancave_directory}")
        self.alog_directory_label.setText(f"ALog directory: {self.alog_directory}")
   
    @pyqtSlot('QCloseEvent')
    def closeEvent(self, event:Optional['QCloseEvent'] = None) -> None: # type: ignore
        settings = QSettings()
        settings.setValue('BeanCaveGeometry', self.saveGeometry())
        
        # Sauvegarde l'ordre des colonnes dans une chaîne de caractères
        header:QHeaderView = self.datatable.horizontalHeader()
        logical_indices = [header.logicalIndex(visual_index) for visual_index in range(header.count())]
        order_str = ','.join(map(str, logical_indices))
        settings.setValue('BeanCaveColumnOrder', order_str)
        
        # Sauvegarde les largeurs de colonnes
        for i in range(header.count()):
            settings.setValue(f'BeanCaveColumnWidth/{i}', header.sectionSize(i))
            
        self.aw.beanCaveMenuAction.setChecked(False)

    @pyqtSlot()
    def select_beancave_directory(self) -> None:
        new_dir = QFileDialog.getExistingDirectory(self, "Select Beancave directory", self.beancave_directory)
        if new_dir:
            self.beancave_directory = new_dir
            self.save_settings()
            self.load_green_beans()
            self.populate_table()
            self.update_directory_labels()
            _log.info(f"Beancave directory selected: {self.beancave_directory}")
            QMessageBox.information(self, "Beancave Directory Selected", 
                                    f"The directory '{self.beancave_directory}' has been selected.\n"
                                    "The beancave.json file is now loaded from this location.")

    @pyqtSlot()
    def select_alog_directory(self) -> None:
        settings = QSettings()
        default_dir = self.alog_directory if self.alog_directory else os.path.expanduser("~")
        alog_dir = QFileDialog.getExistingDirectory(self, "Select ALog directory", default_dir)
        if alog_dir:
            self.alog_directory = alog_dir
            self.save_settings()
            self.update_directory_labels()
            _log.info(f"ALog directory selected: {self.alog_directory}")
            QMessageBox.information(self, "ALog Directory Selected", 
                                    f"The directory '{self.alog_directory}' has been selected.\n"
                                    "Click on 'Update Roast Sessions' to update the counts.")

    @pyqtSlot()
    def update_alog_counts(self) -> None:
        """Met à jour le champ 'count' de chaque grain de café en fonction des fichiers ALog."""
        if not self.alog_directory or not os.path.isdir(self.alog_directory):
            QMessageBox.warning(self, "Error", "Please, select a valid ALog directory first.") # type: ignore
            return
        _log.info(f"update of Alog information from : {self.alog_directory}")
        
        # Réinitialiser tous les compteurs
        for bean in self.green_beans:
            bean.count = 0
        
        flagUpdate: bool = False
            
        alog_files = [f for f in os.listdir(self.alog_directory) if f.endswith('.alog')]
        
        for alog_file in alog_files:
            file_path = os.path.join(self.alog_directory, alog_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Utiliser ast.literal_eval pour une évaluation sûre de la chaîne de dictionnaire
                    data = ast.literal_eval(content)
                    alog_title = data.get('title', '')
                    if alog_title:
                        for bean in self.green_beans:
                            # Comparer le nom du grain avec le titre du fichier, en ignorant la casse
                            if bean.name.lower() in alog_title.lower():
                                flagUpdate = True
                                bean.count += 1
                                _log.debug(f"Match found for '{bean.name}' in '{alog_file}'")
                                alog_density_data = data.get('density')
                                if alog_density_data and isinstance(alog_density_data, list) and len(alog_density_data) > 0:
                                    bean.density = alog_density_data[0] if alog_density_data[0] >0 else bean.density # Assurez-vous que la première valeur est la densité
                                    _log.debug(f"Match found for density of '{bean.name}' in '{alog_file}'")

            except (IOError, ValueError, SyntaxError) as e:
                _log.warning(f"Unable to read or decode alog file '{alog_file}': {e}")
           
        if flagUpdate:
            self.save_green_beans()
            self.populate_table()
            QMessageBox.information(self, "Update finished", # type: ignore
                                "Information has been updated successfully.") 
        else:
            QMessageBox.information(self, "Update finished", # type: ignore
                                "No changes were made.")

    @pyqtSlot()
    def generate_qr_code(self) -> None:
        """Génère un QR code à partir des informations de la ligne sélectionnée (en JSON) et l'affiche."""
        selected_row_index = self.datatable.currentRow()
        if selected_row_index == -1:
            QMessageBox.warning(self, "Error", "Select a line to generate a QRCODE")
            return

        try:
            # Récupérer l'objet GreenBean de la ligne sélectionnée
            bean = self.green_beans[selected_row_index]

            # Convertir l'objet GreenBean en dictionnaire, puis en JSON
            data_dict = bean.to_dict()
            json_data = json.dumps(data_dict, indent=2, ensure_ascii=False)

            # Créer le QR code à partir de la chaîne JSON
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H, # type: ignore
                box_size=5,
                border=4,
            )
            qr.add_data(json_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Créer et afficher le dialogue
            qr_dialog = QDialog(self)
            qr_dialog.setWindowTitle(f"QR Code for {bean.name}")
            qr_dialog_layout = QVBoxLayout()
            
            label_info = QLabel("Scan the QR code to see information about the green coffee beans.")
            label_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qr_dialog_layout.addWidget(label_info)
            
            qr_label = QLabel()

            # Convertir l'image PIL en QPixmap pour l'affichage
            qimg = ImageQt(img.convert("RGB")) # type: ignore
            pixmap = QPixmap.fromImage(qimg)
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            qr_dialog_layout.addWidget(qr_label)
            qr_dialog.setLayout(qr_dialog_layout)
            qr_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error happened while generating the QRCode: {e}")
            _log.error(f"QRCode generation error: {e}")

    @pyqtSlot()
    def show_bean_data_from_combobox(self) -> None:
        """Affiche les données du grain sélectionné dans la QComboBox."""
        index = self.bean_selection_combo.currentIndex()
        bean_data = self.helper.get_bean_data_by_index(index)
        
        if bean_data:
            # Formater les données pour l'affichage
            data_str = json.dumps(bean_data, indent=2, ensure_ascii=False)
            
            # Créer et afficher un dialogue
            info_dialog = QMessageBox(self)
            info_dialog.setWindowTitle(f"Données pour {self.bean_selection_combo.currentText()}")
            info_dialog.setText("Voici les données complètes du grain de café sélectionné :")
            info_dialog.setInformativeText(f"<pre>{data_str}</pre>")
            info_dialog.exec()
        else:
            QMessageBox.warning(self, "Erreur", "Aucun grain de café n'est sélectionné.")