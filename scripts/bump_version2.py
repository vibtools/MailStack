import pathlib

ROOT = pathlib.Path('.')

# 1. docs/PUBLISHING.md - update version-specific commands
p = ROOT / 'docs' / 'PUBLISHING.md'
t = p.read_text(encoding='utf-8')
t2 = t.replace('1.3.4', '1.3.5')
p.write_text(t2, encoding='utf-8')
print('docs/PUBLISHING.md: updated')

# 2. docs/RELEASE_PROCESS.md - update version example
p = ROOT / 'docs' / 'RELEASE_PROCESS.md'
t = p.read_text(encoding='utf-8')
t2 = t.replace('1.3.4', '1.3.5')
p.write_text(t2, encoding='utf-8')
print('docs/RELEASE_PROCESS.md: updated')

# 3. design/DESIGN_MANIFEST.json - update release_version
p = ROOT / 'design' / 'DESIGN_MANIFEST.json'
t = p.read_text(encoding='utf-8')
old_rv = '"release_version": "1.3.4"'
new_rv = '"release_version": "1.3.5"'
t2 = t.replace(old_rv, new_rv)
p.write_text(t2, encoding='utf-8')
print('design/DESIGN_MANIFEST.json: updated')

print('Done.')
