import time

class EarBlinkDetector:
    def __init__(self, ear_threshold=0.19, min_blink_duration=0.20, long_blink_duration=1.2):
        self.ear_threshold = ear_threshold              # عتبة غلق العين
        self.min_blink_duration = min_blink_duration    # الحد الأدنى للرمشة الإرادية
        self.long_blink_duration = long_blink_duration  # مدة الرمشة الطويلة للرجوع

        # مؤقتات تتبع غلق العين
        self.left_closed_start = None
        self.right_closed_start = None
        self.long_blink_triggered = False

    def process_frame(self, left_ear, right_ear, gesture_controller):
        now = time.time()
        result = None

        # 1. فحص العين اليسرى
        if left_ear < self.ear_threshold:
            if self.left_closed_start is None:
                self.left_closed_start = now
                self.long_blink_triggered = False
            else:
                # التحقق من الرمشة الطويلة للعين اليسرى (Back)
                closed_dur = now - self.left_closed_start
                if closed_dur >= self.long_blink_duration and not self.long_blink_triggered:
                    self.long_blink_triggered = True
                    self.left_closed_start = None
                    return {"type": "COMMAND", "action": "BACK"}
        else:
            # العين فُتحت بعد أن كانت مغلقة
            if self.left_closed_start is not None:
                duration = now - self.left_closed_start
                self.left_closed_start = None
                if not self.long_blink_triggered and (duration >= self.min_blink_duration):
                    # رمشة يسار مقصودة
                    res = gesture_controller.add_blink("L")
                    if res:
                        result = res

        # 2. فحص العين اليمنى
        if right_ear < self.ear_threshold:
            if self.right_closed_start is None:
                self.right_closed_start = now
        else:
            if self.right_closed_start is not None:
                duration = now - self.right_closed_start
                self.right_closed_start = None
                if duration >= self.min_blink_duration:
                    # رمشة يمين مقصودة
                    res = gesture_controller.add_blink("R")
                    if res:
                        result = res

        return result