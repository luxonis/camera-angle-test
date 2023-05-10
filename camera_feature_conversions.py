
import depthai as dai

# Conversion between and CameraBoardSocket enum and string representation
def cam_to_str(cam: dai.CameraBoardSocket) -> str:
	return cam.name

def str_to_cam(cam: str) -> dai.CameraBoardSocket:
	return dai.CameraBoardSocket.__members__[cam]


# Mapping between sensor name and resolution
cam_to_mono_res_dict = {
	'OV7251' : dai.MonoCameraProperties.SensorResolution.THE_480_P,
	'OV9*82' : dai.MonoCameraProperties.SensorResolution.THE_800_P,
	'OV9282' : dai.MonoCameraProperties.SensorResolution.THE_800_P,
	'AR0234' : dai.ColorCameraProperties.SensorResolution.THE_1200_P,
}

cam_to_rgb_res_dict = {
	'IMX378' : dai.ColorCameraProperties.SensorResolution.THE_4_K,
	'IMX214' : dai.ColorCameraProperties.SensorResolution.THE_4_K,
	'OV9*82' : dai.ColorCameraProperties.SensorResolution.THE_800_P,
	'OV9282' : dai.ColorCameraProperties.SensorResolution.THE_800_P,
	'OV9782' : dai.ColorCameraProperties.SensorResolution.THE_800_P,
	'IMX582' : dai.ColorCameraProperties.SensorResolution.THE_12_MP,
	'LCM48' : dai.ColorCameraProperties.SensorResolution.THE_12_MP, # Same as IMX582
	'AR0234' : dai.ColorCameraProperties.SensorResolution.THE_1200_P,
}

if hasattr(dai.ColorCameraProperties.SensorResolution, 'THE_4000X3000'):
	cam_to_rgb_res_dict['imx412'] = dai.ColorCameraProperties.SensorResolution.THE_4000X3000

if hasattr(dai.ColorCameraProperties.SensorResolution, 'THE_1200_P'):
    cam_to_rgb_res_dict['AR0234'] = dai.ColorCameraProperties.SensorResolution.THE_1200_P

cam_to_mono_res = cam_to_mono_res_dict.get
cam_to_rgb_res = cam_to_rgb_res_dict.get