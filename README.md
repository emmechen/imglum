# imglum

Generates color-at-luminance backgrounds from a folder of images.

## What you need
- A Mac with Terminal (Applications > Utilities > Terminal)
- Git (Terminal will offer to install it the first time you use it)
- Mamba or conda. If you don't have either, install Miniforge:
  https://github.com/conda-forge/miniforge
  Download the installer that matches your Mac (Apple Silicon or Intel),
  run it, then close and reopen Terminal.
- If the repo is private, a GitHub account that has been added as a collaborator

## One-time setup

1. Choose where to keep the project and go there (Documents is fine):

       cd ~/Documents

2. Download the repo:

       git clone https://github.com/YOUR-USERNAME/imglum.git

   (If the repo is private, sign in when prompted. See "Signing in" below.)

3. Go into the project folder:

       cd imglum

4. Build the environment (takes a few minutes):

       mamba env create -f environment.yml

   If you use conda, replace `mamba` with `conda`.

## Running the script

Each time you want to use it:

1. Open Terminal and activate the environment:

       mamba activate imgbg

   Your prompt should now start with (imgbg).

2. Go to the project folder:

       cd ~/Documents/imglum

3. Run the script on a folder of images. Type this with a trailing space:

       python color_at_luminance_backgrounds.py

   Then drag your image folder from Finder into Terminal and press Enter.
   Or type the path yourself, using quotes if it contains spaces:

       python color_at_luminance_backgrounds.py "/path/to/image_folder"

## Getting updates

If the script or environment has changed:

    cd ~/Documents/imglum
    git pull
    mamba env update -f environment.yml --prune

## Signing in (private repos only)

The easiest method is the GitHub CLI:

    brew install gh
    gh auth login

Choose GitHub.com, then HTTPS, then "Login with a web browser", and enter
the one-time code in your browser. If you don't have Homebrew, install
GitHub Desktop (https://desktop.github.com) and clone the repo from there.

## Troubleshooting

- **"mamba: command not found"**: Close and reopen Terminal. If it persists,
  Miniforge isn't installed. Use `conda` instead if you have it.
- **"No such file or directory"**: You're in the wrong folder, or the path
  has spaces and needs quotes. Run `ls` to confirm you can see
  color_at_luminance_backgrounds.py.
- **"ModuleNotFoundError"**: Make sure (imgbg) shows at the start of your
  prompt. If not, run `mamba activate imgbg`.
- **"An environment named imgbg already exists"**: Run
  `mamba env update -f environment.yml` instead of `create`.