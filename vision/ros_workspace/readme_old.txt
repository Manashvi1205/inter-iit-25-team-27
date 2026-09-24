->>>> @jarvis-desktop:~/Inter_IIT$ source ultron/bin/activate

Wechat require opencv contribution 
model requires file in the same parent directory
run in virutal env
debug contains a josn for output data forn  each level



SERVO
pyserial required               
-> find usb port using  '  ls /dev/ttyUSB*  '
maybe:  /dev/ttyUSB0 
-> port permission is rquired to access the port
give perm and reboot: sudo usermod -aG dialout $USER
                next: sudo reboot



->AUTOFOCUS : 0 -OFF,1-ON 'v4l2-ctl -d /dev/video0 --set-ctrl=focus_automatic_continuous=1'
MANUAL  FOCUS: ' v4l2-ctl -d /dev/video0 --set-ctrl=focus_absolute=200'


servo_move_to_delay  can be reduced!!!!!
write this function: 'remove_duplicates_across_poses' ,





ISSUES:
MULTIPLE IMAGES CASUING ISSUUES -> DIFFERENT SCAN STILL SAME QR DATA, STILL STORED... NEEDS FIX



ALSO NO BOUNDING BOX!!? WHY??
CREATE BOUNDING BOX..(RESOLVED)
ALSO THE DEBUG IS FALSE BY DEFAULT CAUSING ISSUES!!(STILL NEEDS FIXES)
=> entire code for debug output needs to be fixecds!!
 => hommography incorporate karna hai!!
=> also once the scanning finish it should go back to Home that is (1,1) position
=> also if the output path/directory is  not present then create one and use.. do not throw such errors... print in logs/consol as required!


NEXT(2/DEC)

 => hommography incorporate karna hai!!
 => return HOME SEQUENCE 
 => CLIBRATE SERVOS (done)
 => RGB (done)
 



 




'''
FLOW:
get-input->img2write->process_data		
		
		
img2write: take(img,x0,d,z0,ori,K) ->img2rack(proj,scale,xz_topleft)->make_qr_array(yolo)=>{for each qr runthis}=> rack_xy(process the qr_coordinates) & reader.read(process the img,get payload) -> return output		
		
		



1.) Create a class Scanner=> init with camera,servo,detector
2.) get_input grab frames   save to a folder ( captures for now)  along with the meta data
3.) that is it!
additional public methods:
servoBoard access/acces to servomotion and LEDs
# stored images and metadata is processed by ProcessorClass.py code
'''









'''

Flow:

make a classProcessor=. init with input folder output foldder/files .... 
along with loading wechat model and yolo model for multi qr detection

here we process the data stored in the folder(raw_captures)
-> read the image and metadata
-> pass it to img2write along with the parameters
=> using the output payload and centroids process and log data using process_data.py
->process_data.py will handle logging and storing the data 

now the question! when do i run the processorclass!!!!

should i keep looking for new images or is there a better wat!?!

lets plan
'''


TO DO
usb candidates

=> Run  from inTERiit ONLY, CAUSE THE FILE PATHS ARE RELATIVE

K MATRIX UPDATED, WE TOOK  BETTER IMAGES AND RECALIBRATED ALSO UPDATED SQUARE SIZE OF CHESSBOARD TO  20 MM FROM 25 MM. NEW k is
objpoints[0].shape: (48, 3)
imgpoints[0].shape: (48, 1, 2)

Calibration success flag: 2.264043821905698
Camera matrix (intrinsic):
 [[252.48483428   0.         314.2399718 ]
 [  0.         254.07987077 231.91962777]
 [  0.           0.           1.        ]]

Distortion coefficients:
 [-0.05275756  0.07169613  0.00231284 -0.00724033 -0.03682232]
Wrote sample undistorted image to calibresult.png
Mean reprojection error (pixels): 0.24514515338970655




