import sys, cv2, mysql.connector, pickle, numpy as np, os, shutil, json
from datetime import datetime, date, time

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from insightface.app import FaceAnalysis

# ==================== KONFIGURASI DASAR ====================

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'aiot'
}

# --- KONFIGURASI PENYIMPANAN FOTO KE LARAVEL ---
# GANTI PATH DI BAWAH INI SESUAI LOKASI PROYEK ANDA!
# Pastikan folder 'kehadiran' sudah dibuat di storage/app/public/
LARAVEL_STORAGE_PATH = r"C:\xampp\htdocs\belajar_laravel\storage\app\public\kehadiran"

# Buat folder otomatis jika belum ada (safety check)
if not os.path.exists(LARAVEL_STORAGE_PATH):
    try:
        os.makedirs(LARAVEL_STORAGE_PATH)
    except Exception as e:
        print(f"Warning: Gagal membuat folder {LARAVEL_STORAGE_PATH}. Error: {e}")

ADMIN_PASSWORD = "admin123"

JAM_MASUK_MULAI = time(8, 0)
JAM_MASUK_AKHIR = time(20, 0)
JAM_TELAT = time(10, 0)
JAM_PULANG_MINIMAL = time(20, 0)

DATASET_FOLDER = "database_wajah"
NUM_PHOTOS = 5
FRAME_SKIP = 2
STATUS_RESET_TIME = 5000

# Global Variables
face_engine = None
face_db = {}
db_pool = None
executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="BG")


# ==================== FACE ENGINE INSIGHTFACE ====================

