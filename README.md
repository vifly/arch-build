Use GitHub Actions to build Arch packages.
For more information, please read [my post](https://viflythink.com/Use_GitHubActions_to_build_AUR/) (Chinese).

The uploadToOneDrive job is optional, you can use [urepo](https://github.com/vifly/urepo) to create your package repositories after uploading to OneDrive. Thanks https://github.com/vifly/arch-build/pull/8 , so you can choose other cloud storage rclone support, but the action input are changed, remember to update your secrets.

# Usage
The packages are located at OneDrive and GitHub releases, choose one of you like.

Add the following code snippet to your `/etc/pacman.conf` (choose one):

```
# Download from OneDrive
[vifly]
Server = https://archrepo.viflythink.com
```

```
# Download from GitHub releases
[vifly]
Server = https://github.com/vifly/arch-build/releases/latest/download
```

And import my pubkey:

```Bash
wget -O /tmp/vifly-repo.key 'https://share.viflythink.com/arch-repo.key' && sudo pacman-key --add /tmp/vifly-repo.key
sudo pacman-key --lsign-key viflythink@gmail.com
```

Then, run `sudo pacman -Syu` to update the repository and upgrade the system.

Now you can use `sudo pacman -S <pkg_name>` to install packages from my repository.

# TODO
- [ ] some actions are too coupled, need to refactor
- [ ] add more clear output log for debug
