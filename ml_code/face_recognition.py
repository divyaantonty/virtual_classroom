# % -*- coding: utf-8 -*-

import cv2
import pickle
#from hostel.models import *
import datetime
import os
#print(os.listdir('ml_code/database'))
label=list(os.listdir('ml_code/database'))

def fun(stud_id,date,status):
    import mysql.connector
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="vc1"
        )

    mycursor = mydb.cursor()
    sql="SELECT * FROM myapp_attendance WHERE student_id={} and date='{}'".format(stud_id,date)
    #print(sql)
    #val=
    mycursor.execute(sql)
    if len(mycursor.fetchall())==0:
        mycursor = mydb.cursor()
        sql = "insert into myapp_attendance(student_id, date, status)values(%d,%s,%s)"
        val = (stud_id,date,status)
        mycursor.execute(sql, val)
        mydb.commit()
    else:
        pass

 
def face_recognize(status):
    base_dir="ml_code/"
    # create objects
    cam = cv2.VideoCapture(0)
    #model = cv2.createFisherFaceRecognizer()
    #model = cv2.face.FisherFaceRecognizer_create()
    model = cv2.face.LBPHFaceRecognizer_create()
    faceD = cv2.CascadeClassifier(base_dir+"haarcascade_frontalface_default.xml")

    f= open(base_dir+"cand.txt","w")
    f.write("")
    f.close()
    i=0
    flag=0

    f=open(base_dir+"candt.txt", "r")
    contents =f.read()
    print(contents)



    with open(base_dir+'model.pkl', 'rb') as f:
            ids = pickle.load(f)
    model.read(base_dir+'model.xml')

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
            result = model.predict(face)
            print(label)
            print(result)
            if int(result[0]) < len(label):  # Add check to prevent index out of range
                print("prediction:", label[int(result[0])])
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                uid = label[int(result[0])]
                time = datetime.datetime.now()
                print(uid)
                print(time)
                print(status)
                if result[1] < 100:
                    flag = 1
            else:
                print("Unrecognized face - prediction index out of range")

        #cv2.imshow("video", frame)
        #print(ids[result[0]])
        
        if flag==1:
            fun(uid,str(time)[:10],str("present"))
            cam.release()
            cv2.destroyAllWindows()
            #user=wattendence(studentname=uid,date=)
            break
        """if cv2.waitKey(1) & 0xFF == ord("q"):
            cam.release()
            cv2.destroyAllWindows()"""


#face_recognize("entry")

