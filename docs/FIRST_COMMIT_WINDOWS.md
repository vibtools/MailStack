# First commit from Windows

Use Git for Windows from the project directory. The explicit index-mode commands ensure shell programs are executable in Linux checkouts and release archives.

```cmd
git init -b main
git remote add origin https://github.com/vibtools/MailStack.git
git add --all
git update-index --chmod=+x install.sh
for /r %F in (*.sh) do @git update-index --chmod=+x "%F"
git commit -m "chore: bootstrap MailStack open-source repository"
git push -u origin main
```

In a `.cmd` file, use `%%F` instead of `%F`. After push, require the GitHub Actions CI workflow to pass before deleting the pre-replacement backup or the former repository.
