import cv2
import time
import os
import winsound
import logging

# --- LOGGER CONFIGURATION ---
# This is our "Log4j" equivalent in Python
logger = logging.getLogger("AndonstarEngine")
logger.setLevel(logging.INFO)

# Format: Time - Name - Level - Message
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

# Console Handler
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

class AndonstarEngine:
    def __init__(self, camera_index=1, base_dir=None):
        if camera_index == -1:
            self.camera_index = self._find_microscope_index()
        else:
            self.camera_index = camera_index
        
        # Portable path management: defaults to a 'captures' folder next to the script
        if base_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.base_dir = os.path.join(project_root, "captures")
        else:
            self.base_dir = base_dir
            
        self.fps = 15.0  
        self.resolution = (1920, 1080)
        
        # Internal variable (protected)
        self._current_project = "Microscope_Project"
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            logger.info(f"Created capture directory at: {self.base_dir}")

    @property
    def project_display_name(self) -> str:
        """Returns the project name formatted for UI/Watermark (underscores to spaces)."""
        return self._current_project.replace("_", " ")

    def set_project(self, name: str) -> str:
        """Updates the project context and logs the change."""
        old_name = self._current_project
        self._current_project = name.strip().replace(" ", "_")
        logger.info(f"Project context changed: {old_name} -> {self._current_project}")
        return self._current_project

    def _beep_start(self):
        """Audio feedback before recording."""
        for _ in range(3):
            winsound.Beep(1000, 100)
            time.sleep(0.3)
        winsound.Beep(2000, 500)

    def _beep_stop(self):
        """Audio feedback after recording."""
        winsound.Beep(600, 400)

    def _setup_camera(self, low_res=False):
        """Configures the camera with Andonstar-specific MJPG settings."""
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        if low_res:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        else:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        return cap

    def run_focus_assistant(self):
        """Live focus assistant using Laplacian variance."""
        logger.info("Starting Focus Assistant...")
        cap = self._setup_camera(low_res=True)
        max_f, last_f = 0, 0
        
        while True:
            ret, frame = cap.read()
            if not ret: 
                logger.error("Focus Assistant: Failed to grab frame.")
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            last_f = cv2.Laplacian(gray, cv2.CV_64F).var()
            if last_f > max_f: max_f = last_f
            
            color = (0, 255, 0) if last_f > max_f * 0.95 else (0, 0, 255)
            cv2.putText(frame, f"CURRENT: {int(last_f)}", (20, 40), 1, 1.5, color, 2)
            cv2.putText(frame, f"PEAK (R: Reset): {int(max_f)}", (20, 80), 1, 1.5, (255, 250, 0), 2)
            cv2.imshow('Andonstar Focus Assistant - Q: Exit, R: Reset', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            if key == ord('r'): 
                max_f = 0
                logger.info("Focus Peak reset by user.")
            
        cap.release()
        cv2.destroyAllWindows()
        logger.info(f"Focus Assistant closed. Final Peak: {int(max_f)}")
        return int(last_f), int(max_f)

    def take_snapshot(self):
        """Captures a high-res image with a timestamped watermark."""
        cap = self._setup_camera()
        time.sleep(0.6) # Wait for auto-exposure to settle
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            filename = f"{self._current_project}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            path = os.path.join(self.base_dir, filename)
            
            h, w = frame.shape[:2]
            # Using our property for the label
            label = f"{self.project_display_name} | {time.strftime('%H:%M:%S')}"
            
            # Simple text shadow for readability
            cv2.putText(frame, label, (22, h - 22), 1, 1.5, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(frame, label, (20, h - 20), 1, 1.5, (255,255,255), 1, cv2.LINE_AA)
            
            cv2.imwrite(path, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            logger.info(f"Snapshot saved: {filename}")
            return path
            
        logger.error("Snapshot failed: Could not read from camera.")
        return None

    def record_clip(self, duration=5):
        """Records a video clip with pre-measured FPS for sync stability."""
        cap = self._setup_camera()
        out = None
        try:
            # Flush buffer
            for _ in range(10): cap.read()
            
            # Measure actual FPS
            start_m = time.time()
            for _ in range(10): cap.read()
            measured_fps = 10 / (time.time() - start_m)
            
            # Clamp FPS to reasonable values
            if measured_fps > 60: measured_fps = 30.0
            
            logger.info(f"Recording video ({duration}s) at {measured_fps:.2f} FPS.")
            self._beep_start()
            
            filename = f"{self._current_project}_{time.strftime('%Y%m%d_%H%M%S')}.avi"
            path = os.path.join(self.base_dir, filename)
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            out = cv2.VideoWriter(path, fourcc, measured_fps, (1920, 1080))
            
            total_frames = int(measured_fps * duration)
            recorded = 0
            start_rec = time.time()
            
            while recorded < total_frames:
                ret, frame = cap.read()
                if not ret: 
                    logger.warning("Video Recording: Frame drop detected.")
                    break
                out.write(frame)
                recorded += 1
            
            actual_duration = time.time() - start_rec
            logger.info(f"Video saved to {filename}. ({recorded} frames in {actual_duration:.2f}s)")
            
            self._beep_stop()
            return path
        except Exception as e:
            logger.error(f"Video recording error: {str(e)}")
            return None
        finally:
            if out: out.release()
            cap.release()

    def _find_microscope_index(self) -> int:
        """
        Smart scan to find the microscope. 
        Prioritizes high-res devices over standard webcams.
        """
        logger.info("Scanning for microscope device...")
        # 0 is usually the integrated webcam, we check up to 4
        for i in range(5):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    h, w = frame.shape[:2]
                    logger.info(f"Checking device {i}: {w}x{h}")
                    # Andonstar specific: usually shows up as 1080p or 720p MJPG
                    if w >= 1280:
                        logger.info(f"Microscope found and selected at index {i}")
                        cap.release()
                        return i
                cap.release()
        
        logger.warning("No high-res device found. Defaulting to index 1.")
        return 1

if __name__ == "__main__":
    # Simple self-test
    logger.info("--- ANDONSTAR ENGINE SELF-TEST MODE ---")
    test_engine = AndonstarEngine()
    print(f"Initial project: {test_engine.project_display_name}")
    vid = test_engine.record_clip(3)