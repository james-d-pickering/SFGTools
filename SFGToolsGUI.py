from PyQt5 import QtCore, QtWidgets
from SFGTools_ui import Ui_MainWindow
import sys
import sfgtools as SFGTools
from pathlib import PurePath

class ItemDelegate(QtWidgets.QStyledItemDelegate):
    editingstarted = QtCore.pyqtSignal(int, int)
    editingfinished = QtCore.pyqtSignal(int, int)

    def createEditor(self, parent, option, index):
        result = super(ItemDelegate, self).createEditor(parent, option, index)
        if result:
            self.editingstarted.emit(index.row(), index.column())
        return result


class TableModel(QtCore.QAbstractTableModel):

    def __init__(self, data, header):
        super(TableModel, self).__init__()
        self.tabledata = data
        self.header_labels = header

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.header_labels[section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
                if 0 <= index.column() < len(self.tabledata):
                    if 0 <= index.row() < len(self.tabledata[index.column()][:]):
                        value = self.tabledata[index.column()][index.row()]
                        return str(value)

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            self.tabledata[index.column()][index.row()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def rowCount(self, index):
        return len(self.tabledata[0])

    def columnCount(self, index):
        return 3

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def add_rows(self, new_rows):
        current_rows = self.rowCount(0)
        self.beginInsertRows(QtCore.QModelIndex(), current_rows, new_rows)
        self.insertRows(current_rows, new_rows - current_rows)
        self.endInsertRows()


class MainWindowUIClass(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.model = SFGTools.SFGProcessTools()
        # JDP persistent settings between runs
        self.initsettings = QtCore.QSettings()

        # JDP initialise checkboxes - these store as True/False values and inherit whatever is set as default
        # in Qt designer
        self.model.verbose = self.verbose_check.isChecked()
        self.model.downconvert_check = self.downconvert_checkbox.isChecked()
        self.model.subtract_check = self.subtract_checkbox.isChecked()
        self.model.normalise_check = self.normalise_checkbox.isChecked()
        self.model.exposure_check = self.exposure_checkbox.isChecked()
        self.model.plot_data_check = self.plot_data_checkbox.isChecked()
        self.model.write_file_check = self.write_file_checkbox.isChecked()
        self.model.cosmic_kill_check = self.killcosmic_checkbox.isChecked()
        self.model.calibrate_check = self.calibrate_checkbox.isChecked()
        self.model.close_plots_check = self.close_plots_checkbox.isChecked()
        self.model.stack_plots_check = self.stack_plots_checkbox.isChecked()
        self.model.auto_sort_check = self.auto_sort_checkbox.isChecked()

        # JDP getting last run values for boxes and things from the Qsettings
        if self.initsettings.value("last_dir"):
            self.data_directory_box.setText(self.initsettings.value("last_dir"))
            self.model.data_directory = self.initsettings.value("last_dir")

        if self.initsettings.value("last_write_dir"):
            self.write_directory_box.setText(self.initsettings.value("last_write_dir"))
            self.model.write_directory = self.initsettings.value("last_write_dir")

        if self.initsettings.value("last_samplestring"):
            self.sample_string_box.setText(self.initsettings.value("last_samplestring"))
            self.model.samplestring = self.initsettings.value("last_samplestring")

        if self.initsettings.value("last_refstring"):
            self.ref_string_box.setText(self.initsettings.value("last_refstring"))
            self.model.refstring = self.initsettings.value("last_refstring")

        if self.initsettings.value("last_cosmicwidth"):
            self.cosmic_width_box.setText(self.initsettings.value("last_cosmicwidth"))
            self.model.cosmic_max_width = self.initsettings.value("last_cosmicwidth")

        if self.initsettings.value("last_cosmicthreshold"):
            self.cosmic_threshold_box.setText(self.initsettings.value("last_cosmicthreshold"))
            self.model.cosmic_threshold = self.initsettings.value("last_cosmicthreshold")

        if self.initsettings.value("last_upconverter"):
            self.upconversion_line_dropdown.setCurrentText(self.initsettings.value("last_upconverter"))
            self.model.upconversion_line_num = self.initsettings.value("last_upconverter")

        if self.initsettings.value("last_caliboffset"):
            self.calibrate_offset_box.setText(str(self.initsettings.value("last_caliboffset")))
            self.model.calibration_offset = self.initsettings.value("last_caliboffset")

        if self.initsettings.value("last_regionstart"):
            self.custom_region_start_textbox.setText(self.initsettings.value("last_regionstart"))
            self.model.custom_region_start = self.initsettings.value("last_regionstart")

        if self.initsettings.value("last_regionend"):
            self.custom_region_end_textbox.setText(self.initsettings.value("last_regionend"))
            self.model.custom_region_end = self.initsettings.value("last_regionend")

        if self.initsettings.value("last_bgstring"):
            self.bg_string_box.setText(self.initsettings.value("last_bgstring"))
            self.model.bg_string = self.initsettings.value("last_bgstring")

        self.model.upconversion_line_num = float(self.upconversion_line_dropdown.currentText())
        self.datatable_headers = ['Signal', 'Background', 'Reference ID']
        self.referencetable_headers = ['Reference', 'Background', 'ID']
        self.tablemodel = TableModel(self.model.tabledata, self.datatable_headers)
        self.dataTable.setModel(self.tablemodel)
        self.tablemodelRef = TableModel(self.model.reftabledata, self.referencetable_headers)
        self.referenceTable.setModel(self.tablemodelRef)

    def setupUi(self, mainWindow):
        super().setupUi(mainWindow)
        self.delegate = ItemDelegate(mainWindow)
        self.dataTable.setItemDelegate(self.delegate)
        self.referenceTable.setItemDelegate(self.delegate)

    @QtCore.pyqtSlot()
    def detonateSlot(self):
        self.model.pull_trigger()

    @QtCore.pyqtSlot()
    def data_directorySlot(self):
        self.model.data_directory = self.data_directory_box.text()
        if self.model.data_directory:
            self.initsettings.setValue("last_dir", self.model.data_directory)

    @QtCore.pyqtSlot()
    def write_directory_boxSlot(self):
        self.model.write_directory = self.write_directory_box.text()
        if self.model.write_directory:
            self.initsettings.setValue("last_write_dir", self.model.write_directory)

    @QtCore.pyqtSlot()
    def sample_stringSlot(self):
        self.model.samplestring = self.sample_string_box.text()
        if self.model.samplestring:
            self.initsettings.setValue("last_samplestring", self.model.samplestring)

    @QtCore.pyqtSlot()
    def ref_stringSlot(self):

        self.model.refstring = self.ref_string_box.text()
        if self.model.refstring:
            self.initsettings.setValue("last_refstring", self.model.refstring)

    @QtCore.pyqtSlot()
    def bg_string_boxSlot(self):

        self.model.bg_string = self.bg_string_box.text()
        if self.model.bg_string:
            self.initsettings.setValue("last_bgstring", self.model.bg_string)

    @QtCore.pyqtSlot()
    def browse_directorySlot(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)

        self.model.data_directory = dlg.getExistingDirectory(self) + r'/'
        if not self.model.write_directory:
            self.model.write_directory = self.model.data_directory
            self.write_directory_box.setText(self.model.write_directory)

        if self.model.data_directory:
            self.initsettings.setValue("last_dir", self.model.data_directory)
            self.data_directory_box.setText(self.model.data_directory)

    @QtCore.pyqtSlot()
    def browse_write_directorySlot(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)

        self.model.write_directory = dlg.getExistingDirectory(self) + r'/'

        if self.model.write_directory:
            self.initsettings.setValue("last_write_dir", self.model.write_directory)
            self.write_directory_box.setText(self.model.write_directory)

    @QtCore.pyqtSlot()
    def browse_signal_filesSlot(self):

        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        filepaths = dlg.getOpenFileNames(self)[0]

        filenames = []
        for i, file in enumerate(filepaths):
            if i == 0:
                self.model.data_directory = str(PurePath(file).parent) + r'/'
            filename = PurePath(file).name
            filenames.append(filename)

        self.data_directory_box.setText(self.model.data_directory)
        self.model.signal_names = filenames
        self.model.update_datatable()
        self.dataTable.model().layoutAboutToBeChanged.emit()
        self.tablemodel.add_rows(len(filenames))
        self.tablemodel.tabledata = self.model.tabledata
        self.dataTable.model().layoutChanged.emit()

    @QtCore.pyqtSlot()
    def browse_background_filesSlot(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        filepaths = dlg.getOpenFileNames(self)[0]
        filenames = []
        for i, file in enumerate(filepaths):
            filename = PurePath(file).name
            filenames.append(filename)
        self.model.bg_names = filenames
        self.model.update_datatable()
        self.dataTable.model().layoutAboutToBeChanged.emit()
        self.tablemodel.add_rows(len(filenames))
        self.tablemodel.tabledata = self.model.tabledata
        self.dataTable.model().layoutChanged.emit()

    @QtCore.pyqtSlot()
    def browse_reference_filesSlot(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        filepaths = dlg.getOpenFileNames(self)[0]
        filenames = []
        refnums = []
        for i, file in enumerate(filepaths):
            filename = PurePath(file).name
            filenames.append(filename)
            refnums.append(i + 1)
        self.model.ref_num = refnums
        self.model.ref_names = filenames
        self.model.update_reftable()
        self.referenceTable.model().layoutAboutToBeChanged.emit()
        self.tablemodelRef.add_rows(len(filenames))
        self.tablemodelRef.tabledata = self.model.reftabledata
        self.referenceTable.model().layoutChanged.emit()

    @QtCore.pyqtSlot()
    def browse_reference_background_filesSlot(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        filepaths = dlg.getOpenFileNames(self)[0]
        filenames = []
        for i, file in enumerate(filepaths):
            filename = PurePath(file).name
            filenames.append(filename)
        self.model.ref_bg_names = filenames
        self.model.update_reftable()
        self.referenceTable.model().layoutAboutToBeChanged.emit()
        self.tablemodelRef.add_rows(len(filenames))
        self.tablemodelRef.tabledata = self.model.reftabledata
        self.referenceTable.model().layoutChanged.emit()

    @QtCore.pyqtSlot()
    def editSlot(self):
        print(self.tablemodel.tabledata)

    @QtCore.pyqtSlot()
    def upconversion_line_dropdownSlot(self):
        self.model.upconversion_line_num = self.upconversion_line_dropdown.currentText()
        # if not self.model.upconversion_line_num.isnumeric():
        #   err = QtWidgets.QMessageBox()
        #  err.setText("Upconversion line input must be numeric")
        # err.setIcon(QtWidgets.QMessageBox.Warning)
        # err.setStandardButtons(QtWidgets.QMessageBox.Ok)
        # err.setDefaultButton(QtWidgets.QMessageBox.Ok)
        # err.exec_()

        self.model.upconversion_line_num = float(self.model.upconversion_line_num)
        self.initsettings.setValue("last_upconverter", self.model.upconversion_line_num)

    @QtCore.pyqtSlot()
    def custom_region_start_textboxSlot(self):
        self.model.custom_region_start = self.custom_region_start_textbox.text()
        if self.model.custom_region_start == '':
            self.model.custom_region_start = None

        self.initsettings.setValue("last_regionstart", self.model.custom_region_start)

    @QtCore.pyqtSlot()
    def custom_region_end_textboxSlot(self):
        self.model.custom_region_end = self.custom_region_end_textbox.text()
        if self.model.custom_region_end == '':
            self.model.custom_region_end = None
        self.initsettings.setValue("last_regionend", self.model.custom_region_end)

    @QtCore.pyqtSlot()
    def downconvert_checkboxSlot(self):
        self.model.downconvert_check = self.downconvert_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def subtract_checkboxSlot(self):
        self.model.subtract_check = self.subtract_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def normalise_checkboxSlot(self):
        self.model.normalise_check = self.normalise_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def exposure_checkboxSlot(self):
        self.model.exposure_check = self.exposure_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def plot_data_checkboxSlot(self):
        self.model.plot_data_check = self.plot_data_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def write_file_checkboxSlot(self):
        self.model.write_file_check = self.write_file_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def verboseSlot(self):
        self.model.verbose = self.verbose_check.isChecked()

    @QtCore.pyqtSlot()
    def stupid_verboseSlot(self):
        self.model.stupid_verbose = self.stupid_verbose_check.isChecked()

    @QtCore.pyqtSlot()
    def cosmic_kill_checkboxSlot(self):
        self.model.cosmic_kill_check = self.killcosmic_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def cosmic_thresholdSlot(self):
        self.model.cosmic_threshold = float(self.cosmic_threshold_box.text())
        self.initsettings.setValue("last_cosmicthreshold", self.model.cosmic_threshold)

    @QtCore.pyqtSlot()
    def cosmic_widthSlot(self):
        self.model.cosmic_max_width = float(self.cosmic_width_box.text())
        self.initsettings.setValue("last_cosmicwidth", self.model.cosmic_max_width)

    @QtCore.pyqtSlot()
    def calibrate_checkboxSlot(self):
        self.model.calibrate_check = self.calibrate_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def calibrate_offsetSlot(self):
        self.model.calibration_offset = self.calibrate_offset_box.text()
        self.initsettings.setValue("last_caliboffset", self.model.calibration_offset)

    @QtCore.pyqtSlot()
    def clear_persistent_settingsSlot(self):

        if self.initsettings.value("last_dir"):
            self.model.data_directory = None
            self.data_directory_box.setText(self.model.data_directory)

        if self.initsettings.value("last_write_dir"):
            self.model.write_directory = None
            self.write_directory_box.setText(self.model.write_directory)

        if self.initsettings.value("last_samplestring"):
            self.model.samplestring = None
            self.sample_string_box.setText(self.model.samplestring)

        if self.initsettings.value("last_refstring"):
            self.model.refstring = None
            self.ref_string_box.setText(self.model.refstring)

        if self.initsettings.value("last_cosmicwidth"):
            self.model.cosmic_max_width = None
            self.cosmic_width_box.setText(self.model.cosmic_max_width)

        if self.initsettings.value("last_cosmicthreshold"):
            self.model.cosmic_threshold = None
            self.cosmic_threshold_box.setText(self.model.cosmic_threshold)

        if self.initsettings.value("last_upconverter"):
            self.model.upconversion_line_num = None
            self.upconversion_line_dropdown.setCurrentText(self.model.upconversion_line_num)

        if self.initsettings.value("last_caliboffset"):
            self.model.calibration_offset = None
            self.calibrate_offset_box.setText(self.model.calibration_offset)

        if self.initsettings.value("last_regionstart"):
            self.model.custom_region_start = None
            self.custom_region_start_textbox.setText(self.model.custom_region_start)

        if self.initsettings.value("last_regionend"):
            self.model.custom_region_end = None
            self.custom_region_end_textbox.setText(self.model.custom_region_end)

        for i in self.initsettings.allKeys():
            self.initsettings.remove(i)

    @QtCore.pyqtSlot()
    def close_plotsSlot(self):
        self.model.close_plots_check = self.close_plots_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def auto_sortSlot(self):
        self.model.signal_names, self.model.bg_names, self.model.ref_names, self.model.ref_bg_names, \
            self.model.sig_ref_num, self.model.ref_num = self.model.match_files(self.model.signal_names,
                                                                                self.model.bg_names,
                                                                                self.model.ref_names,
                                                                                self.model.ref_bg_names,
                                                                                self.model.ref_num,
                                                                                self.model.data_directory)

        self.model.update_datatable()
        self.model.update_reftable(remove_duplicates=True)
        self.update_gui_tables()

    def update_gui_tables(self):
        self.referenceTable.model().layoutAboutToBeChanged.emit()
        self.dataTable.model().layoutAboutToBeChanged.emit()
        self.tablemodel.tabledata = self.model.tabledata
        self.tablemodelRef.tabledata = self.model.reftabledata
        self.referenceTable.model().layoutChanged.emit()
        self.dataTable.model().layoutChanged.emit()

    @QtCore.pyqtSlot()
    def testSlot(self):
        print('Data to put into processing:')
        dat = [self.model.signal_names, self.model.bg_names, self.model.ref_names, self.model.ref_bg_names]
        for v in zip(*dat):
            print(v)

    @QtCore.pyqtSlot()
    def get_dataSlot(self):
        self.model.signal_names, self.model.bg_names, self.model.ref_names, self.model.ref_bg_names, \
            self.model.ref_num = self.model.get_filenames_smart()
        if self.model.auto_sort_check:
            self.model.signal_names, self.model.bg_names, self.model.ref_names, self.model.ref_bg_names, \
            self.model.sig_ref_num, self.model.ref_num = self.model.match_files(self.model.signal_names,
                                                                                self.model.bg_names,
                                                                                self.model.ref_names,
                                                                                self.model.ref_bg_names,
                                                                                self.model.ref_num,
                                                                                self.model.data_directory)
        self.model.update_datatable()
        self.model.update_reftable(remove_duplicates=False)
        self.update_gui_tables()

    @QtCore.pyqtSlot()
    def stack_plots_checkboxSlot(self):
        self.model.stack_plots_check = self.stack_plots_checkbox.isChecked()

    @QtCore.pyqtSlot()
    def quit_Slot(self):
        QtWidgets.QApplication.quit()

    @QtCore.pyqtSlot()
    def auto_sort_checkSlot(self):
        self.model.auto_sort_check = self.auto_sort_checkbox.isChecked()


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("Surflab")
    app.setOrganizationDomain("Surflabdomain")
    app.setApplicationName("SFGProcess")

    ui = MainWindowUIClass()

    ui.show()
    app.exec()


main()
