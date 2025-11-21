# Deal Template Reference Guide

This document explains the normalized structure of deal templates based on analysis of all existing templates in the `v2-deals` folder.

## Overview

Deal templates are JSON files that define user interactions including:
- Form generation with conditional fields
- Capacity controls for limited options
- Branding and styling
- Authentication requirements
- SMS notifications
- Integration with punch cards and rewards

## Template Structure

### Top-Level Properties

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `biz_id` | Yes | string | Business identifier (must exist in graph) |
| `check_in` | No | boolean | If `true`, deal auto-grabs without confirmation |
| `auth_required` | No | boolean | If `true`, user must authenticate before access |
| `error_auth` | No | object | Custom error message when auth fails |
| `styling` | No | object | Custom fonts for branding |
| `FORM` | No | object | Form definition (if present, shown before MAIN) |
| `MAIN` | Yes | object | Confirmation page content |
| `PUNCHCARDS` | No | array | Punch card templates to activate |
| `REWARDS` | No | array | Reward templates available for redemption |
| `limit` | No | object | Deal-level usage limit |

### FORM Structure

| Property | Required | Type | Description |
|----------|----------|------|-------------|
| `title` | No | string | Form title displayed at top |
| `fields` | Yes | array | Array of field definitions |
| `limits` | No | object | Capacity calculation settings |
| `submit` | No | object | Submit button customization |
| `notify` | No | object | SMS notification configuration |

### Field Types

#### 1. `info` - Markdown Content
Non-input field for displaying formatted text.

```json
{
  "type": "info",
  "justify": "center",
  "markdown": "# Header\n\n**Bold** text"
}
```

**Properties:**
- `justify`: Optional - `"left"`, `"center"`, or `"right"`
- `markdown`: Required - Markdown content

#### 2. `text` - Text Input
Single-line text input.

```json
{
  "id": "name",
  "type": "text",
  "label": "Name:",
  "placeholder": "Enter name",
  "required": true,
  "sticky": false,
  "disabled": false,
  "hidden": false
}
```

#### 3. `email` - Email Input
Text input with email validation.

```json
{
  "id": "email",
  "type": "email",
  "label": "Email:",
  "required": true,
  "sticky": true
}
```

#### 4. `textarea` - Multi-line Text
Multi-line text input.

```json
{
  "id": "comments",
  "type": "textarea",
  "label": "Comments:",
  "rows": 3,
  "required": false
}
```

**Properties:**
- `rows`: Optional - Number of visible rows

#### 5. `select` - Single Selection
Dropdown for selecting one option.

**Simple format (string array):**
```json
{
  "id": "choice",
  "type": "select",
  "label": "Choose:",
  "range": ["Option 1", "Option 2", "Option 3"],
  "required": true
}
```

**Object format (with capacity limits):**
```json
{
  "id": "timeslot",
  "type": "select",
  "label": "Choose time:",
  "limit": 100,
  "nomore_text": "All slots full",
  "range": [
    {
      "value": "5:00 PM",
      "count": 1,
      "limit": 25,
      "claimed": 0
    }
  ],
  "required": true
}
```

**Capacity Control:**
- `limit` (field-level): Total capacity across all options
- `limit` (option-level): Capacity for specific option
- `count`: How many capacity units this option consumes
- `claimed`: Populated by server during pre-processing
- `nomore_text`: Message when all options are at capacity

#### 6. `multi-select` - Multiple Selection
Allows selecting multiple options.

```json
{
  "id": "interests",
  "type": "multi-select",
  "label": "Select all that apply:",
  "range": ["Option A", "Option B", "Option C"],
  "required": false
}
```

#### 7. `checkbox` - Boolean Checkbox
Single checkbox for boolean values.

```json
{
  "id": "agree",
  "type": "checkbox",
  "label": "I agree to terms",
  "required": true
}
```

#### 8. `characters` - Character Input
Character-by-character input (e.g., for monograms).

```json
{
  "id": "monogram",
  "type": "characters",
  "label": "Enter monogram:",
  "count": 3,
  "required": true
}
```

**Properties:**
- `count`: Required - Number of character inputs

#### 9. `image` - Image Upload
Photo capture or image upload.

```json
{
  "id": "photo",
  "type": "image",
  "required": false
}
```

#### 10. `fields_group` - Field Container
Groups fields with optional background color.

```json
{
  "type": "fields_group",
  "bgcolor": "#c8f0fc",
  "fields": [
    {
      "id": "name",
      "type": "text",
      "label": "Name:",
      "required": true
    }
  ]
}
```

**Properties:**
- `bgcolor`: Optional - Background color (hex code)
- `fields`: Required - Array of field definitions

### Conditional Fields

Fields can be conditionally shown based on other field values.

**Simple condition (single field, single value):**
```json
{
  "id": "conditional_field",
  "type": "text",
  "label": "Appears when 'choice' equals 'Option 1'",
  "conditional": {
    "field": "choice",
    "value": "Option 1"
  }
}
```

**Complex condition (multiple fields, AND logic):**
```json
{
  "id": "conditional_field",
  "type": "text",
  "label": "Appears when multiple conditions met",
  "conditional": [
    {
      "field": "choice",
      "value": "Option 1"
    },
    {
      "field": "agree",
      "value": true
    }
  ]
}
```

