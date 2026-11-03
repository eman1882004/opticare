import time

class BlinkGestureController:
    def __init__(self, timeout=0.5, cooldown=0.6):
        self.timeout = timeout          # أقصى وقت مسموح به بين الرمشة الأولى والثانية
        self.cooldown = cooldown        # وقت الراحة بعد تنفيذ أمر لمنع التكرار
        self.sequence = []              # مخزن الرمشات المؤقت
        self.last_blink_time = 0        # توقيت آخر رمشة
        self.last_action_time = 0       # توقيت آخر أمر نُفذ

    def add_blink(self, eye_type):
        """
        eye_type: 'L' للعين اليسرى، 'R' للعين اليمنى
        """
        now = time.time()

        # إذا كنا في فترة الـ Cooldown بعد تنفيذ أمر، نتجاهل أي مدخلات
        if now - self.last_action_time < self.cooldown:
            return None

        # فحص انتهاء الوقت: إذا تأخر المستخدم بين الرمشتين نمسح التخزين ونبدأ من جديد
        if self.sequence and (now - self.last_blink_time > self.timeout):
            self.sequence.clear()

        self.sequence.append(eye_type)
        self.last_blink_time = now

        # إذا كانت هذه الرمشة الأولى، نخبر الواجهة لعرض الحرف في الأسفل
        if len(self.sequence) == 1:
            return {"type": "BUFFER", "current_sequence": eye_type}

        # إذا اكتملت رمشتان متتاليتان
        elif len(self.sequence) == 2:
            gesture_code = "".join(self.sequence)
            self.sequence.clear()
            self.last_action_time = now
            return {"type": "SELECTION", "sequence": gesture_code}

        return None

    def reset_sequence(self):
        """تصفير المخزن يدوياً عند تبديل القوائم"""
        self.sequence.clear()