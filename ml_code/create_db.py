
import cv2
import os

def create_data(contents):
    base_dir="ml_code/"
    """
    f=open(base_dir+"input.txt", "r")
    contents =f.read()"""
    print(contents)



    database = base_dir+'database'
    dataset = contents
    path = os.path.join(database,dataset)
    if not os.path.isdir(path):
        os.mkdir(path)

    # create objects
    cam = cv2.VideoCapture(0)
    faceD = cv2.CascadeClassifier(base_dir+"haarcascade_frontalface_default.xml")
    count = 1
    while (cam.isOpened()):
        ret, frame = cam.read()
        if not(ret):
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceD.detectMultiScale(gray, 1.3, 5)
        for (x,y,w,h) in faces:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
            face = gray[y:y+h,x:x+w]
            face = cv2.resize(face,(130,100))
            cv2.imwrite('{}/{}.png'.format(path,count), face)
            count+=1
            if count==31:
                cam.release()
                cv2.destroyAllWindows()

        cv2.imshow("video", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cam.release()
            cv2.destroyAllWindows()
			
#fun1('2')




