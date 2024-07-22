import xml.etree.ElementTree as ET
import os
from datetime import datetime


def extract_well_coordinates(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    coordinates = {}
    for region in root.findall('.//SingleTileRegion'):
        name = region.get('Name')
        x = float(region.find('X').text)
        y = float(region.find('Y').text)
        coordinates[name] = (x, y)

    return coordinates

def extract_positions_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    positions = []
    for region in root.findall('.//SingleTileRegion'):
        x = float(region.find('X').text)
        y = float(region.find('Y').text)
        positions.append((x, y))

    return positions


def calculate_all_well_centers_from_reference(reference_well, reference_coords, horizontal_distance, vertical_distance):
    ref_x, ref_y = reference_coords
    rows = 'ABCD'
    cols = '123456'

    well_centers = {}
    for row in rows:
        y_offset = (ord(row) - ord(reference_well[0])) * vertical_distance

        for col in cols:
            well_name = f"{row}{col}"

            if well_name == reference_well:
                well_centers[well_name] = (ref_x, ref_y)
            else:
                ref_x_offset = ref_x + (int(col) - int(reference_well[1])) * horizontal_distance
                ref_y_offset = ref_y - y_offset
                well_centers[well_name] = (ref_x_offset, ref_y_offset)

    return well_centers


def apply_positions_to_wells(well_centers, positions, center_of_b6_from_previous_plate):
    well_positions = {}
    x_center_b6_prev, y_center_b6_prev = center_of_b6_from_previous_plate

    # Calculate relative positions from the previous plate's B6
    positions_relative_to_b6_prev = [(x - x_center_b6_prev, y - y_center_b6_prev) for x, y in positions]

    for well, (center_x, center_y) in well_centers.items():
        well_positions[well] = [(center_x + dx, center_y + dy) for dx, dy in positions_relative_to_b6_prev]

    return well_positions


def write_positions_to_file(output_folder, well, positions, template_file):
    tree = ET.parse(template_file)
    root = tree.getroot()
    single_tile_regions = root.find('.//SingleTileRegions')

    # Remove existing regions
    for region in list(single_tile_regions):
        single_tile_regions.remove(region)

    for i, (x, y) in enumerate(positions):
        region = ET.Element("SingleTileRegion", Name=f"P{i + 1}")
        ET.SubElement(region, "X").text = str(x)
        ET.SubElement(region, "Y").text = str(y)
        ET.SubElement(region, "Z").text = "5048.87"  # Adjust Z if needed
        ET.SubElement(region, "IsUsedForAcquisition").text = "true"
        single_tile_regions.append(region)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    tree.write(os.path.join(output_folder, f"{well}.czexp"), encoding="utf-8", xml_declaration=True)


REFERENCE_WELL = 'A1'
REFERENCE_WELL_COORDINATES = (41873, 26300.75)  # Example coordinates for the reference well
POSITIONS_FILE = '../data/LA2_220724_25positions.czexp'
WELL_COORDINATES_FILE = '../data/LA_220724_centres.czexp'


def main():
    # Extract coordinates and positions
    coordinates = extract_well_coordinates(WELL_COORDINATES_FILE)
    positions = extract_positions_from_xml(POSITIONS_FILE)

    # Extract distances from the coordinates
    x_a6, y_a6 = coordinates.get('A6', (None, None))
    x_a5, y_a5 = coordinates.get('A5', (None, None))
    x_b6, y_b6 = coordinates.get('B6', (None, None))

    if None in (x_a6, y_a6, x_a5, y_a5, x_b6, y_b6):
        raise ValueError("Missing coordinates for one or more wells.")

    horizontal_distance = x_a6 - x_a5
    vertical_distance = y_a6 - y_b6

    # Calculate all well c
    # enters based on the reference well
    well_centers = calculate_all_well_centers_from_reference(REFERENCE_WELL, REFERENCE_WELL_COORDINATES, horizontal_distance, vertical_distance)
    print("Well Centers:")
    for well, (x, y) in well_centers.items():
        print(f"{well}: X = {x}, Y = {y}")

    # Get the center of B6 from the previous plate - Using x_a6 as in main.py (Lara said it might be more accurate)
    center_of_b6_from_previous_plate = (x_a6, y_b6)
    # Apply positions to all wells
    well_positions = apply_positions_to_wells(well_centers, positions, center_of_b6_from_previous_plate)

    # Create the output folder path with the current date and time
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M")
    output_folder = os.path.join("..", "output", f"{current_datetime}_24wp_25positions")

    # Write positions to files
    for well, positions in well_positions.items():
        write_positions_to_file(output_folder, well, positions, POSITIONS_FILE)


if __name__ == '__main__':
    main()

