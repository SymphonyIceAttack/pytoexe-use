import cv2
import mediapipe as mp
import pyautogui
import time

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

last_swipe_time = 0
last_fist_time = 0
last_thumb_time = 0
SWIPE_COOLDOWN = 0.4
GESTURE_COOLDOWN = 1.0

prev_y = None
swipe_accumulator = 0
SWIPE_THRESHOLD = 35

pyautogui.FAILSAFE = False


def detect_gesture(lm):
    tips = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    folded = [lm[tip].y > lm[pip].y + 0.02 for tip, pip in zip(tips, pips)]
    all_folded = all(folded)
    thumb_up = (
        lm[4].y < lm[3].y < lm[2].y and
        lm[4].y < lm[8].y - 0.05
    )
    if all_folded and thumb_up:
        return 'thumbs_up'
    if all_folded and not thumb_up:
        return 'fist'
    return None


def change_volume(direction):
    """Надёжный способ — эмуляция клавиш громкости"""
    if direction == 'up':
        pyautogui.press('volumeup')
        print("🔊 Громкость +")
    else:
        pyautogui.press('volumedown')
        print("🔉 Громкость -")


print("🎥 Камера запущена.")
print("   ✋ Открытая ладонь + движение вверх/вниз = громкость")
print("   ✊ Кулак (неподвижно) = пауза")
print("   👍 Класс = скриншот")
print("   'q' = выход\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    now = time.time()
    gesture = None

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)
            lm = hand_lms.landmark
            h, w, _ = frame.shape
            palm_y = lm[9].y * h

            gesture = detect_gesture(lm)

            # === СВАЙП ===
            if gesture is None and prev_y is not None:
                dy = prev_y - palm_y
                if abs(dy) < 150:
                    swipe_accumulator += dy

                if (now - last_swipe_time) > SWIPE_COOLDOWN:
                    if swipe_accumulator > SWIPE_THRESHOLD:
                        change_volume('up')
                        swipe_accumulator = 0
                        last_swipe_time = now
                        cv2.arrowedLine(frame, (w//2, h//2), (w//2, h//2 - 80),
                                        (0, 255, 0), 5)
                        cv2.putText(frame, "VOL +", (w//2 - 60, h//2 - 100),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    elif swipe_accumulator < -SWIPE_THRESHOLD:
                        change_volume('down')
                        swipe_accumulator = 0
                        last_swipe_time = now
                        cv2.arrowedLine(frame, (w//2, h//2), (w//2, h//2 + 80),
                                        (0, 255, 0), 5)
                        cv2.putText(frame, "VOL -", (w//2 - 60, h//2 + 120),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            elif gesture is not None:
                swipe_accumulator = 0

            prev_y = palm_y

            # === КУЛАК ===
            if gesture == 'fist' and (now - last_fist_time) > GESTURE_COOLDOWN:
                if abs(swipe_accumulator) < 15:
                    pyautogui.press('space')
                    print("⏸ Пауза/Play")
                    last_fist_time = now
                    cv2.putText(frame, "PAUSE!", (w//2 - 80, h//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

            # === ЛАЙК ===
            elif gesture == 'thumbs_up' and (now - last_thumb_time) > GESTURE_COOLDOWN:
                pyautogui.screenshot(f"screenshot_{int(now)}.png")
                print("📸 Скриншот сохранён")
                last_thumb_time = now
                cv2.putText(frame, "SCREENSHOT!", (w//2 - 150, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 255), 4)

            cv2.putText(frame, f"Gesture: {gesture or 'open'}",
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Swipe acc: {int(swipe_accumulator)}",
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    else:
        prev_y = None
        swipe_accumulator = 0

    cv2.putText(frame, "Open palm+swipe=Vol | Fist=Pause | Thumb=Shot | q=Quit",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()