# Configure access to outer directories
import sys, os
dirs = ['calibration', 'camera', 'pose']
for dirName in dirs:
    sys.path.append(os.path.abspath(os.path.join('..', dirName)))

# Import packages
import cv2 
import numpy as np
import argparse
import shutil

# Import modules
from calibration import parameters as param
from camera import webcam as wc
from camera import apriltag_detection as ap
from pose import localisation as loc
from pose import plot
from visualisation import camera_pose_visualizer as cpv

if __name__ == "__main__":
    
    # # Clear atlas
    # atlas_folder = './pose/atlas'
    # for filename in os.listdir(atlas_folder):
    #     file_path = os.path.join(atlas_folder, filename)
    #     try:
    #         if os.path.isfile(file_path) or os.path.islink(file_path):
    #             os.unlink(file_path)
    #         elif os.path.isdir(file_path):
    #             shutil.rmtree(file_path)
    #     except Exception as e:
    #         print('Failed to delete %s. Reason: %s' % (file_path, e))

    # For parsing command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--image", required=False, 
        help = "Path to AprilTag image")
    parser.add_argument("-u", "--user", required=True, help = "User folder to search for calibration data")
    parser.add_argument("-c", "--calibrate", help = "Use calibration images instead of stored matrices", action="store_true")
    args = vars(parser.parse_args())
    
    # User variable is always going to be something
    user = args["user"]
    user_calibration_path = f"calibration/{user}/*.jpg"
    user_calibration_file = f"calibration/{user}/params"
    
    if args["calibrate"] is True:
        # Calibrate camera
        # TODO make the 2.1 a variable based on who is using the script
        side_len = float(input("How large is the checkerboard used in the calibration photos?"))
        _, cameraMatrix, distCoeffs, _, _ = param.get_calibration_values(side_len, user_calibration_path)
        param.write_parameter_files(user_calibration_file, cameraMatrix, distCoeffs)

    else:
        (cameraMatrix, distCoeffs) = param.read_values_from_file(user_calibration_file)
        #print(f"{cameraMatrix=}, {distCoeffs=}")

    # Set up camera pose visulariser
    visualizer = cpv.CameraPoseVisualizer([-100, 3000], [-100, 3000], [-100, 3000])

    # If no image flag provided, open webcam and do live localisation
    if isinstance(args["image"],type(None)):
        
        # Open webcam for image capture
        capture = wc.open_webcam()

        # Initialise plot handle
        hl = plot.init_position_figure()

        # Run continuously 
        while True:

            # Get frame
            frame = wc.get_current_webcam_frame(capture)

            # Detect apriltags
            results = ap.detect_apriltag(frame, silent=True)
            boxes, centers = ap.get_box_coords(results)
            ids = ap.get_detected_ids(results)

            # Localise if at least one aprilTag detected
            if (len(centers) >= 1):
                position, orientation = loc.results_to_global_pose(boxes, centers, ids, cameraMatrix, distCoeffs)
                # print(f"{position=}")
                # print(f"{orientation=}")

                # Rotation matrix
                R = loc.euler_zyx_to_rotm(orientation)
                # Translation vector
                t = position
                temp_matrix = np.hstack((R,t))

                # Extrinsic matrix 
                extrinsic_matrix = np.vstack((temp_matrix,np.array([0,0,0,1])))
                visualizer.extrinsic2pyramid(extrinsic_matrix.A, 'c', 400)
                visualizer.show()

                # Plot points
                plot.update_line(hl, np.asarray(position))

            # Draw boxes
            img = ap.draw_apriltag_boxes(results, frame)
            cv2.imshow("Image", img)

            # Check if 'q' was pressed
            key = cv2.waitKey(1)
            if key == ord('q'):
                quit()

    # Else if an image is provided, run localisation on it     
    else:

        # Get frame
        frame = cv2.imread(args["image"])

        # Detect apriltags
        results = ap.detect_apriltag(frame)
        boxes, centers = ap.get_box_coords(results)

        # Localise
        ids = ap.get_detected_ids(results)
        position, orientation = loc.results_to_global_pose(boxes, centers, ids, cameraMatrix, distCoeffs)
        #print('position (xyz) (mm):')
        #print(position)
        #print('orientation (RPY) (rad):')
        #print(orientation)

        # Draw boxes
        img = ap.draw_apriltag_boxes(results, frame)
        cv2.imshow("Image", img)

        # Check if 'q' was pressed
        while True:
            key = cv2.waitKey(1)
            if key == ord('q'):
                quit()

    capture.release()
    cv2.destroyAllWindows()
