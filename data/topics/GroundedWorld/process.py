import os
from glob import glob
from comtypes import client


def convert_pptx_to_pdf(pptx_path, pdf_path):
    if not os.path.exists(pptx_path):
        raise FileNotFoundError(f"The file {pptx_path} does not exist.")

    # Initialize PowerPoint application
    powerpoint = client.CreateObject("PowerPoint.Application")
    powerpoint.Visible = 1  # Optional: Makes the process visible for debugging

    # Open the presentation
    presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)

    # Save as PDF
    try:
        presentation.SaveAs(pdf_path, FileFormat=32)  # 32 = PDF format
    finally:
        # Clean up
        presentation.Close()
        powerpoint.Quit()

    print(f"Converted {pptx_path} to {pdf_path}")


if __name__ == "__main__":
    # Get all .pptx files in the current directory
    current_folder = os.getcwd()
    pptx_files = glob(os.path.join(current_folder, "*.pptx").replace("\\", "/"))

    # Convert each .pptx file to PDF
    for pptx_file in pptx_files:
        pdf_file = os.path.splitext(pptx_file)[0] + ".pdf"
        convert_pptx_to_pdf(pptx_file, pdf_file)
