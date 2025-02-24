# % -*- coding: utf-8 -*-
"""
Created With PYTHON 3.6

@author: ARUN KUMAR
"""


import os
import cv2
import numpy
import pickle
from time import sleep

def train_faces():
    base_dir="ml_code/"
    images = []
    labels = []
    ids = {}
    count = 0
    for subdir in os.listdir(base_dir+'database'):
        ids[count] = subdir
        path = base_dir+'/database/'+subdir
        for filename in os.listdir(path):
            impath = path+ '/'+filename
            im = cv2.imread(impath,0)
            #cv2.imshow("Adding faces to traning set...", im)
            #sleep(1)
            images.append(im)
            labels.append(count)
        count+=1

    images = numpy.array(images)
    labels = numpy.array(labels)
    print(labels)

    #model = cv2.createFisherFaceRecognizer()
    #model = cv2.face.FisherFaceRecognizer_create()
    model = cv2.face.LBPHFaceRecognizer_create()
    model.train(images, labels)
    model.save(base_dir+'model.xml')
    with open(base_dir+'model.pkl', 'wb') as f:
        pickle.dump(ids, f)
    cv2.destroyAllWindows()
    print("training completed")
    
#train_faces()