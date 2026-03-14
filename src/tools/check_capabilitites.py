import cv2
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CapCheck")

def check_device(index=1):
    logger.info(f"Opening camera index {index}...")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        logger.error(f"Could not open camera at index {index}")
        return

    # Adunk neki egy kis időt, hogy magához térjen
    time.sleep(1)

    logger.info("Setting MJPG and Resolution...")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Fontos: egy üres olvasás, hogy a puffer ürüljön
    for _ in range(5):
        cap.read()
        time.sleep(0.1)

    ret, frame = cap.read()
    if ret and frame is not None:
        logger.info(f"SUCCESS! Actual frame size: {frame.shape[1]}x{frame.shape[0]}")
    else:
        logger.warning("Failed to grab frame.")
    
    logger.info(f"Reported Width: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}")
    logger.info(f"Reported Height: {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
    logger.info(f"FOURCC Code: {int(cap.get(cv2.CAP_PROP_FOURCC))}")
    
    cap.release()

if __name__ == "__main__":
    # Érdemes kipróbálni a 0-s és 1-es indexet is
    check_device(1)