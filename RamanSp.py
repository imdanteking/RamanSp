import sys
import os
import time

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication, QStyleFactory, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon

from extract_spectrum import *
from process_spectrum import *
from merge_spectrum import *
from get_filenames_recursively import *
from test1 import Ui_Form

class SpectrumThread(QThread):
    progressSignal = pyqtSignal(str)

    def __init__(self, extracted_file_list, batch_size, output_directory_path, trim=False, trim_start=400, trim_end=1800, normalization_minmax=False, normalization_area=False, merged=False, merged_filename=""):
        super().__init__()
        self.extracted_file_list = extracted_file_list
        self.batch_size = batch_size
        self.output_directory_path = output_directory_path 
        self.trim = trim
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.normalization_minmax = normalization_minmax
        self.normalization_area = normalization_area
        self.merged = merged
        self.merged_filename = merged_filename
        self.output_file_list = []
        
    
    def run(self):
        extracted_dir_path = os.path.join(self.output_directory_path, "extracted_dir")
        processed_dir_path = os.path.join(self.output_directory_path, "processed_dir")
        merged_dir_path = os.path.join(self.output_directory_path, "merged_dir")
        # print("begin")
        if not(os.path.exists(extracted_dir_path)):
            os.makedirs(extracted_dir_path)
        if not(os.path.exists(processed_dir_path)):
            os.makedirs(processed_dir_path)

        # extract spectra
        self.progressSignal.emit("extract")
        for filename in self.extracted_file_list:
            # self.flushProcessInfo(filename+"\n")
            output_file = batch_extract_spectrum(self.batch_size, filename, extracted_dir_path)
            self.output_file_list.append(output_file)
            time.sleep(1)

        # process spectra
        self.progressSignal.emit("process")
        process_spectrum(extracted_dir_path, processed_dir_path, self.trim, self.trim_start, self.trim_end, self.normalization_minmax, self.normalization_area)

        # merge spectra
        if(self.merged):
            self.progressSignal.emit("merge")
            if not(os.path.exists(merged_dir_path)):
                os.makedirs(merged_dir_path)
            merged_file_path = os.path.join(merged_dir_path, self.merged_filename)
            merge_spectrum(processed_dir_path, merged_file_path)


class MainWidget(Ui_Form, QMainWindow):
    def __init__(self):
        super().__init__()
        # set UI
        self.setupUi(self)
        # raw spectrum files
        self.extracted_file_list = []
        # the amount of spectra extracted from one raw spectrum file, default 1
        self.spectrum_number = 1
        # number of all files
        self.total_file_amount = 0
        self.done_file_amount = 0
        # pyqt signals
        
        # disable options
        self.lineEdit_trim_start.setEnabled(False)
        self.lineEdit_trim_end.setEnabled(False)
        self.lineEdit_merged_filename.setEnabled(False)

    def selectDirectory(self):
        try:
            directory_path = QFileDialog.getExistingDirectory()
            return directory_path
        except Exception:
            QMessageBox.warning(None, "warning", "please choose a valid path...")
    # slot 
    def selectInputDirectory(self):
        self.input_directory_path = self.selectDirectory()
        self.lineEdit_input_path.clear()
        self.lineEdit_input_path.setText(self.input_directory_path)
        self.lineEdit_input_path.setCursorPosition(0)
    # slot
    def selectOutputDirectory(self):
        self.output_directory_path = self.selectDirectory()
        self.lineEdit_output_path.clear()
        self.lineEdit_output_path.setText(self.output_directory_path)
        self.lineEdit_output_path.setCursorPosition(0)
    
    # slot
    def enableMergeFileOption(self, checked):
        if(checked):
            self.lineEdit_merged_filename.setEnabled(True)
        else:
            self.lineEdit_merged_filename.setEnabled(False)
    
    # slot
    def enableTrimOption(self, checked):
        if(checked):
            self.lineEdit_trim_start.setEnabled(True)
            self.lineEdit_trim_end.setEnabled(True)
        else:
            self.lineEdit_trim_start.setEnabled(False)
            self.lineEdit_trim_end.setEnabled(False)
    
    #slot
    def check_normalization_minmax(self, checked):
        if(checked):
            self.radioButton_normalization_area.setChecked(False)

    #slot
    def check_normalization_area(self, checked):
        if(checked):
            self.radioButton_normalization_minmax.setChecked(False)


    def getExtractedFilenameList(self, root_path, file_list):
        get_filenames(root_path, file_list)
 
    def extractSpectrum(self, filename, spectrum_number):
        batch_extract_spectrum(spectrum_number ,filename)

    def getSpectrumNumber(self):
        spectrum_number = int(self.lineEdit_spectrum_number.text())
        if(isinstance(spectrum_number, int) and spectrum_number % 1 == 0):
            return spectrum_number
        else:
            return 1

    def getMergedFilename(self):
        filename = self.lineEdit_merged_filename.text()
        if(len(filename) != 0):
            return filename + ".csv"
        else:
            return "merged_file.csv"
    
    def flushProcessInfo(self, task):
        self.label_status.setText(task)
        self.label_status.repaint()
        self.done_file_amount = self.done_file_amount + 1
        self.label_7.setText(str(self.done_file_amount) + " / " + str(self.total_file_amount))
        self.label_7.repaint()
        self.updateProcessbarValue(self.done_file_amount)
    
    def initProcessbar(self, max):
        self.progressBar.setMaximum(max)
    
    def updateProcessbarValue(self, value):
        self.progressBar.setValue(value)

    #slot
    def startBatchExtraction(self):
        # prepare
        self.spectrum_number = self.getSpectrumNumber()

        self.trim = self.radioButton_trim.isChecked()
        if(self.lineEdit_trim_start.text().isdigit()):
            self.trim_start = int(self.lineEdit_trim_start.text())
        else:
            QMessageBox.warning(None, "warning", "please enter a valid number")
            return

        if(self.lineEdit_trim_end.text().isdigit()):
            self.trim_end = int(self.lineEdit_trim_end.text())
        else:
            QMessageBox.warning(None, "warning", "please enter a valid number")
            return

        self.normalization_minmax = self.radioButton_normalization_minmax.isChecked()
        self.normalization_area = self.radioButton_normalization_area.isChecked()

        self.merged = self.radioButton_merge_output.isChecked()
        self.merged_filename = self.getMergedFilename()


        # get all files recursively
        if(self.spectrum_number != None and self.input_directory_path != None):
            self.getExtractedFilenameList(self.input_directory_path, self.extracted_file_list)
            # get total file number
            self.total_file_amount = len(self.extracted_file_list)
            self.initProcessbar(self.total_file_amount)
        else:
            QMessageBox.warning(None, "error", "wrong parameters...")
            return

        # create thread
        self.progressThread = SpectrumThread(
            extracted_file_list=self.extracted_file_list, 
            batch_size=2, 
            output_directory_path=self.output_directory_path,
            trim=self.trim,
            trim_start=self.trim_start,
            trim_end=self.trim_end,
            normalization_minmax=self.normalization_minmax,
            normalization_area=self.normalization_area,
            merged=self.merged,
            merged_filename = self.merged_filename)

        self.progressThread.progressSignal.connect(self.flushProcessInfo)
        self.progressThread.start()

        # clear
        self.extracted_file_list = []
        self.done_file_amount = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # print(QStyleFactory.keys())
    QApplication.setStyle(QStyleFactory.create("fusion"))

    w = MainWidget()
    w.setFixedSize(580, 380)
    # w.setWindowIcon(QIcon("./favicon.ico"))
    w.setWindowTitle("RamanSpectrumProcessor")
    w.show()

    app.exec()