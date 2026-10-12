# imglum

Generates color-at-luminance backgrounds from a folder of images.

## Setup (one time)
Requires mamba or conda. Install Miniforge if you don't have it:
https://github.com/conda-forge/miniforge

    git clone https://github.com/YOUR-USERNAME/imglum.git
    cd imglum
    mamba env create -f environment.yml

## Run
    mamba activate imgbg
    python color_at_luminance_backgrounds.py /path/to/image_folder

Tip: type `python color_at_luminance_backgrounds.py ` (with a trailing
space), drag the image folder from Finder into Terminal, then press Enter.

## Updating
If the environment file changes:

    git pull
    mamba env update -f environment.yml