# UI Design Reference and Screenshot Defect Matrix

## Design authority for the next update

MailStack keeps its own product identity. The reference inputs are used in this order:

1. **MailStack v1.3.3 current behavior/business contracts** — functional authority.
2. **Owner-supplied screenshots and annotations** — defect/acceptance authority.
3. **VibTools Web UI v2.1.2** — structural geometry, typography, density and component-system reference.
4. **Licora v5.5.0** — implementation-pattern reference showing how VibTools structure can be mapped onto a
   different product theme without copying the reference product's branding.

## VibTools structural values extracted

| Role | Reference value |
|---|---:|
| Primary UI text | `13px` |
| Micro labels/badges | `11px` |
| Controls/helper | `12px` |
| Compact heading | `14px` |
| Section header | `16px` |
| Page title cap | `20px` |
| Expanded sidebar | `196px` |
| Topbar | `44px` |
| Small button | `28px` |
| Medium button | `32px` |
| Small input | `30px` |
| Medium input | `34px` |
| Card padding | `10px 12px` |
| Radius small/control/card | `6px / 8px / 12px` |
| Card shadow | none / border-driven |
| Normal transition | `120ms ease` |

## Current MailStack structural values causing density mismatch

| Role | v1.3.3 current value | Forensic interpretation |
|---|---:|---|
| Base font | `1rem` (~16px) | materially larger than reference |
| Sidebar | `256px` | too wide for compact target |
| Collapsed sidebar | `80px` | oversized icon rail |
| Topbar | `72px` | too tall for compact target |
| General table cell padding | `13px 15px` | heavy for operational tables |
| Mailbox filter controls | `38px` | above compact control target |
| Inbox row min height | `58px` | denser than old UI but still above compact target |
| Reader HTML iframe | `clamp(460px,65vh,800px)` | large nested scroll surface |
| General radius | `14px` | softer/larger than compact reference |
| General shadow | broad card shadow token | more decorative than reference |

## Theme preservation rule

Do not copy VibTools dark colors into MailStack production UI.

MailStack must retain:
- light application background;
- white/light surfaces;
- existing MailStack blue primary action identity;
- semantic green/amber/red statuses;
- MailStack logo and naming.

The update changes **structure and scale**, not product identity.

## Screenshot defect matrix

| ID | Screen / annotation | Defect | Severity | Target phase |
|---|---|---|---|---|
| BUG-001 | HTML message reader top/body | Protected-rendering banner + raw CSS leakage | BLOCKER | PHASE-006 |
| BUG-002 | HTML reader lower body/footer | Body composition too tall; broken blocked image; public footer links | BLOCKER/Major | 006 + 007 |
| BUG-003 | 400px Mailboxes view | Generic table-card conversion is extremely tall | Major | PHASE-007 |
| BUG-004 | Collapsed navigation/dashboard | Icon rail too wide/unfinished; wasted space | Major | PHASE-007 |
| BUG-005 | Create mailbox | Form card too large/sparse; multi-select dated | Medium | PHASE-007 |
| BUG-006 | User management | Table density/alignment/actions poor | Major | PHASE-007 |
| BUG-007 | Add user | Oversized form controls/help block/dead space | Medium | PHASE-007 |

## Component-specific target structure

### Shell
- desktop: fixed compact expanded sidebar;
- optional compact icon collapse;
- tablet/mobile: off-canvas drawer;
- topbar contains context/account only, not duplicate primary navigation;
- workspace width is fluid and does not reserve unnecessary dead space.

### Mailboxes
Desktop row priority:
1. mailbox address;
2. status;
3. unread / total;
4. last received;
5. compact actions.

Mobile card/list priority:
1. address + status;
2. unread/total + last received;
3. compact secondary/action row.

### Inbox
Desktop target:
`status dot | sender | subject + preview | attachment/meta | time`

Mobile target:
- sender/time first line;
- subject second line;
- preview/meta optional third compact line;
- no oversized row cards.

### Reader
- one compact header;
- sender/routing metadata expandable;
- action buttons compact;
- body immediately readable;
- no permanent security warning strip;
- attachments immediately follow body;
- no public footer clutter.

### Forms
- compact input/button height;
- smaller page-title/helper copy;
- clear groups rather than oversized cards;
- responsive widths use available space intelligently;
- validation remains directly adjacent to affected controls.

## UI anti-regression rules

- No page-specific hardcoded typography system.
- No new shadow/elevation system.
- No horizontal viewport overflow.
- No action accessible only by hover.
- No icon-only action without accessible label/title.
- No destructive action bypassing server-side permission/CSRF/confirmation.
- No change to route names, field names or JavaScript hooks solely for styling convenience.
- No public-site promotional navigation inside the authenticated operational workspace.
