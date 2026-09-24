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



->AUTOFOCUS : 0 -OFF,1-ON'v4l2-ctl -d /dev/video0 --set-ctrl=focus_automatic_continuous=1'
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
 



 