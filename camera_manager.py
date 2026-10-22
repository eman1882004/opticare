import cv2
from session_manager import ConfigurationManager

class CameraManager:
    def __init__(self, config_manager=None):
        if config_manager is None:
            self.config = ConfigurationManager()
        else:
            self.config = config_manager
            
        self.camera_index = self.config.get_setting("camera_index")
        self.cap = None

    def start_camera(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"Error: Unable to open camera with index {self.camera_index}")
            return False
        return True

    def get_frame(self):
        if self.cap is not None and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None

    def release_camera(self):
        if self.cap is not None:
            self.cap.release()
            cv2.destroyAllWindows()
            print("Camera released successfully.")

if __name__ == "__main__":
    camera = CameraManager()
    if camera.start_camera():
        print("Camera feed running. Press 'q' on the video window to exit.")
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to grab frame.")
                break

            cv2.imshow("OptiCare - Camera Test", frame)
            
            # Exit when 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        camera.release_camera()