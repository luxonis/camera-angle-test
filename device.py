import depthai as dai
from typing import List, Union, Optional, Dict
from depthai_helpers.camera_feature_conversions import cam_to_mono_res, cam_to_rgb_res
import numpy as np
import cv2
from pathlib import Path

class Device:
	def __init__(self, device_info: dai.DeviceInfo):
		self.device = dai.Device(device_info)
		self.last_frame: Dict[str, np.ndarray] = {}
		self.device_dir = Path(__file__).parent / "data" / self.device.getMxId()
		self.device_dir.mkdir(parents=True, exist_ok=True)

		print(f"Connecting to {self.device.getMxId()}")	
		self.calibration = self.device.readCalibration2()


		# create pipeline
		self.pipeline = dai.Pipeline()
		# create a stream for each camera
		self.camera_nodes: List[Union[dai.node.ColorCamera, dai.node.MonoCamera]] = []
		self.left_camera: Optional[Union[dai.node.ColorCamera, dai.node.MonoCamera]] = None
		self.right_camera: Optional[Union[dai.node.ColorCamera, dai.node.MonoCamera]] = None
		for camera in self.device.getConnectedCameraFeatures():
			xout = self.pipeline.createXLinkOut()
			xout.setStreamName(camera.name)

			if dai.CameraSensorType.COLOR in camera.supportedTypes:
				# create color camera
				cam_node = self.pipeline.createColorCamera()
				cam_node.setBoardSocket(camera.socket)
				res = cam_to_rgb_res(camera.sensorName)
				if res is not None:
					cam_node.setResolution(res)
				cam_node.setIspScale(2, 3)
				cam_node.isp.link(xout.input)
			elif dai.CameraSensorType.MONO in camera.supportedTypes:
				# create mono camera
				cam_node = self.pipeline.createMonoCamera()
				cam_node.setBoardSocket(camera.socket)
				res = cam_to_mono_res(camera.sensorName)
				if res is not None: 
					cam_node.setResolution(res)
				cam_node.out.link(xout.input)
			else:
				# unsupported sensor type
				continue
			if camera.socket == self.calibration.getStereoLeftCameraId():
				self.left_camera = cam_node
			if camera.socket == self.calibration.getStereoRightCameraId():
				self.right_camera = cam_node
			self.camera_nodes.append(cam_node)

		if self.left_camera is not None and self.right_camera is not None:
			# create a depth stream and rectified left/right stream for default stereo pair
			stereo_depth = self.pipeline.createStereoDepth()
			stereo_depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
			stereo_depth.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
			stereo_depth.setLeftRightCheck(False)
			stereo_depth.setExtendedDisparity(False)
			stereo_depth.setSubpixel(False)
			stereo_depth.setDepthAlign(dai.CameraBoardSocket.LEFT)
			stereo_depth.setConfidenceThreshold(250)

			if isinstance(self.left_camera, dai.node.ColorCamera):
				self.left_camera.isp.link(stereo_depth.left)
			else:
				self.left_camera.out.link(stereo_depth.left)
			
			if isinstance(self.right_camera, dai.node.ColorCamera):
				self.right_camera.isp.link(stereo_depth.right)
			else:
				self.right_camera.out.link(stereo_depth.right)

			xout_depth = self.pipeline.createXLinkOut()
			xout_depth.setStreamName("depth")
			xout_rectified_left = self.pipeline.createXLinkOut()
			xout_rectified_left.setStreamName("rectified_left")
			xout_rectified_right = self.pipeline.createXLinkOut()
			xout_rectified_right.setStreamName("rectified_right")

			stereo_depth.depth.link(xout_depth.input)
			stereo_depth.rectifiedLeft.link(xout_rectified_left.input)
			stereo_depth.rectifiedRight.link(xout_rectified_right.input)



		self.device.startPipeline(self.pipeline)

		# get the quueues
		self.camera_queues: Dict[str, dai.DataOutputQueue] = {}

		for camera in self.device.getConnectedCameraFeatures():
			self.camera_queues[camera.name] = self.device.getOutputQueue(name=camera.name, maxSize=1, blocking=False)

		self.camera_queues["rectified_left"] = self.device.getOutputQueue("rectified_left")
		self.camera_queues["rectified_right"] = self.device.getOutputQueue("rectified_right")

		self.depth_queue = self.device.getOutputQueue("depth")

	def update(self):
		res: Dict[str, np.ndarray] = {}
		for name, queue in self.camera_queues.items():
			msg = queue.tryGet()
			if msg is not None:
				img = msg.getCvFrame() # type: ignore
				res[name] = img
				self.last_frame[name] = img

		depth_msg = self.depth_queue.tryGet()

		return res


	def update_debug(self):
		for name, queue in self.camera_queues.items():
			msg = queue.tryGet()
			if msg is not None:
				img = msg.getCvFrame() # type: ignore

				# downscale image to max 640x480
				img_downscaled = cv2.resize(img, (640, 480), interpolation=cv2.INTER_AREA)

				self.last_frame[name] = img
				cv2.imshow(name, img_downscaled)

		depth_msg = self.depth_queue.tryGet()

		key = cv2.waitKey(1)

		if key == ord('s'):
			for name, img in self.last_frame.items():
				cv2.imwrite(f"{self.device_dir}/{name}.png", img)


if __name__ == "__main__":
	found, device_info = dai.Device.getFirstAvailableDevice() # type: ignore

	if not found:
		raise Exception("No device connected!")
	
	device = Device(device_info)

	while True:
		device.update_debug()
