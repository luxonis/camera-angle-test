import json
import matplotlib.pyplot as plt
import argparse

def angular_difference(angle1, angle2):
    """
    Calculate the smallest difference between two angles.
    """
    # First calculate the difference between the angles
    abs_difference = abs(angle1 - angle2)
    dist_0 = abs(abs_difference)
    dist_360 = abs(360 - abs_difference)
    dist_minus_360 = abs(360 + abs_difference)
    # Then return the smallest difference
    # print(f"dist_0: {dist_0}, dist_360: {dist_360}, dist_minus_360: {dist_minus_360}")
    minDistance = min(dist_0, dist_360, dist_minus_360)
    print(f"minDistance: {minDistance}")
    return minDistance

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def compare_data(data1, data2):
    differences = {}
    for key in data1:
        if "rectified" in key:
            continue # Skip rectified images
        if "diff" in key:
            # Special handling for angles
            diff = angular_difference(data2[key], data1[key])
            differences[key] = diff
        else:
            continue # Only compare differences
    return differences

def plot_differences(differences):
    keys = list(differences.keys())
    values = list(differences.values())
    plt.figure(figsize=(15,10))
    plt.barh(keys, values, color=['red' if v < 0 else 'blue' for v in values])
    plt.xlabel('Difference in degrees')
    plt.title("Relative angle differences between two measurements")
    # Set max value to 2 degrees
    plt.xlim(0, 2)
    plt.tight_layout()
    plt.show()

def main(args):
    data1 = load_json(args.file1)
    data2 = load_json(args.file2)

    differences = compare_data(data1, data2)
    plot_differences(differences)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Compare two JSON files and visualize the differences.")
    parser.add_argument("file1", type=str, help="Path to the first JSON file")
    parser.add_argument("file2", type=str, help="Path to the second JSON file")
    args = parser.parse_args()

    main(args)