**Match one of multiple values:**
```json
{
  "id": "conditional_field",
  "type": "text",
  "label": "Appears when field matches any value",
  "conditional": {
    "field": "choice",
    "values": ["Option 1", "Option 2"]
  }
}
```

### Field Properties

Common properties available on most field types:

| Property | Type | Description |
|----------|------|-------------|
| `id` | string | Unique identifier (required for input fields) |
| `type` | string | Field type (required) |
| `label` | string | Display label |
| `required` | boolean | Whether field is required |
| `disabled` | boolean | Whether field is read-only |
| `hidden` | boolean | Whether field is hidden (value still submitted) |
| `sticky` | boolean | Whether value persists across deals for this business |
| `placeholder` | string | Placeholder text |
| `conditional` | object/array | Conditional display logic |

### Capacity Limits

Capacity limits control availability of options in select fields.

**Field-level limit:**
```json
{
  "id": "timeslot",
  "type": "select",
  "limit": 100,
  "range": [...]
}
```

**Option-level limits:**
```json
{
  "id": "timeslot",
  "type": "select",
  "range": [
    {
      "value": "5:00 PM",
      "count": 1,
      "limit": 25
    },
    {
      "value": "7:00 PM",
      "count": 2,
      "limit": 25
    }
  ]
}
```

**Capacity calculation settings:**
```json
{
  "limits": {
    "most_recent_only": true,
    "most_recent_key": "PlayerID"
  }
}
```

- `most_recent_only`: If `true`, only count most recent grab per user (useful for RSVPs)
- `most_recent_key`: Field ID to identify unique users (typically `PlayerID`)

### SMS Notifications

Forms can trigger SMS notifications when users opt in.

```json
{
  "notify": {
    "opt_in": "contact",
    "message": "(from {_mob}) {name} requested contact: {comments}",
    "mobiles": ["+1234567890", "+0987654321"]
  }
}
```

**Properties:**
- `opt_in`: Field ID that must be checked/selected to trigger
- `message`: Template with field substitutions (`{_mob}` is user's mobile)
- `mobiles`: Array of phone numbers to receive notifications

### Styling

Custom fonts for branding.

```json
{
  "styling": {
    "fonts": {
      "headers": {
        "family": "Raleway",
        "weight": 700,
        "style": "italic"
      },
      "body": {
        "family": "Raleway",
        "weight": "normal"
      },
      "formlabels": {
        "family": "Raleway",
        "weight": "bold"
      }
    }
  }
}
```

### MAIN Page

Confirmation page shown after form submission.

```json
{
  "MAIN": {
    "title": "Thank You!",
    "body_md": "# Confirmation\n\nThank you for your submission!"
  }
}
```

**Properties:**
- `title`: Optional - Page title
- `body_md`: Required - Markdown content

### Punch Cards

Activate punch card tracking.

```json
{
  "PUNCHCARDS": [
    {
      "template": "loyalty_card.json"
    }
  ]
}
```

### Rewards

Make rewards available for redemption.

```json
{
  "REWARDS": [
    {
      "template": "reward1.json"
    }
  ]
}
```

### Deal-Level Limits

Limit how often a deal can be claimed.

```json
{
  "limit": {
    "type": "day",
    "message": "You've already claimed this deal today."
  }
}
```

**Types:**
- `"day"`: Once per day
- `"onetime"`: Once ever

## Common Patterns

### Pattern 1: Sticky + Disabled Fields
Display user profile data that's pre-filled and read-only.

```json
{
  "id": "z_FIRSTNAME",
  "type": "text",
  "label": "First Name:",
  "sticky": true,
  "disabled": true
}
```

**Note:** Fields prefixed with `z_` are typically system fields from user profile.

### Pattern 2: Hidden Context Fields
Store context data that's not visible to user.

```json
{
  "id": "DIST",
  "type": "text",
  "hidden": true,
  "sticky": true
}
```

### Pattern 3: Nested Conditional Fields
Show different options based on previous selections.

```json
{
  "id": "attend",
  "type": "select",
  "range": ["Yes", "No"]
},
{
  "id": "time",
  "type": "select",
  "conditional": {
    "field": "attend",
    "value": "Yes"
  }
}
```

### Pattern 4: Capacity-Controlled RSVP
RSVP with time slots and party size tracking.

```json
{
  "id": "timeslot",
  "type": "select",
  "limit": 150,
  "range": [
    {
      "value": "5pm",
      "count": 1,
      "limit": 50
    },
    {
      "value": "6pm",
      "count": 2,
      "limit": 50
    }
  ]
},
{
  "limits": {
    "most_recent_only": true,
    "most_recent_key": "PlayerID"
  }
}
```

## Edge Cases

1. **Conditional arrays vs objects**: `conditional` can be either an object (single condition) or array (multiple AND conditions)

2. **Range formats**: `range` can be array of strings or array of objects (for capacity control)

3. **Capacity pre-processing**: Server pre-processes templates to populate `claimed` values before rendering

4. **Sticky field persistence**: Sticky fields persist at business level, available across all deals for that business

5. **Hidden fields**: Hidden fields are not displayed but their values are still submitted

6. **System fields**: Fields with `z_` prefix are typically system/user profile fields

7. **Character field navigation**: Character fields have back/forth navigation between inputs

8. **Image field**: Supports both camera capture and file upload

## Reference Template

See `REFERENCE-TEMPLATE.json` for a complete example with all patterns documented inline.

