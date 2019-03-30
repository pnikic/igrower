import cv2
import numpy as np
import argparse

def nothing(x):
    pass

def run():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--image', help = 'path to the image')
    args = vars(ap.parse_args())

    if args['image'] == None:
        print('Image is not loaded')
        return

    cv2.namedWindow('W', cv2.WINDOW_NORMAL)
    img = cv2.imread(args['image'])
    scale = 4
    hor = img.shape[1] // scale
    ver = img.shape[0] // scale

    # B G R
    lo = [0,   0,  0]
    hi = [255, 255, 255]

    cv2.createTrackbar('B1', 'W', lo[0], 255, nothing)
    cv2.createTrackbar('B2', 'W', hi[0], 255, nothing)
    cv2.createTrackbar('G1', 'W', lo[1], 255, nothing)
    cv2.createTrackbar('G2', 'W', hi[1], 255, nothing)
    cv2.createTrackbar('R1', 'W', lo[2], 255, nothing)
    cv2.createTrackbar('R2', 'W', hi[2], 255, nothing)

    while True:
        lower = np.array([cv2.getTrackbarPos('B1','W'),
                          cv2.getTrackbarPos('G1','W'),
                              cv2.getTrackbarPos('R1','W')])
        upper = np.array([cv2.getTrackbarPos('B2','W'),
                          cv2.getTrackbarPos('G2','W'),
                              cv2.getTrackbarPos('R2','W')])

        mask = cv2.inRange(img, lower, upper)
        output = cv2.bitwise_and(img, img, mask = mask)


        stack = [img, output]
        cv2.resizeWindow('W', len(stack) * hor, ver)
        cv2.imshow('W', np.hstack(stack))
        cv2.resizeWindow('W', hor, ver)
        key = cv2.waitKey(100)
        
        if key == ord('q'):
            break

if __name__ == "__main__":
    run()