class FaceEngine:
    def __init__(self, threshold=0.60):
        print("Inisialisasi InsightFace...")
        self.app = FaceAnalysis(name="buffalo_l")
        # coba GPU dulu, jika gagal fallback ke CPU (ctx_id=-1)
        try:
            self.app.prepare(ctx_id=0, det_size=(640, 640))
        except Exception as e:
            print("GPU tidak tersedia, fallback ke CPU:", e)
            self.app.prepare(ctx_id=-1, det_size=(640, 640))
        self.threshold = float(threshold)
        print("InsightFace siap. Model:", self.app.models.keys())

    def detect_faces(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        faces = self.app.get(frame_rgb)
        return faces

    def get_embedding(self, face):
        emb = face.normed_embedding
        emb = emb.astype("float32")
        return emb

    def compute_centroid(self, embeddings):
        if len(embeddings) == 0:
            return None
        arr = np.stack(embeddings, axis=0)
        center = arr.mean(axis=0)
        norm = np.linalg.norm(center)
        if norm > 0:
            center = center / norm
        return center.astype("float32")

    def match(self, emb, db):
        best_nim = None
        best_info = None
        best_score = -1.0

        for nim, item in db.items():
            centroid = item.get("centroid")
            if centroid is None:
                continue
            score = float(np.dot(emb, centroid))
            if score > best_score:
                best_score = score
                best_nim = nim
                best_info = item.get("info")

        if best_nim is not None and best_score >= self.threshold:
            return best_info, best_score
        return None, best_score


# ==================== DATABASE POOL ====================

class DatabasePool:
    def __init__(self, size=5):
        self.pool = Queue(maxsize=size)
        for _ in range(size):
            try:
                conn = mysql.connector.connect(**DB_CONFIG, autocommit=True)
                self.pool.put(conn)
            except Exception as e:
                print("Gagal buat koneksi awal:", e)

    def get_connection(self, timeout=2):
        try:
            return self.pool.get(timeout=timeout)
        except:
            try:
                return mysql.connector.connect(**DB_CONFIG, autocommit=True)
            except:
                return None

    def return_connection(self, conn):
        if conn:
            try:
                self.pool.put_nowait(conn)
            except:
                try:
                    conn.close()
                except:
                    pass

    def close_all(self):
        while True:
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                break


# ==================== STORAGE MANAGER ====================

class StorageManager:
    @staticmethod
    def init():
        if not os.path.exists(DATASET_FOLDER):
            os.makedirs(DATASET_FOLDER)

    @staticmethod
    def get_student_folder(nim):
        folder = os.path.join(DATASET_FOLDER, f"{nim}")
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    @staticmethod
    def save_student_data(nim, nama, pbl, embeddings, frames):
        folder = StorageManager.get_student_folder(nim)

        info = {
            'nim': nim,
            'nama': nama,
            'pbl': pbl,
            'terdaftar': datetime.now().isoformat(),
            'num_emb': len(embeddings)
        }

        # hitung centroid
        centroid = None
        if len(embeddings) > 0:
            arr = np.stack(embeddings, axis=0)
            center = arr.mean(axis=0)
            norm = np.linalg.norm(center)
            if norm > 0:
                center = center / norm
            centroid = center.astype("float32")

        enc_data = {
            'info': info,
            'centroid': centroid
        }

        with open(os.path.join(folder, 'encodings.pkl'), 'wb') as f:
            pickle.dump(enc_data, f)

        for i, frame in enumerate(frames[:NUM_PHOTOS], 1):
            cv2.imwrite(os.path.join(folder, f'photo_{i}.jpg'), frame)

        return True

    @staticmethod
    def load_all_students():
        global face_db
        face_db = {}

        if not os.path.exists(DATASET_FOLDER):
            return face_db

        try:
            for folder in os.listdir(DATASET_FOLDER):
                folder_path = os.path.join(DATASET_FOLDER, folder)
                if not os.path.isdir(folder_path):
                    continue

                enc_file = os.path.join(folder_path, 'encodings.pkl')
                if not os.path.exists(enc_file):
                    continue

                try:
                    with open(enc_file, 'rb') as f:
                        enc_data = pickle.load(f)
                    info = enc_data.get('info', {})
                    centroid = enc_data.get('centroid', None)

                    nim = info.get('nim', folder)
                    if centroid is not None:
                        centroid = np.array(centroid, dtype="float32")
                        face_db[nim] = {
                            'info': info,
                            'centroid': centroid
                        }
                except Exception as e:
                    print(f"Gagal load {folder}: {e}")
        except Exception as e:
            print(f"Error load_all_students: {e}")

        return face_db

    @staticmethod
    def delete_student_folder(nim):
        folder = os.path.join(DATASET_FOLDER, nim)
        if os.path.exists(folder):
            shutil.rmtree(folder)
            return True
        return False

    @staticmethod
    def get_student_folder_exists(nim):
        folder = os.path.join(DATASET_FOLDER, nim)
        return os.path.exists(folder)


# ==================== LOAD THREAD ====================

class LoadThread(QThread):
    finished = pyqtSignal()

    def run(self):
        global face_engine, face_db
        try:
            # db_pool harus sudah diinisialisasi di main thread sebelum LoadThread start
            if face_engine is None:
                globals()['face_engine'] = FaceEngine(threshold=0.35)

            StorageManager.init()
            face_db = StorageManager.load_all_students()
            print(f"Loaded {len(face_db)} user centroid.")
        except Exception as e:
            print(f"Error load: {e}")

        self.finished.emit()


# ==================== VIDEO THREAD ====================

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    # UPDATE: Menambahkan np.ndarray di signal untuk mengirim frame gambar
    face_detected_signal = pyqtSignal(str, str, str, str, np.ndarray)
    unknown_face_signal = pyqtSignal()
    no_face_signal = pyqtSignal()
    countdown_signal = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.is_paused = False
        self.recently_processed = {}
        self.frame_count = 0
        self.processing_queue = Queue(maxsize=2)
        self.face_present = False
        self.face_start_time = None
        self.last_face_time = datetime.now()
        self.last_absen_time = datetime.min

        for _ in range(2):
            t = threading.Thread(target=self.process_worker, daemon=True)
            t.start()

    def run(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print("Kamera aktif")

        while self._run_flag:
            ret, frame = cap.read()
            if not ret:
                continue

            self.frame_count += 1
            display_frame = self.draw_frame_info(frame.copy())
            self.change_pixmap_signal.emit(display_frame)

            if not self.is_paused and self.frame_count % FRAME_SKIP == 0:
                now = datetime.now()
                waktu = now.time()

                if JAM_MASUK_MULAI <= waktu <= JAM_MASUK_AKHIR:
                    mode = 'masuk'
                elif JAM_MASUK_AKHIR < waktu < JAM_PULANG_MINIMAL:
                    mode = 'none'
                elif waktu >= JAM_PULANG_MINIMAL:
                    mode = 'pulang'
                else:
                    mode = 'none'

                try:
                    self.processing_queue.put_nowait((frame.copy(), mode))
                except:
                    pass

        cap.release()
        for _ in range(2):
            try:
                self.processing_queue.put_nowait(None)
            except:
                pass

    def draw_frame_info(self, frame):
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, f"Frame: {self.frame_count}", (10, 30),
                    font, 0.6, (0, 255, 0), 1)
        return frame

    def process_worker(self):
        while self._run_flag:
            try:
                frame_data = self.processing_queue.get(timeout=0.1)
                if frame_data is None:
                    break
                frame, mode = frame_data
                self.process_attendance(frame, mode)
            except:
                continue

    def process_attendance(self, frame, mode):
        global face_engine, face_db

        if (datetime.now() - self.last_absen_time).total_seconds() < 3:
            return

        if face_engine is None or not face_db:
            return

        faces = face_engine.detect_faces(frame)

        if len(faces) == 0:
            if self.face_present:
                self.no_face_signal.emit()
            self.face_present = False
            self.face_start_time = None
            return

        if len(faces) > 1:
            self.face_present = False
            self.face_start_time = None
            self.no_face_signal.emit()
            QMetaObject.invokeMethod(
                QApplication.instance().activeWindow(),
                "show_multiple_faces_warning",
                Qt.QueuedConnection
            )
            return

        if not self.face_present:
            self.face_present = True
            self.face_start_time = datetime.now()
            return

        elapsed = (datetime.now() - self.face_start_time).total_seconds()
        if elapsed < 3:
            remaining = 3 - elapsed
            self.countdown_signal.emit(remaining)
            return

        face = faces[0]
        emb = face_engine.get_embedding(face)
        if emb is None:
            return

        result, score = face_engine.match(emb, face_db)

        if result:
            nim = result.get('nim')
            nama = result.get('nama')
            pbl = result.get('pbl')
            now = datetime.now()

            if nim in self.recently_processed:
                diff = (now - self.recently_processed[nim]).total_seconds()
                if diff < 10:
                    return

            self.recently_processed[nim] = now
            # UPDATE: Mengirim frame asli untuk bukti foto
            self.face_detected_signal.emit(nim, nama, pbl, mode, frame.copy())
            self.last_absen_time = now
        else:
            self.unknown_face_signal.emit()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self._run_flag = False
        self.wait(3000)


# ==================== MAIN WINDOW (FIXED) ====================

class MainWindow(QMainWindow):
    reload_face_db_signal = pyqtSignal()

    # Signals UI-thread safe
    attendance_result_signal = pyqtSignal(str, str)  # message, color_hex
    dashboard_info_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistem Absensi Face Recognition")
        self.setGeometry(0, 0, 1366, 768)
        self.showMaximized()

        self.video_thread = VideoThread()
        self.video_thread.change_pixmap_signal.connect(self.update_image, Qt.QueuedConnection)
        self.video_thread.face_detected_signal.connect(self.handle_face_detection, Qt.QueuedConnection)
        self.video_thread.unknown_face_signal.connect(self.handle_unknown_face, Qt.QueuedConnection)
        self.video_thread.no_face_signal.connect(self.handle_no_face, Qt.QueuedConnection)
        self.video_thread.countdown_signal.connect(self.update_countdown_label, Qt.QueuedConnection)

        self.reset_status_timer = QTimer()
        self.reset_status_timer.timeout.connect(self.reset_status_bar)
        self.reset_status_timer.setSingleShot(True)

        self.reload_face_db_signal.connect(self.do_reload_face_db, Qt.QueuedConnection)

        self.attendance_result_signal.connect(self.on_attendance_saved, Qt.QueuedConnection)
        self.dashboard_info_signal.connect(self.on_info_updated, Qt.QueuedConnection)

        self.load_thread = None

        self.init_ui()

        self.load_thread = LoadThread()
        self.load_thread.finished.connect(self.on_load_finished, Qt.QueuedConnection)
        self.load_thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def on_load_finished(self):
        print("Loading selesai")
        self.video_thread.start()
        self.update_time()
        self.reset_status_bar()
        self.update_info()

    @pyqtSlot(str, str)
    def on_attendance_saved(self, message, color_hex):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"background-color: {color_hex}; padding: 10px; color: white; border-radius: 8px;")
        # hanya start timer untuk pesan bukan pesan progress/warning sederhana
        self.reset_status_timer.start(STATUS_RESET_TIME)

    @pyqtSlot(str)
    def on_info_updated(self, text):
        self.info_label.setText(text)

    @pyqtSlot()
    def show_multiple_faces_warning(self):
        self.on_attendance_saved("Terdeteksi lebih dari satu wajah. Harap hanya satu orang di depan kamera.", "#E74C3C")
        self.reset_status_timer.start(STATUS_RESET_TIME)

    def do_reload_face_db(self):
        print("Reload data wajah...")
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.wait(500)

        self.load_thread = LoadThread()
        self.load_thread.finished.connect(self.on_load_finished, Qt.QueuedConnection)
        self.load_thread.start()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)

        header = QFrame()
        header.setStyleSheet("QFrame { background: #003366; padding: 15px; border-radius: 10px; } QLabel { color: white; }")
        header_layout = QHBoxLayout()

        logo = QLabel("🎓")
        logo.setFont(QFont('Arial', 40))
        header_layout.addWidget(logo)

        title = QLabel("SISTEM ABSENSI FACE RECOGNITION\nAiOT Simalas")
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title, 1)

        self.time_label = QLabel()
        self.time_label.setFont(QFont('Arial', 28, QFont.Bold))
        self.time_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.time_label)

        header.setLayout(header_layout)
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        video_container = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setMinimumSize(850, 480)
        self.video_label.setMaximumHeight(480)
        self.video_label.setStyleSheet("background-color: #000; border: 4px solid #3498DB; border-radius: 10px;")
        self.video_label.setAlignment(Qt.AlignCenter)
        video_container.addWidget(self.video_label)

        self.status_label = QLabel("Loading sistem...")
        self.status_label.setFont(QFont('Arial', 13, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setMinimumHeight(45)
        self.status_label.setStyleSheet("background-color: #F39C12; padding: 10px; color: white; border-radius: 8px;")
        video_container.addWidget(self.status_label)

        content_layout.addLayout(video_container, 7)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)

        mode_group = QGroupBox("MODE")
        mode_layout = QVBoxLayout()
        self.mode_label = QLabel("Loading...")
        self.mode_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setMinimumHeight(40)
        self.mode_label.setStyleSheet("background-color: #3498DB; padding: 10px; border-radius: 6px; color: white;")
        mode_layout.addWidget(self.mode_label)
        mode_group.setLayout(mode_layout)
        right_panel.addWidget(mode_group)

        info_group = QGroupBox("INFO")
        info_layout = QVBoxLayout()
        self.info_label = QLabel("Loading...")
        self.info_label.setFont(QFont('Arial', 11))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("background-color: #34495E; padding: 10px; border-radius: 6px; color: white;")
        info_layout.addWidget(self.info_label)
        info_group.setLayout(info_layout)
        right_panel.addWidget(info_group)

        jam_group = QGroupBox("JAM KERJA")
        jam_layout = QVBoxLayout()
        jam_text = f"Masuk: {JAM_MASUK_MULAI.strftime('%H:%M')}-{JAM_MASUK_AKHIR.strftime('%H:%M')}\n"
        jam_text += f"Telat: {JAM_TELAT.strftime('%H:%M')}\n"
        jam_text += f"Pulang: {JAM_PULANG_MINIMAL.strftime('%H:%M')}"
        jam_label = QLabel(jam_text)
        jam_label.setFont(QFont('Arial', 10))
        jam_label.setStyleSheet("background-color: #34495E; padding: 10px; border-radius: 6px; color: white;")
        jam_layout.addWidget(jam_label)
        jam_group.setLayout(jam_layout)
        right_panel.addWidget(jam_group)

        right_panel.addStretch()
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        btn_manage = QPushButton("KELOLA DATA")
        btn_manage.setMinimumHeight(50)
        btn_manage.clicked.connect(self.open_manage)
        btn_layout.addWidget(btn_manage)

        btn_exit = QPushButton("KELUAR")
        btn_exit.setMinimumHeight(50)
        btn_exit.clicked.connect(self.confirm_exit)
        btn_layout.addWidget(btn_exit)
        right_panel.addLayout(btn_layout)

        content_layout.addLayout(right_panel, 3)
        main_layout.addLayout(content_layout)
        central_widget.setLayout(main_layout)

        self.update_time()

    def reset_status_bar(self):
        self.status_label.setText("Sistem Siap")
        self.status_label.setStyleSheet("background-color: #27AE60; padding: 10px; color: white; border-radius: 8px;")

    @pyqtSlot()
    def handle_unknown_face(self):
        self.on_attendance_saved("Wajah tidak dikenal. Silakan registrasi", "#E74C3C")
        self.reset_status_timer.start(STATUS_RESET_TIME)

    @pyqtSlot(float)
    def update_countdown_label(self, remaining):
        self.status_label.setText(f"Wajah terdeteksi, harap diam... ({remaining:.1f}s)")
        self.status_label.setStyleSheet("background-color: #F39C12; padding: 10px; color: white; border-radius: 8px;")

    @pyqtSlot()
    def handle_no_face(self):
        self.reset_status_bar()

    def update_time(self):
        now = datetime.now()
        self.time_label.setText(now.strftime('%H:%M:%S'))
        self.update_mode_auto()

    def update_mode_auto(self):
        now = datetime.now()
        waktu = now.time()

        if JAM_MASUK_MULAI <= waktu <= JAM_MASUK_AKHIR:
            self.mode_label.setText("ABSEN MASUK")
            self.mode_label.setStyleSheet("background-color: #27AE60; padding: 10px; border-radius: 6px; color: white;")
        elif waktu >= JAM_PULANG_MINIMAL:
            self.mode_label.setText("ABSEN PULANG")
            self.mode_label.setStyleSheet("background-color: #E67E22; padding: 10px; border-radius: 6px; color: white;")
        else:
            self.mode_label.setText("DI LUAR JAM")
            self.mode_label.setStyleSheet("background-color: #95A5A6; padding: 10px; border-radius: 6px; color: white;")

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        try:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            scaled = qt_img.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(QPixmap.fromImage(scaled))
        except:
            pass

    # UPDATE: Menerima frame untuk disimpan
    @pyqtSlot(str, str, str, str, np.ndarray)
    def handle_face_detection(self, nim, nama, pbl, mode, frame):
        self.reset_status_timer.stop()
        executor.submit(self.save_attendance_to_db, nim, nama, pbl, mode, frame)
        self.on_attendance_saved(f"Memproses {nama}...", "#F39C12")

    # UPDATE: Logic simpan foto ke folder Laravel
    def save_attendance_to_db(self, nim, nama, pbl_lama, mode, frame_img):
        conn = None
        try:
            conn = db_pool.get_connection(timeout=2)
            if not conn:
                self.attendance_result_signal.emit("Database tidak tersedia", "#C0392B")
                return

            cursor = conn.cursor()
            now = datetime.now()
            today = date.today()

            cursor.execute("SELECT PBL FROM user WHERE NIM = %s", (nim,))
            user_data = cursor.fetchone()
            
            if user_data:
                pbl_fix = user_data[0]
            else:
                pbl_fix = pbl_lama

            if mode == 'none':
                db_pool.return_connection(conn)
                self.attendance_result_signal.emit("Sekarang di luar jam absensi", "#95A5A6")
                return

            if mode == 'masuk':
                cursor.execute("""
                    SELECT id FROM absen 
                    WHERE NIM = %s AND tanggal = %s AND absen_hadir IS NOT NULL
                """, (nim, today))

                if cursor.fetchone():
                    db_pool.return_connection(conn)
                    self.attendance_result_signal.emit(f"{nama} sudah absen masuk", "#F39C12")
                    return

                # --- FITUR BUKTI FOTO ---
                filename = f"{nim}_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
                save_path = os.path.join(LARAVEL_STORAGE_PATH, filename)
                
                # Simpan gambar
                try:
                    cv2.imwrite(save_path, frame_img)
                except Exception as e:
                    print(f"Gagal simpan foto: {e}")

                # Path relatif untuk database
                db_foto_path = f"kehadiran/{filename}"
                # ------------------------

                status_masuk = "Tepat Waktu" if now.time() <= JAM_TELAT else "Terlambat"

                cursor.execute("""
                    INSERT INTO absen 
                    (NIM, Nama, PBL, absen_hadir, tanggal, status_kehadiran, status_masuk, bukti_foto) 
                    VALUES (%s, %s, %s, %s, %s, 'Hadir', %s, %s)
                """, (nim, nama, pbl_fix, now, today, status_masuk, db_foto_path))

                db_pool.return_connection(conn)
                self.attendance_result_signal.emit(f"{nama} - {status_masuk} (Foto Tersimpan)", "#27AE60")

            elif mode == 'pulang':
                if now.time() < JAM_PULANG_MINIMAL:
                    db_pool.return_connection(conn)
                    self.attendance_result_signal.emit(f"Belum waktunya pulang ({now.strftime('%H:%M:%S')})", "#C0392B")
                    return

                cursor.execute("""
                    SELECT absen_hadir, absen_pulang FROM absen 
                    WHERE NIM = %s AND tanggal = %s
                """, (nim, today))
                result = cursor.fetchone()

                if not result or not result[0]:
                    db_pool.return_connection(conn)
                    self.attendance_result_signal.emit(f"{nama} belum absen masuk", "#C0392B")
                    return

                if result[1]:
                    db_pool.return_connection(conn)
                    self.attendance_result_signal.emit(f"{nama} sudah absen pulang", "#F39C12")
                    return

                durasi = (now - result[0]).total_seconds() / 3600

                cursor.execute("""
                    UPDATE absen 
                    SET absen_pulang = %s, durasi_kerja = %s
                    WHERE NIM = %s AND tanggal = %s
                """, (now, durasi, nim, today))

                db_pool.return_connection(conn)
                self.attendance_result_signal.emit(f"{nama} pulang ({durasi:.1f} jam)", "#E67E22")

            self.update_info()

        except Exception as e:
            print(f"Error save: {e}")
            self.attendance_result_signal.emit(f"Error save: {str(e)}", "#C0392B")
            try:
                if conn: db_pool.return_connection(conn)
            except:
                pass

    def update_info(self):
        executor.submit(self._update_info)

    def _update_info(self):
        conn = None
        try:
            conn = db_pool.get_connection(timeout=2)
            if not conn:
                return

            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM user")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM absen WHERE tanggal = %s", (date.today(),))
            hadir = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM absen 
                WHERE tanggal = %s AND absen_pulang IS NOT NULL
            """, (date.today(),))
            pulang = cursor.fetchone()[0]

            db_pool.return_connection(conn)

            text_info = f"Terdaftar: {total}\nHadir: {hadir}\nPulang: {pulang}"
            self.dashboard_info_signal.emit(text_info)

        except:
            if conn: db_pool.return_connection(conn)
            self.dashboard_info_signal.emit("Terdaftar: 0\nHadir: 0\nPulang: 0")

    def open_manage(self):
        password, ok = QInputDialog.getText(self, 'Password', 'Password admin:', QLineEdit.Password)
        if ok and password == ADMIN_PASSWORD:
            self.video_thread.pause()
            print("Video di pause")

            window = ManageWindow(self)
            result = window.exec_()

            if result == QDialog.Accepted:
                print("Reload data wajah")
                self.reload_face_db_signal.emit()

            self.video_thread.resume()
            print("Video di resume")
            self.update_info()
        elif ok:
            QMessageBox.critical(self, "Error", "Password salah")

    def confirm_exit(self):
        reply = QMessageBox.question(self, 'Konfirmasi', 'Keluar?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event):
        print("Menutup")

        if self.video_thread and self.video_thread.isRunning():
            self.video_thread._run_flag = False
            self.video_thread.wait(1000)

        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.wait(500)

        if db_pool:
            db_pool.close_all()

        print("Ditutup")
        event.accept()


# ==================== MANAGE WINDOW (UPDATED) ====================

class ManageWindow(QDialog):
    student_list_signal = pyqtSignal(list)
    search_result_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kelola Data Wajah")
        self.setGeometry(150, 80, 1100, 700)
        self.setModal(True)

        self.reg_thread = None
        self.management_success = False

        # Signal connections
        self.student_list_signal.connect(self.populate_list, Qt.QueuedConnection)
        self.search_result_signal.connect(self.handle_search_result, Qt.QueuedConnection)

        self.init_ui()

        # --- FITUR AUTO RELOAD MYSQL ---
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.load_students_list)
        self.auto_refresh_timer.start(5000) # 5000 ms = 5 detik

        # Load awal
        self.load_students_list()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("KELOLA DATA WAJAH")
        header.setFont(QFont('Arial', 22, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("background-color: #3498DB; padding: 15px; border-radius: 8px; color: white;")
        layout.addWidget(header)

        tabs = QTabWidget()
        tabs.addTab(self.create_register_tab(), "Registrasi")
        tabs.addTab(self.create_delete_tab(), "Hapus & Status")
        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("TUTUP")
        btn_close.setMinimumWidth(100)
        btn_close.setMinimumHeight(40)
        btn_close.clicked.connect(self.close)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def create_register_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        content = QHBoxLayout()

        self.video_label = QLabel()
        self.video_label.setMinimumSize(400, 500)
        self.video_label.setStyleSheet("background-color: black; border: 3px solid #3498DB;")
        content.addWidget(self.video_label, 5)

        controls = QVBoxLayout()

        form = QHBoxLayout()
        form.addWidget(QLabel("NIM:"))
        self.nim_input = QLineEdit()
        self.nim_input.setPlaceholderText("Ketik NIM lalu Enter...")
        self.nim_input.returnPressed.connect(self.search_student)
        form.addWidget(self.nim_input)
        
        btn_search = QPushButton("Cari")
        btn_search.setMaximumWidth(80)
        btn_search.clicked.connect(self.search_student)
        form.addWidget(btn_search)
        controls.addLayout(form)

        # Input Nama
        controls.addWidget(QLabel("Nama:"))
        self.nama_input = QLineEdit()
        self.nama_input.setPlaceholderText("Otomatis terisi dari DB")
        self.nama_input.setEnabled(False)
        controls.addWidget(self.nama_input)

        # Input PBL
        controls.addWidget(QLabel("PBL / Divisi:"))
        self.pbl_input = QLineEdit()
        self.pbl_input.setPlaceholderText("Otomatis terisi dari DB")
        self.pbl_input.setEnabled(False)
        controls.addWidget(self.pbl_input)

        self.info_label = QLabel("Masukkan NIM untuk memulai")
        self.info_label.setStyleSheet("background-color: #34495E; padding: 12px; color: white; border-radius: 4px;")
        self.info_label.setWordWrap(True)
        controls.addWidget(self.info_label)

        self.progress = QProgressBar()
        self.progress.setMaximum(NUM_PHOTOS)
        controls.addWidget(self.progress)

        self.status_label = QLabel("Siap")
        self.status_label.setMinimumHeight(45)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("background-color: #F39C12; padding: 10px; color: white; border-radius: 4px;")
        controls.addWidget(self.status_label)

        controls.addStretch()

        self.btn_start = QPushButton("Mulai Ambil Foto")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_capture)
        controls.addWidget(self.btn_start)

        self.btn_capture = QPushButton("Jepret Kamera")
        self.btn_capture.setMinimumHeight(40)
        self.btn_capture.setEnabled(False)
        self.btn_capture.clicked.connect(self.trigger_capture)
        controls.addWidget(self.btn_capture)

        self.btn_save = QPushButton("Simpan Dataset")
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet("background-color: #27AE60; font-weight: bold; color: white;")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_registration)
        controls.addWidget(self.btn_save)

        content.addLayout(controls, 5)
        layout.addLayout(content)
        w.setLayout(layout)
        return w

    def create_delete_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        header = QLabel("Daftar Mahasiswa di Database (MySQL)")
        header.setStyleSheet("background-color: #E74C3C; padding: 10px; color: white; border-radius: 4px;")
        layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        
        btn_refresh = QPushButton("Refresh List Manual")
        btn_refresh.clicked.connect(self.load_students_list)
        btn_layout.addWidget(btn_refresh)

        btn_delete = QPushButton("Hapus Folder Wajah")
        btn_delete.setStyleSheet("background-color: #C0392B; color: white; font-weight: bold;")
        btn_delete.clicked.connect(self.delete_student_folder)
        btn_layout.addWidget(btn_delete)
        
        layout.addLayout(btn_layout)

        w.setLayout(layout)
        return w

    def search_student(self):
        nim = self.nim_input.text().strip()
        if nim:
            self.status_label.setText("Mencari di Database...")
            self.status_label.setStyleSheet("background-color: #3498DB; padding: 10px; color: white;")
            executor.submit(self._search_student, nim)

    def _search_student(self, nim):
        try:
            conn = db_pool.get_connection(timeout=2)
            if not conn:
                self.search_result_signal.emit(None)
                return
            
            cursor = conn.cursor()
            cursor.execute("SELECT NIM, Nama, PBL FROM user WHERE NIM = %s", (nim,))
            result = cursor.fetchone()
            
            db_pool.return_connection(conn)
            self.search_result_signal.emit(result)
        except Exception as e:
            print(f"Search error: {e}")
            self.search_result_signal.emit(None)

    @pyqtSlot(object)
    def handle_search_result(self, result):
        if result:
            self.nama_input.setText(result[1])
            self.pbl_input.setText(result[2])
            
            self.info_label.setText(f"Data Ditemukan:\n{result[1]}\n({result[2]})")
            self.info_label.setStyleSheet("background-color: #27AE60; padding: 12px; color: white; border-radius: 4px;")
            
            self.btn_start.setEnabled(True)
            self.status_label.setText("Data Valid. Klik Mulai.")
            self.status_label.setStyleSheet("background-color: #27AE60; padding: 10px; color: white;")
        else:
            self.nama_input.clear()
            self.pbl_input.clear()
            self.info_label.setText("NIM tidak ditemukan di tabel user MySQL!")
            self.info_label.setStyleSheet("background-color: #C0392B; padding: 12px; color: white; border-radius: 4px;")
            
            self.status_label.setText("Tidak ditemukan")
            self.status_label.setStyleSheet("background-color: #E74C3C; padding: 10px; color: white;")
            self.btn_start.setEnabled(False)

    def start_capture(self):
        if not self.nim_input.text().strip():
            return

        self.reg_thread = RegistrationThread()
        self.reg_thread.student_data = {
            'nim': self.nim_input.text().strip(),
            'nama': self.nama_input.text().strip(),
            'pbl': self.pbl_input.text().strip()
        }
        self.reg_thread.change_pixmap_signal.connect(self.update_video, Qt.QueuedConnection)
        self.reg_thread.capture_success_signal.connect(self.on_capture_success, Qt.QueuedConnection)
        self.reg_thread.capture_error_signal.connect(self.on_capture_error, Qt.QueuedConnection)
        self.reg_thread.start()

        self.btn_start.setEnabled(False)
        self.nim_input.setEnabled(False)
        self.btn_capture.setEnabled(True)
        self.status_label.setText("Kamera Aktif. Silakan Jepret.")

    @pyqtSlot(np.ndarray)
    def update_video(self, cv_img):
        try:
            rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            scaled = qt_img.scaled(self.video_label.size(), Qt.KeepAspectRatio)
            self.video_label.setPixmap(QPixmap.fromImage(scaled))
        except:
            pass

    def trigger_capture(self):
        if self.reg_thread:
            self.reg_thread.trigger_capture()

    @pyqtSlot(int)
    def on_capture_success(self, count):
        self.progress.setValue(count)
        self.status_label.setText(f"Foto {count}/{NUM_PHOTOS} Terambil")
        if count >= NUM_PHOTOS:
            self.btn_capture.setEnabled(False)
            self.btn_save.setEnabled(True)
            self.status_label.setText("Foto Selesai. Klik Simpan.")
            self.status_label.setStyleSheet("background-color: #27AE60; padding: 10px; color: white;")

    @pyqtSlot(str)
    def on_capture_error(self, error):
        self.status_label.setText(error)

    def save_registration(self):
        if self.reg_thread:
            self.status_label.setText("Menyimpan data...")
            success, result = self.reg_thread.save_to_storage()
            if success:
                self.management_success = True
                QMessageBox.information(self, "Sukses", result)
                self.load_students_list() 
                self.accept()
            else:
                QMessageBox.critical(self, "Error", result)

    def load_students_list(self):
        executor.submit(self._load_students)

    def _load_students(self):
        try:
            conn = db_pool.get_connection(timeout=1)
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("SELECT NIM, Nama, PBL FROM user ORDER BY Nama")
            rows = cursor.fetchall()
            db_pool.return_connection(conn)

            self.student_list_signal.emit(rows)
        except:
            pass

    @pyqtSlot(list)
    def populate_list(self, rows):
        current_row = self.list_widget.currentRow()
        
        self.list_widget.clear()
        for nim, nama, pbl in rows:
            has_folder = StorageManager.get_student_folder_exists(nim)
            
            if has_folder:
                status_icon = "✅" 
                color = QColor("#27AE60")
            else:
                status_icon = "❌"
                color = QColor("#C0392B")

            item_text = f"{status_icon} {nim} - {nama} ({pbl})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, nim)
            item.setForeground(color)
            
            self.list_widget.addItem(item)
        
        if current_row >= 0 and current_row < self.list_widget.count():
            self.list_widget.setCurrentRow(current_row)

    def delete_student_folder(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "Peringatan", "Pilih user yang ingin dihapus datanya.")
            return

        nim = item.data(Qt.UserRole)
        if not StorageManager.get_student_folder_exists(nim):
            QMessageBox.information(self, "Info", "User ini memang belum memiliki data wajah.")
            return

        nama_display = item.text().split(" - ")[1]
        
        reply = QMessageBox.question(self, 'Konfirmasi Hapus', 
                                   f'Yakin ingin menghapus data wajah untuk:\n{nama_display}?',
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if StorageManager.delete_student_folder(nim):
                self.management_success = True
                QMessageBox.information(self, "Sukses", "Data wajah berhasil dihapus.")
                self.load_students_list() 
            else:
                QMessageBox.critical(self, "Error", "Gagal menghapus folder.")

    def closeEvent(self, event):
        if hasattr(self, 'auto_refresh_timer'):
            self.auto_refresh_timer.stop()
            
        if self.reg_thread and self.reg_thread.isRunning():
            self.reg_thread.stop()
            
        if self.management_success:
            self.accept()
        else:
            self.reject()
        event.accept()

# ==================== REGISTRATION THREAD ====================

class RegistrationThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    capture_success_signal = pyqtSignal(int)
    capture_error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.capture_now = False
        self.captured_embeddings = []
        self.captured_frames = []
        self.student_data = None
        self.cap = None

    def run(self):
        global face_engine
        if face_engine is None:
            face_engine = FaceEngine(threshold=0.35)

        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.capture_error_signal.emit("Gagal buka kamera. Pastikan kamera tidak dipakai aplikasi lain.")
                return
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        except Exception as e:
            self.capture_error_signal.emit(f"Error buka kamera: {e}")
            return

        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                self.change_pixmap_signal.emit(frame.copy())
                if self.capture_now:
                    self.process_capture(frame)
                    self.capture_now = False

        if self.cap:
            self.cap.release()
            self.cap = None

    def process_capture(self, frame):
        global face_engine
        try:
            faces = face_engine.detect_faces(frame)
            if len(faces) == 0:
                self.capture_error_signal.emit("Tidak ada wajah")
            elif len(faces) > 1:
                self.capture_error_signal.emit(f"Terdeteksi {len(faces)} wajah")
            else:
                emb = face_engine.get_embedding(faces[0])
                self.captured_embeddings.append(emb)
                self.captured_frames.append(frame.copy())
                self.capture_success_signal.emit(len(self.captured_embeddings))
        except Exception as e:
            self.capture_error_signal.emit(f"Error capture {e}")

    def trigger_capture(self):
        self.capture_now = True

    def save_to_storage(self):
        try:
            while len(self.captured_embeddings) < NUM_PHOTOS:
                if len(self.captured_embeddings) > 0:
                    self.captured_embeddings.append(self.captured_embeddings[0])
                    self.captured_frames.append(self.captured_frames[0])

            StorageManager.save_student_data(
                self.student_data['nim'],
                self.student_data['nama'],
                self.student_data['pbl'],
                self.captured_embeddings[:NUM_PHOTOS],
                self.captured_frames[:NUM_PHOTOS]
            )

            return True, f"{self.student_data['nama']} tersimpan"
        except Exception as e:
            return False, str(e)

    def stop(self):
        self._run_flag = False
        self.wait(500)
        try:
            if self.cap:
                self.cap.release()
        except:
            pass


# ==================== MAIN APP ====================

if __name__ == '__main__':
    try:
        db_pool = DatabasePool(5)
    except Exception as e:
        print("Gagal inisialisasi database pool:", e)
        db_pool = None

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())