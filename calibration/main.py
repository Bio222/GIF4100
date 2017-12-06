import numpy as np
import cv2
import glob

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objectPoint = np.zeros((7 * 6, 3), np.float32)
objectPoint[:, :2] = np.mgrid[0:7, 0:6].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objectPoints = [] # 3d point in real world space
imagePoints = [] # 2d points in image plane.

imageNames = glob.glob('*.jpg')

for name in imageNames:
    image = cv2.imread(name)
    grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Find the chess board corners
    isChessboardCornersFound, corners = cv2.findChessboardCorners(grayImage, (7, 6), None)

    newCameraMatrix = 0

    # If found, add object points, image points (after refining them)
    if isChessboardCornersFound:
        objectPoints.append(objectPoint)

        corners2 = cv2.cornerSubPix(grayImage, corners, (11, 11), (-1, -1), criteria)

        imagePoints.append(corners)

        # Calibration
        ret, cameraMatrix, distortionCoef, rotationVectors, translationVectors = cv2.calibrateCamera(objectPoints, imagePoints, grayImage.shape[::-1], None, None)

        # Undistortion
        h, w = image.shape[:2]
        newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, distortionCoef, (w, h), 1, (w, h))

        # undistort
        mapx, mapy = cv2.initUndistortRectifyMap(cameraMatrix, distortionCoef, None, newCameraMatrix, (w, h), 5)
        dst = cv2.remap(image, mapx, mapy, cv2.INTER_LINEAR)

        dst = cv2.undistort(image, cameraMatrix, distortionCoef, None, newCameraMatrix)

        # crop the image
        #x, y, w, h = roi
        #dst = dst[y:y + h, x:x + w]

        cv2.imshow('calibresult', dst)
        cv2.waitKey()
        
        np.savetxt("newCameraMatrix.txt", newCameraMatrix, fmt='%.2f')

cv2.destroyAllWindows()