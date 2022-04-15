from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout,QTabWidget,QPushButton,QHBoxLayout,QSlider,QStyle,QFileDialog,QCheckBox
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread,QUrl,QTime
import numpy as np
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import wave
import pyaudio
import  threading
import os
class AudioRecorder():

    # Audio class based on pyAudio and Wave
    def __init__(self):

        self.open = True
        self.rate = 44100
        self.frames_per_buffer = 1024
        self.channels = 2
        self.format = pyaudio.paInt16
        self.audio_filename = "temp_audio.wav"
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.frames_per_buffer)
        self.audio_frames = []

    # Audio starts being recorded
    def record(self):

        self.stream.start_stream()
        while (self.open == True):
            data = self.stream.read(self.frames_per_buffer)
            self.audio_frames.append(data)
            if self.open == False:
                break

    # Finishes the audio recording therefore the thread too
    def stop(self):

        if self.open == True:
            self.open = False
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()

            waveFile = wave.open(self.audio_filename, 'wb')
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(self.audio.get_sample_size(self.format))
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b''.join(self.audio_frames))
            waveFile.close()

        pass

    # Launches the audio recording function using a thread
    def start(self):
        audio_thread = threading.Thread(target=self.record)
        audio_thread.start()


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.logic=0
        self.path=""
        self.stoprecording=False

    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        frame_width=int(cap.get(3))
        frame_height=int(cap.get(4))
        codec=cv2.VideoWriter_fourcc(*'MP42')
        output = cv2.VideoWriter('Captured.avi', codec, 24.0, (640, 480))
        while self._run_flag:
            ret, cv_img = cap.read()

            if ret:
                self.change_pixmap_signal.emit(cv_img)
                # cv2.imwrite(os.path.join('C:/Users/ehian/Pictures', 'image.jpg'), cv_img)
                # print("image collected")
                if self.logic==1:
                    print("test")
                    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                    cv2.imwrite('image.jpg',cv_img,[cv2.IMWRITE_JPEG_QUALITY,100])
                    print("image collected")
                    cv2.imshow('Your picture', cv_img)
                    self.logic == 0
                    if (cv2.waitKey(1) & 0xFF == ord('x')):
                        self.logic == 0
                        break
                if self.logic==2:
                    self.stoprecording=False
                    cv_img=cv2.resize(cv_img,(640,480))
                    rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                    output.write(cv_img)
                    cv2.imshow('Video',cv_img)
                    if(cv2.waitKey(1) & 0xFF== ord('x')):
                        self.logic == 0
                        break


        # shut down capture system
        cap.release()



    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
    def setpath(self,path):
        self.path=""
    def setlogic(self,logic):
        self.logic=logic
    def state(self,logic):
        self.logic=logic
    def stprcrd(self):
        self.stoprecording =True
class App(QTabWidget):
    def __init__(self):
        super().__init__()
        self.layout=QVBoxLayout(self)
        self.id=0
        self.rcrd=False
        self.disply_width = 640
        self.display_height = 480
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.tabs=QTabWidget()
        self.centralWidget = QWidget(self)
        self.play = QPushButton()
        self.play.setEnabled(False)
        self.setWindowTitle('Main Window')
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.label_img = QLabel(self)
        self.label_img.resize(640, 400)
        self.tab1UI()
        self.tab2UI()
        self.tab3UI()

        self.tabs.addTab(self.tab2, "Video recorder")
        self.tabs.addTab(self.tab1, "Media player")
        self.tabs.addTab(self.tab3, "Audio Recorder")

        self.tabs.resize(680, 400)
        self.layout.addWidget(self.tabs)


        # create a vertical box layout and add the two labels


        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def tab1UI(self):
        self.mediaplayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.videowidget = QVideoWidget()
        self.open = QPushButton("Open Video", self)
        self.mediaplayer.setVideoOutput(self.videowidget)
        self.videowidget.setGeometry(self.pos().x(), self.pos().y(), self.width(), self.height())
        Hor_box = QHBoxLayout()
        Hor_box.setContentsMargins(0, 0, 0, 0)

        ver_box = QVBoxLayout()
        ver_box.addWidget(self.videowidget)

        self.play.clicked.connect(lambda checked: self.Vplay())
        Hor_box.addWidget(self.open)
        self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        Hor_box.addWidget(self.play)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        Hor_box.addWidget(self.slider)
        ver_box.addLayout(Hor_box)
        self.open.clicked.connect(lambda checked: self.open_video())
        self.mediaplayer.stateChanged.connect(self.onstatechanged)
        self.mediaplayer.positionChanged.connect(lambda checked: self.onmove)
        self.mediaplayer.durationChanged.connect(self.duration)
        self.slider.sliderMoved.connect(self.setposition)

        # self.layout.addWidget(self.tabs)
        self.tab1.setLayout(ver_box)
    def open_video(self):
        file, _ = QFileDialog.getOpenFileName(self,"Open Video")
        print(file)
        if file != '':
            self.mediaplayer.setMedia(QMediaContent(QUrl.fromLocalFile(file)))

            self.play.setEnabled(True)



    def Vplay(self):
        if self.mediaplayer.state() == QMediaPlayer.PlayingState:
            self.mediaplayer.pause()
            print("pause")
        else:
            self.mediaplayer.play()
            print("play")
    def onstatechanged(self,state):
        if self.mediaplayer.state() == QMediaPlayer.PlayingState:
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def onmove(self,position):
        self.slider.setValue(position)
    def duration(self,duration):
        self.slider.setRange(0,duration)
        mtime=QTime(0,0,0,0)
        mtime=mtime.addMSecs(self.mediaplayer.duration())

        print(duration)
    def setposition(self,position):
        self.mediaplayer.setPosition(position)

    def tab2UI(self):

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        dir=QPushButton('Select directory')
        stop=QPushButton('Restart recording')
        pic = QPushButton('Take a picture')
        self.video = QPushButton()
        self.video.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        hbox= QHBoxLayout()
        hbox.addWidget(dir)
        hbox.addWidget(stop)
        hbox.addWidget(pic)
        hbox.addWidget(self.video)
        stop.clicked.connect(self.test)
        vbox.addLayout(hbox)
        dir.clicked.connect(self.locate)
        pic.clicked.connect(self.capture)
        self.video.clicked.connect(self.rec)

        # set the vbox layout as the widgets layout

        self.tab2.setLayout(vbox)

    def tab3UI(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("subjects"))
        layout.addWidget(QCheckBox("Physics"))
        layout.addWidget(QCheckBox("Maths"))
        self.setTabText(2, "Education Details")
        self.tab3.setLayout(layout)
    def test(self):
        self.thread.start()
    def locate(self):
        pth = QFileDialog.getExistingDirectory(self, "Choose where your pictures and videos will be stored")
        if pth:
            self.path=pth
            self.thread.setpath(self.path)
    def logic(self,logic):
        self.id=logic
        self.thread.state(self.id)
    def capture(self):
        self.id=1
        self.thread.setlogic(self.id)
    def rec(self):
        if self.rcrd==False:
            self.thread.setlogic(2)
            self.rcrd=True
            self.video.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.thread.stprcrd()
            self.thread.setlogic(0)
            self.rcrd=False
            self.video.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
app = QApplication(sys.argv)
a = App()
a.show()
sys.exit(app.exec_())