import cv2
import numpy as np
import mediapipe as mp
from session_manager import ConfigurationManager
from camera_manager import CameraManager


class EyeTracker:
    def __init__(self, config_manager=None):
        if config_manager is None:
            self.config = ConfigurationManager()
        else:
            self.config = config_manager

        self.ear_threshold = self.config.get_setting("ear_threshold")
        if self.ear_threshold is None:
            self.ear_threshold = 0.22

        self.LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.blink_count = 0
        self.eye_closed = False

    def calculate_ear(self, landmarks, eye_indices, img_w, img_h):
        points = []
        for idx in eye_indices:
            lm = landmarks[idx]
            points.append(np.array([lm.x * img_w, lm.y * img_h]))

        dist_v1 = np.linalg.norm(points[1] - points[5])
        dist_v2 = np.linalg.norm(points[2] - points[4])
        dist_h = np.linalg.norm(points[0] - points[3])

        if dist_h == 0:
            return 0.0

        ear = (dist_v1 + dist_v2) / (2.0 * dist_h)
        return ear

    def get_gaze_ratio(self, landmarks, eye_indices, frame):
        h, w, _ = frame.shape
        eye_points = np.array(
            [[int(landmarks[idx].x * w), int(landmarks[idx].y * h)] for idx in eye_indices],
            np.int32,
        )

        # إنشاء قناع للعين فقط
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.polylines(mask, [eye_points], True, 255, 2)
        cv2.fillPoly(mask, [eye_points], 255)

        # عزل منطقة العين وتحويلها لتدرج رمادي
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        eye_region = cv2.bitwise_and(gray_frame, gray_frame, mask=mask)

        min_x = np.min(eye_points[:, 0])
        max_x = np.max(eye_points[:, 0])
        min_y = np.min(eye_points[:, 1])
        max_y = np.max(eye_points[:, 1])

        eye_cropped = eye_region[min_y:max_y, min_x:max_x]
        if eye_cropped.size == 0:
            return 1.0

        # تطبيق عتبة لمعرفة بؤبؤ العين
        _, threshold_eye = cv2.threshold(eye_cropped, 70, 255, cv2.THRESH_BINARY)
        eye_h, eye_w = threshold_eye.shape
        if eye_w == 0 or eye_h == 0:
            return 1.0

        # تقسيم العين إلى نصفين (يمين ويسار) ومقارنة كثافة الضوء
        left_side_threshold = threshold_eye[0:eye_h, 0:int(eye_w / 2)]
        left_side_white = cv2.countNonZero(left_side_threshold)

        right_side_threshold = threshold_eye[0:eye_h, int(eye_w / 2):eye_w]
        right_side_white = cv2.countNonZero(right_side_threshold)

        if left_side_white == 0:
            gaze_ratio = 5.0
        elif right_side_white == 0:
            gaze_ratio = 0.2
        else:
            gaze_ratio = left_side_white / right_side_white

        return gaze_ratio

    def process_frame(self, frame):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        avg_ear = None
        gaze_direction = "Looking Center"

        if results.multi_face_landmarks:
            mesh_points = results.multi_face_landmarks[0].landmark

            # 1. حساب الـ EAR لاكتشاف الرمشات
            left_ear = self.calculate_ear(mesh_points, self.LEFT_EYE_INDICES, w, h)
            right_ear = self.calculate_ear(mesh_points, self.RIGHT_EYE_INDICES, w, h)
            avg_ear = (left_ear + right_ear) / 2.0

            if avg_ear < self.ear_threshold:
                if not self.eye_closed:
                    self.eye_closed = True
                    self.blink_count += 1
            else:
                self.eye_closed = False
                # 2. حساب اتجاه النظر (Gaze Ratio)
            left_gaze = self.get_gaze_ratio(mesh_points, self.LEFT_EYE_INDICES, frame)
            right_gaze = self.get_gaze_ratio(mesh_points, self.RIGHT_EYE_INDICES, frame)
            gaze_ratio = (left_gaze + right_gaze) / 2.0

            if gaze_ratio < 0.8:
                gaze_direction = "Looking Right"
            elif 0.8 <= gaze_ratio <= 1.6:
                gaze_direction = "Looking Center"
            else:
                gaze_direction = "Looking Left"

        return avg_ear, self.blink_count, gaze_direction


if __name__ == "__main__":
    camera = CameraManager()
    tracker = EyeTracker()

    if camera.start_camera():
        print("Blink and Gaze detection running. Press 'q' to exit.")
        while True:
            frame = camera.get_frame()
            if frame is None:
                break

            ear, blinks, gaze = tracker.process_frame(frame)

            if ear is not None:
                cv2.putText(
                    frame,
                    f"EAR: {ear:.2f}",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
            cv2.putText(
                frame,
                f"Blinks: {blinks}",
                (30, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Gaze: {gaze}",
                (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 200, 255),
                2,
            )

            cv2.imshow("OptiCare - Blink & Gaze Detection Test", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        camera.release_camera()