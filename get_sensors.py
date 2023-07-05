import depthai as dai
with dai.Device() as d:
    print(d.getConnectedCameraFeatures())


