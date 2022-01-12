import face_recognition
import numpy as np
import cv2, queue, threading
import os, re
from datetime import datetime 

import pandas as pd
df = pd.DataFrame(list())
df.to_csv('Attendance.csv')

# bufferless VideoCapture
class VideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()
def MarkAttendance(name):
    with open("Attendance.csv","r+") as f:
        myDatalist = f.readlines()
        nameList = []
        for line in myDatalist:
            entry = line.split(",")
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            f.writelines(f'\n{name},{dtString}')

# Select the webcam of the computer
video_capture = VideoCapture(0)


# * -------------------- USERS -------------------- *
known_face_encodings = []
known_face_names = []
known_faces_filenames = []

for (dirpath, dirnames, filenames) in os.walk('known_faces/jahnavi/'):
    known_faces_filenames.extend(filenames)
    break

for filename in known_faces_filenames:
    face = face_recognition.load_image_file('known_faces/jahnavi/' + filename)
    known_face_names.append(re.sub("[0-9]",'', filename[:-4]))
    known_face_encodings.append(face_recognition.face_encodings(face)[0])



face_locations = []
face_encodings = []
face_names = []
process_this_frame = True


while True:

    frame = video_capture.read()
    
    # # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
#    frame = small_frame[:, :, ::-1]
    
    # Process every frame only one time
    if process_this_frame:
        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(frame,model = "hog")
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        # Initialize an array for the name of the detected users
        face_names = []

        # * ---------- Initialyse JSON to EXPORT --------- *
#        json_to_export = {}
        
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # # If a match was found in known_face_encodings, just use the first one.
            # if True in matches:
            #     first_match_index = matches.index(True)
            #     name = known_face_names[first_match_index]

            # Or instead, use the known face with the smallest distance to the new face
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]


            face_names.append(name)
        
    process_this_frame = not process_this_frame
            
            # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):


        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (255, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        MarkAttendance(name)
    # Display the resulting image
    cv2.imshow('Video', frame)

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release handle to the webcam
#video_capture.release()
cv2.destroyAllWindows()
