import os
import argparse
from xml.etree import ElementTree as ET

def split_svg(svg_file, output_folder):
    # Parse the input SVG file
    tree = ET.parse(svg_file)
    root = tree.getroot()

    # Define SVG namespace
    namespaces = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', namespaces['svg'])

    # Find all symbols in the SVG
    symbols = root.findall('.//svg:symbol', namespaces)

    # Process each symbol
    for symbol in symbols:
        symbol_id = symbol.get('id')
        if not symbol_id:
            continue  # Skip symbols without an id

        # Create a new SVG tree with the content of the symbol
        new_svg = ET.Element('svg')
        
        # Copy necessary attributes like viewBox, if they exist
        if 'viewBox' in symbol.attrib:
            new_svg.set('viewBox', symbol.attrib['viewBox'])

        # Append all elements inside the symbol to the new SVG
        for child in symbol:
            new_svg.append(child)

        # Create a new SVG file for each symbol
        output_file = os.path.join(output_folder, f"{symbol_id}.svg")
        with open(output_file, 'wb') as f:
            f.write(ET.tostring(new_svg, encoding='utf-8', xml_declaration=True))

        print(f"Created: {output_file}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Split a large SVG file with multiple symbols into separate SVG files.')
    parser.add_argument('input_svg', type=str, help='Path to the input SVG file.')
    parser.add_argument('output_folder', type=str, help='Path to the folder where the individual SVG files will be saved.')

    # Parse arguments
    args = parser.parse_args()

    # Create output folder if it doesn't exist
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    # Call the split function
    split_svg(args.input_svg, args.output_folder)

if __name__ == '__main__':
    main()
