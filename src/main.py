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


def calculate_all_well_centers(coords):
    REFERENCE_WELL = 'A6'
    x_a6, y_a6 = coords.get('A6', (None, None))
    x_a5, y_a5 = coords.get('A5', (None, None))
    x_b6, y_b6 = coords.get('B6', (None, None))

    if None in (x_a6, y_a6, x_a5, y_a5, x_b6, y_b6):
        raise ValueError("Missing coordinates for one or more wells.")

    horizontal_distance = x_a6 - x_a5
    vertical_distance = y_a6 - y_b6

    rows = 'ABCD'
    cols = '123456'

    well_centers = {}
    for row in rows:
        y_offset = (ord(row) - ord(REFERENCE_WELL[0])) * vertical_distance

        for col in cols:
            well_name = f"{row}{col}"

            if well_name == 'A6':
                ref_x, ref_y = x_a6, y_a6
            else:
                ref_x = x_a6 + (int(col) - int(REFERENCE_WELL[1])) * horizontal_distance
                ref_y = y_a6 - y_offset

            well_centers[well_name] = (ref_x, ref_y)

    return well_centers


def apply_positions_to_wells(well_centers, positions, center_of_b6):
    well_positions = {}
    x_center_b6, y_center_b6 = center_of_b6

    # Calculate relative positions from B6
    positions_relative_to_b6 = [(x - x_center_b6, y - y_center_b6) for x, y in positions]

    for well, (center_x, center_y) in well_centers.items():
        well_positions[well] = [(center_x + dx, center_y + dy) for dx, dy in positions_relative_to_b6]

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


def main():
    # Define the paths to your XML files
    well_coordinates_file = '../data/LA_220724_centres.czexp'
    positions_file = '../data/LA2_220724_25positions.czexp'

    # Extract coordinates and positions
    coordinates = extract_well_coordinates(well_coordinates_file)
    positions = extract_positions_from_xml(positions_file)

    # Calculate all well centers
    well_centers = calculate_all_well_centers(coordinates)

    # Get the center of well B6
    center_of_b6 = well_centers.get('B6', (None, None))
    if None in center_of_b6:
        raise ValueError("Missing coordinates for well B6.")

    # Apply positions to all wells
    well_positions = apply_positions_to_wells(well_centers, positions, center_of_b6)

    # Create the output folder path with the current date
    current_date = datetime.now().strftime("%Y%m%d")
    output_folder = os.path.join("..", "output", f"{current_date}_24wp_25positions")

    # Write positions to files
    for well, positions in well_positions.items():
        write_positions_to_file(output_folder, well, positions, positions_file)


if __name__ == '__main__':
    main()
