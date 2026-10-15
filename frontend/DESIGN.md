# Bright Smile Dental design system

The patient site and the staff dashboard share one system. Tokens live in `src/app/globals.css`.

## Point of view

A neighborhood family practice whose real differentiator is transparency: it publishes its prices, offers a
membership plan, and answers questions at any hour. The design is calm and plain-spoken, like a good front desk.
The one bold element on the patient site is the **price list**, set like a menu board with dotted leaders.
Everything around it stays quiet.

## Color

| Token                            | Hex                  | Use                                               |
| -------------------------------- | -------------------- | ------------------------------------------------- |
| Porcelain (`--background`)       | `#f7f8f5`            | page background                                   |
| Spruce ink (`--foreground`)      | `#12332b`            | text and headlines                                |
| Pine (`--primary`)               | `#1f6b57`            | primary actions, links, focus ring (6:1 on white) |
| Mist (`--border`, `--secondary`) | `#dce5e0`, `#e7eeea` | rules, quiet fills                                |
| Sunflower (`--accent`)           | `#f2c14e`            | offers only, always with spruce text              |

The palette comes from Montgomery County's tree canopy instead of the usual dental teal. Dark mode (dashboard)
inverts to spruce surfaces with a lighter pine.

## Type

- **Bricolage Grotesque** (`font-heading`): headlines only, tight tracking, balanced wrapping.
- **Lexend** (`font-sans`): body and UI. Designed from reading-proficiency research for easy reading, which suits
  an audience that includes older patients and parents reading on a phone. (Atkinson Hyperlegible was tried first;
  its slashed zero made phone numbers and prices read like code.)
- Body lines stay under about 70 characters. No all-caps labels, no eyebrow text above headings.

## Layout and components

- Left-aligned, single column on mobile, generous vertical rhythm. Sections are separated by space and hairline
  rules, not by stacks of identical cards.
- Numbered markers only for real sequences (the first-visit steps).
- shadcn/ui (`base-nova`) primitives. Deliberate extensions: `Button` sizes `xl` and `icon-xl` (44px touch target
  for patient-facing primary actions) and a `Badge` `accent` variant (sunflower, used for P2 high-value leads).
- Dashboard priority colors: P1 destructive, P2 accent, P3 primary, P4 secondary. Overdue is the only red text.
- Chat UI composes `MessageScroller`, `Message`, and `Bubble`.

## Writing

Plain verbs, sentence case, no em-dashes. Prices and facts come from `src/content/kb.json`, which is generated from
the backend knowledge base. Never type a price, hour, or insurer into a component.

## Motion

One moment only: the chat panel opening. Everything respects `prefers-reduced-motion`.
