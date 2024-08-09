import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QLabel, QSizePolicy
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtCore import Qt
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo

'''
================================================================
GUI oluşturulurken PyQt5 ve OpenGL kullanılmıştır.
OpenGL için "pip install PyOpenGL PyOpenGL_accelerate" komutu ile ilgili kütüphaneler yüklenmiştir.
PyQt5 diğer sürümlere göre en kararlı sürüm olduğu için kullanıldı.

2 farklı class yapısı oluşturuldu. (GLWidget ve MainWindow)
GLWidget class yapısı sadece widget şeklinde modellemenin gösterilmesi için kullanılmıştır. İlgili açıklamalar class içerisine eklenmiştir.

3D modellemenin daha akıcı bir şekilde gözlemlenebilmesi için Vertex Buffer Object (VBO) kullanıldı.
Vertex Buffer Object, OpenGL tarafından sunulmuş olan ve görselleştirmeyi GPU üzerinde yapan bir özelliktir.
================================================================

'''

class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.points = np.array([])  ## Nokta verileri
        self.colors = np.array([])  ## Renk verileri
        self.vbo = None ## vbo 
        self.last_pos = None  ## son mouse pozisyonu
        self.x_deg = -90 * 16  ## X ekseni rotasyon derecesi 
        self.y_deg = 0  ## Y ekseni rotasyon derecesi
        self.z_deg = 0  ## Z ekseni rotasyon derecesi


    ## nokta verilerinin ayarlanması için set_points fonksiyonu
    def set_points(self, points):
        ## noktaların ekrana sığması için normalize edilmesi
        self.points = points - np.mean(points, axis=0) ## merkezeleme (mean centering) işlemi
        ## mean centering işlemi vektörel olarak her bir vektörden ortalamanın çıkarılmasıyla elde edilmiştir.
        self.points /= np.max(np.abs(self.points), axis=0) ## ölçekleme (scaling) işlemi
        ## scaling işlemi her bir verinin vektörel olarak mutlak max'a bölümü ile elde edilmiştir
        
        ## z indexine göre renklendirme yapılması
        ## modellemeye derinlik katmak için yapıldı
        z_values = self.points[:, 2]
        z_min, z_max = np.min(z_values), np.max(z_values)
        z_normalized = (z_values - z_min) / (z_max - z_min)
        self.colors = np.array([[0.6 + 0.4 * z, 0.3 + 0.3 * z, 0.1, 1.0] for z in z_normalized], dtype=np.float32)

        ## GPU üzerinde modellemenin yapılması için VBO'nun güncellenmesi
        data = np.hstack((self.points, self.colors)).astype(np.float32) ## nokta ve renk verilerinin birleştirilmesi
        if self.vbo:
            self.vbo.delete() ## herhangi bir vbo daha önce atanmışsa silinmesi işlemi
        self.vbo = vbo.VBO(data) ## güncel data ile VBO nun oluşturulması
        self.update() ## modelin güncellenmesi

    ## modelin initialize edilmesi
    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)  ## siyah arka plan
        # glEnable(GL_DEPTH_TEST)  ## derinlik testinin etkinleştirilmesi
        glEnable(GL_BLEND) ## derinlik ve saydamlık için BLEND özelliğinin aktif edilmesi
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  ## alpha değerine göre fonksiyonun güncellenmesi
        glPointSize(5.0)  # nokta boyutunun ayarlanması 

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  ## derinlik ve renk özelliklerinin sıfırlanması
        glLoadIdentity() ## model matrisinin sıfırlanması -- identity matrix ile
        
        ## Kameranın pozisyonu
        gluLookAt(2, 0, 0, 0, 0, 0, 0, -1, 0)
        ## X eksenine 2 birim uzaklıkta kamera açıklığı olacak şekilde ayarlandı.
        ## Z ekseni ekrana dikey olarak paralel olacak şekilde ayarlandı.
        ## Bu ayarlar ile kamera sağdan modeli görecek şekilde başlangıç pozisyonu elde edildi.

        ## Modelin dönderilmesi
        glRotatef(self.x_deg / 16.0, 1.0, 0.0, 0.0)
        glRotatef(self.y_deg / 16.0, 0.0, 1.0, 0.0)
        glRotatef(self.z_deg / 16.0, 0.0, 0.0, 1.0)

        if self.points.size:
            self.vbo.bind()  #3 VBO'nun bağlanması
            glEnableClientState(GL_VERTEX_ARRAY)  ## Vertex array'in point görselleştirilmesi için aktif edilmesi
            glEnableClientState(GL_COLOR_ARRAY)  ## Renk array'in renk görselleştirilmesi için aktif edilmesi
            ## Vertex pointer ayarlanması
            glVertexPointer(3, GL_FLOAT, 7 * self.points.itemsize, self.vbo) 
            ## Açıklama :: 4 parametre --> (3 adet veri, veri tipi, verilerin atlanarak döngü halinde alınması (atlanacak veri), vbo parametresi)
            ## Renk pointer ayarlanması
            glColorPointer(4, GL_FLOAT, 7 * self.points.itemsize, self.vbo + 3 * self.points.itemsize) 
            ## Açıklama :: 4 parametre --> (4 adet veri (rgba), veri tipi, verilerin atlanarak döngü halinde alınması (atlanacak veri), vbo parametresi)
            glDrawArrays(GL_POINTS, 0, len(self.points)) ## Noktaların çizilmesi
            self.vbo.unbind()  ## VBO'nun unbind edilmesi
            glDisableClientState(GL_COLOR_ARRAY)  ## Renk array disable işlemi
            glDisableClientState(GL_VERTEX_ARRAY) ## Vertex array disable işlemi
        
        ## Eksenlerin çizilmesi 
        self.draw_axes() 

    def draw_axes(self):
        
        '''
        Eksenlerin çizgi şeklinde görselleştirilmesi
        X - kırmızı
        Y - yeşil
        Z - mavi
        '''
        
        glBegin(GL_LINES)
        
        # X ekseni - kırmızı
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(-1.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)

        # Y ekseni - yeşil
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)

        # Z ekseni - mavi
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, -1.0)
        glVertex3f(0.0, 0.0, 1.0)
        
        glEnd()


    ## built in resizeGL fonksiyonu
    ## model ilk oluşturulduğunda veya yeniden boyutlandırıldığında bu fonksiyon kullanılır
    def resizeGL(self, w, h): 
        ## w -- pencere genişliği
        ## h -- pencere yüksekliği
        glViewport(0, 0, w, h)  ## custom pencere içerisinde tepe ve sol noktalara 0 px uzaklıkta pencere büyüklüğü boyutunca ayarlanması
        ## diğer resize built-in ayarları
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 50.0)  ## perspektif verilmesi
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    ## mouse son pozisyonunun güncellenmesi
    def mousePressEvent(self, event):
        self.last_pos = event.pos()

    ## mouse hareketi ile son pozisyonun güncellenmesi
    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_pos.x()  # X eksenindeki fare hareketi
        dy = event.y() - self.last_pos.y()  # Y eksenindeki fare hareketi

        if event.buttons() & Qt.LeftButton:
            self.x_deg += 8 * dy
            self.y_deg += 8 * dx
        elif event.buttons() & Qt.RightButton:
            self.z_deg += 8 * dx

        self.last_pos = event.pos()  # Son fare pozisyonunu güncelle
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("3D Model Görüntüleme Aracı")  # Pencere başlığı
        self.setGeometry(200, 200, 800, 600)  # Pencerenin konumu ve boyutları

        self.gl_widget = GLWidget(self)  ## GLWidget oluşturulması

        ## Legend yapısı
        legend_x = QLabel()
        legend_x.setText("<font color='red'>------- X ekseni</font>")
        legend_y = QLabel()
        legend_y.setText("<font color='green'>------- Y ekseni</font>")
        legend_z = QLabel()
        legend_z.setText("<font color='blue'>------- Z ekseni</font>")

        # Legend'in boyutları (max 20 px)
        legend_x.setFixedHeight(20)
        legend_x.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        legend_y.setFixedHeight(20)
        legend_y.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        legend_z.setFixedHeight(20)
        legend_z.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Vertical layout oluşturulması
        layout = QVBoxLayout()
        layout.addWidget(self.gl_widget) ## modelin widget olarak eklenmesi
        layout.addWidget(legend_x)  ## legend e X eklenmesi
        layout.addWidget(legend_y)  ## legend e Y eklenmesi
        layout.addWidget(legend_z)  ## legend e Z eklenmesi

        container = QWidget()  ## main container widget
        container.setLayout(layout) ## layout un main container'e eklenmesi
        self.setCentralWidget(container)  # main container'in merkezi widget olarak ayarlanması

        self.load_data() ## güncel dataların yüklenilmesi

    def load_data(self):
        
        '''
        Verilerin csv formatında yüklenilmesi için dialog box açılması
        '''
        
        options = QFileDialog.Options() 
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)", options=options)
        if file_path:
            data = np.loadtxt(file_path, delimiter=';', skiprows=1) 
            print(data)  
            self.gl_widget.set_points(data)  

'''
Uygulamanın başlatılması ve ilgili kapatma fonksiyonlarının eklenmesi
'''

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
