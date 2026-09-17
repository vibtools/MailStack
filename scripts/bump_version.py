import re, pathlib

ROOT = pathlib.Path('.')
OLD = '1.3.4'
NEW = '1.3.5'

# 1. VERSION
p = ROOT / 'VERSION'
p.write_text(NEW + '\n', encoding='utf-8')
print('VERSION: updated')

# 2. pyproject.toml
p = ROOT / 'mailbox-app' / 'pyproject.toml'
t = p.read_text(encoding='utf-8')
t2 = re.sub(r'(version\s*=\s*")1\.3\.4(")', r'\g<1>1.3.5\2', t)
p.write_text(t2, encoding='utf-8')
print('pyproject.toml: updated')

# 3. documents/DOCUMENTATION_MANIFEST.json
p = ROOT / 'documents' / 'DOCUMENTATION_MANIFEST.json'
t = p.read_text(encoding='utf-8')
t2 = t.replace(OLD, NEW)
p.write_text(t2, encoding='utf-8')
print('DOCUMENTATION_MANIFEST.json: updated')

# 4. documents/README.md
p = ROOT / 'documents' / 'README.md'
t = p.read_text(encoding='utf-8')
t2 = t.replace(OLD, NEW)
p.write_text(t2, encoding='utf-8')
print('documents/README.md: updated')

# 5. All documents/**/*.md frontmatter
for md in (ROOT / 'documents').rglob('*.md'):
    t = md.read_text(encoding='utf-8')
    t2 = re.sub(r'^(version:\s*)1\.3\.4$', r'\g<1>1.3.5', t, flags=re.MULTILINE)
    if t2 != t:
        md.write_text(t2, encoding='utf-8')
        print(f'{md.relative_to(ROOT)}: frontmatter updated')

# 6. MEMORY.md: update Active Release Identity line only
p = ROOT / 'MEMORY.md'
t = p.read_text(encoding='utf-8')
# Replace only the active release identity sentence
t2 = re.sub(
    r'(Maintained as `1\.3\.4` \(release tag `)v1\.3\.4(`\))',
    r'\g<1>v1.3.5\2'.replace('1.3.4', '1.3.5'),
    t
)
# Simpler targeted replace
t2 = t.replace(
    'Maintained as `1.3.4` (release tag `v1.3.4`)',
    'Maintained as `1.3.5` (release tag `v1.3.5`)'
)
p.write_text(t2, encoding='utf-8')
print('MEMORY.md: Active Release Identity updated')

# 7. Create docs/RELEASE_NOTES_1.3.5.md
notes_content = """# MailStack 1.3.5 - System Update UX and Bug Fixes

## Purpose

`1.3.5` delivers targeted bug fixes to the Admin Panel System Update page,
improving reliability and enforcing the correct confirmation-modal flow before
any update is triggered. No database migrations, architecture changes, or new
dependencies are introduced.

## Included corrections

- fix: "Install Update" button now always opens the confirmation modal before
  triggering the backend update; previously it bypassed the modal and called
  triggerUpdate() directly, violating the intended UX contract;
- fix: aggressive alert() on initial page-load update_status failure replaced
  with inline error display, consistent with the rest of the page error handling.

## Compatibility

No database migration, Postfix/Dovecot/LMTP/Maildir routing change, authorization
redesign, outbound mail capability, or installer-flow change is included.

## Qualification evidence

Passes forensic audit with BLOCKING_FINDINGS=0 and FORENSIC_AUDIT=PASS.
"""
notes = ROOT / 'docs' / 'RELEASE_NOTES_1.3.5.md'
notes.write_text(notes_content, encoding='utf-8')
print('docs/RELEASE_NOTES_1.3.5.md: created')

# 8. forensic_audit.py: add 1.3.5 entry after 1.3.4
p = ROOT / 'scripts' / 'forensic_audit.py'
t = p.read_text(encoding='utf-8')
if 'RELEASE_NOTES_1.3.5.md' not in t:
    t2 = t.replace(
        '    "docs/RELEASE_NOTES_1.3.4.md",',
        '    "docs/RELEASE_NOTES_1.3.4.md",\n    "docs/RELEASE_NOTES_1.3.5.md",'
    )
    p.write_text(t2, encoding='utf-8')
    print('forensic_audit.py: added 1.3.5 entry')
else:
    print('forensic_audit.py: 1.3.5 already present')

# 9. test_release_workflow.py: update expected RELEASE_NOTES reference
p = ROOT / 'scripts' / 'test_release_workflow.py'
t = p.read_text(encoding='utf-8')
t2 = t.replace(
    "'docs/RELEASE_NOTES_1.3.4.md',",
    "'docs/RELEASE_NOTES_1.3.5.md',"
)
p.write_text(t2, encoding='utf-8')
print('test_release_workflow.py: updated RELEASE_NOTES reference')

print()
print('=== Version bump complete: 1.3.4 -> 1.3.5 ===')
