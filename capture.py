import depthai as dai
import cv2
import numpy as np
from device import Device
import json
from itertools import combinations

found, device_info = dai.Device.getFirstAvailableDevice() # type: ignore

if not found:
	raise Exception("No device connected!")

device = Device(device_info)


CAMERA_WALL_DISTANCE = 1 # m

frame_width = 360

offsets = { # compensation for different camera positions (in m)
    "right": -0.0375,
    "rectified_right": -0.0375,
    "color": 0,
    "left": 0.0375,
    "rectified_left": 0.0375,
}

aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)

def get_corners(image):
	""" Get the corners of the noise pattern board """
	
	corners, ids, rejectedImgPoints = cv2.aruco.detectMarkers(image, aruco_dict)

	if len(corners) != 4:
		raise Exception("Noise pattern board not found")

	inds = np.argsort(ids.flatten())
	corners_sorted = np.array(corners)[inds]
	if len(corners_sorted) != 4:
		raise Exception("Noise pattern board not found")

	center = np.array([m.mean(axis=1).flatten() for m in corners_sorted]).mean(axis=0)

	points = []
	for m in corners_sorted:
		i = np.linalg.norm(m - center, axis=-1).argmin()
		points.append(m[:, i])

	points = np.array(points).reshape(-1, 2)

	return points

def get_center(points):
	center = points.mean(axis=0)
	return center[0], center[1]

def get_rotation(points):
	center_bottom = (points[0] + points[1]) / 2
	center_top = (points[2] + points[3]) / 2
	d = center_bottom - center_top
	angle = np.arctan2(*d)
	return angle

def get_board_width(points):
	return np.linalg.norm(points[0] - points[1])

msg = ""

while True:
	device.update()

	if len(device.last_frame.keys()) == 0:
		continue
	
	img_combined = np.zeros((frame_width, frame_width*len(device.last_frame.keys()), 3), dtype=np.uint8)
	i = 0
	results = {}
	all_cams_detected = True

	for name, img in device.last_frame.items():
		if len(img.shape) == 2:
			img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

		img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
		roll_angle = yaw_angle = pitch_angle = np.nan
		try:
			points = get_corners(img_gray)
			center_x, center_y = get_center(points)
			angle = get_rotation(points)
			board_width = get_board_width(points)
			px2m = 0.6 / board_width
			offset = offsets[name]

			roll_angle = np.rad2deg(angle)
			yaw_angle = np.rad2deg(np.arctan2(offset + px2m * (img.shape[1]/2 - center_x), CAMERA_WALL_DISTANCE))
			pitch_angle = np.rad2deg(np.arctan2(px2m * (img.shape[0]/2 - center_y), CAMERA_WALL_DISTANCE))

			results[f"{name}_roll_angle"] = float(roll_angle)
			results[f"{name}_yaw_angle"] = float(yaw_angle)
			results[f"{name}_pitch_angle"] = float(pitch_angle)


			img = img.copy()
			for p in points:
				cv2.circle(img, tuple(p.astype(int)), img.shape[0]//40, (0, 0, 255), -1)

			
		except:
			all_cams_detected = False

		img_downscale = cv2.resize(img, (frame_width, int(frame_width/img.shape[1]*img.shape[0])), interpolation=cv2.INTER_AREA)
		cv2.putText(img_downscale, name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
		cv2.putText(img_downscale, f"roll: {roll_angle:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
		cv2.putText(img_downscale, f"yaw: {yaw_angle:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
		cv2.putText(img_downscale, f"pitch: {pitch_angle:.2f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 2)
		img_combined[0:img_downscale.shape[0], i*frame_width:(i+1)*frame_width] = img_downscale
		cv2.putText(img_combined, msg, (10, frame_width-30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
		i += 1
	cv2.imshow("preview", img_combined)

	depth_msg = device.depth_queue.tryGet()

	key = cv2.waitKey(1)

	if key == ord('s'):
		if not all_cams_detected:
			msg = "Not all cameras detected the markers"
		else:
			msg = "Saved"
			for name, img in device.last_frame.items():
				cv2.imwrite(f"{device.device_dir}/{name}.png", img)

			for cam_a, cam_b in combinations(["left", "right", "color"], 2):
				results[f"{cam_a}_{cam_b}_roll_diff"] = np.abs(results[f"{cam_a}_roll_angle"] - results[f"{cam_b}_roll_angle"])
				results[f"{cam_a}_{cam_b}_yaw_diff"] = np.abs(results[f"{cam_a}_yaw_angle"] - results[f"{cam_b}_yaw_angle"])
				results[f"{cam_a}_{cam_b}_pitch_diff"] = np.abs(results[f"{cam_a}_pitch_angle"] - results[f"{cam_b}_pitch_angle"])
			with open(f"{device.device_dir}/results.json", "w") as f:
				json.dump(results, f, indent=4)

		print(msg)

	if key == ord('q'):
		break