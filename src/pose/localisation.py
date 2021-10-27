# Import packages
import cv2
import math
import numpy as np

# Import modules
from camera import apriltag_detection as ap

# Public Interface------------------------------------------------------------------------------------------------
def results_to_global_pose(boxes, centers, ids, cameraMatrix, distCoeffs):

    # Construct a numpy array of image points
    imagePoints = []
    for tag in range(len(centers)):
        imagePoints.append(centers[tag])
        for corner in boxes[tag]:
            imagePoints.append(corner)
    imagePoints = np.array(imagePoints)

    # Construct numpy array of object points
    # TODO: currently hardcoded - will expand to lookup table
    objectPoints = np.array([
                            (0.0 ,0.0 ,0.0 ),       # centre
                            (0.0, -12.0, 12.0),     # top-left
                            (0.0, -12.0, -12.0),    # bottom-left
                            (0.0, 12.0, -12.0),     # bottom-right
                            (0.0, 12.0, 12.0),      # top-right
                            ])
    
    position, orientation = points_to_global_pose(objectPoints, imagePoints, cameraMatrix, distCoeffs)

    return position, orientation

def points_to_global_pose(objectPoints, imagePoints, cameraMatrix, distCoeffs):
    _, rVec, tVec = cv2.solvePnP(objectPoints, imagePoints, cameraMatrix, distCoeffs)
    rotm_t = cv2.Rodrigues(rVec)[0]
    rotm = np.matrix(rotm_t).T
    position = -rotm * np.matrix(tVec)
    orientation = rotm_to_euler_zyx(rotm)

    return position, orientation

'''
Return 3D rotation matrix given ZYX Euler angles
- Inputs:
    - euler_zyx: numpy column vector [yaw; pitch; roll] (rad)
- Outputs:
    - rotm: 3x3 rotation matrix
'''
def euler_zyx_to_rotm(euler_zyx):
    yaw = euler_zyx.item(0)
    pitch = euler_zyx.item(1)
    roll = euler_zyx.item(2)

    Rz_yaw = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]])

    Ry_pitch = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]])

    Rx_roll = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]])

    rotm = np.dot(Rz_yaw, np.dot(Ry_pitch, Rx_roll))

    return rotm


'''
Return ZYX Euler angles given 3D rotation matrix
- Inputs:
    - rotm: 3x3 rotation matrix
- Outputs:
    - euler_zyx: numpy column vector [yaw; pitch; roll] (rad)
'''
def rotm_to_euler_zyx(rotm):
    if (rotm.item(2, 0) < 1):
        if (rotm.item(2, 0) > -1):

            # Determine zyx Euler angles
            pitch = np.arcsin(-rotm.item(2, 0))
            yaw = np.arctan2(rotm.item(1, 0), rotm.item(0, 0))
            roll = np.arctan2(rotm.item(2, 1), rotm.item(2, 2))

        else:

            # Non-unique solution hard-coded
            pitch = math.pi / 2
            yaw = -np.arctan2(-rotm.item(1, 2), rotm.item(1, 1))
            roll = 0
    else:

        # Non-unique solution hard-coded
        pitch = -math.pi / 2
        yaw = np.arctan(-np.item(1, 2), np.item(1, 1))
        roll = 0

    euler_zyx = np.array([yaw, pitch, roll]).transpose()

    return euler_zyx


# Main------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    euler_zyx = np.array([0.1, 0.2, 0.3]).transpose()
    print(euler_zyx_to_rotm(euler_zyx))
    print(rotm_to_euler_zyx(euler_zyx_to_rotm(euler_zyx)))

