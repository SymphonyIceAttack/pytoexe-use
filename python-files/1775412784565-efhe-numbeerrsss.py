import cv2
import winsound

print("12\n5\n1\nпривет!")

x = input("Введите число из этого списка: ")

if x == "12":
    print("Правильно!")
else:
    print('Неверно! Или число не из списка')

    cap = cv2.VideoCapture("video.mp4")
    winsound.PlaySound("video.wav", winsound.SND_ASYNC)
    while cap.isOpened():
        ret, frame = cap.read()
        cv2.imshow("", frame)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break