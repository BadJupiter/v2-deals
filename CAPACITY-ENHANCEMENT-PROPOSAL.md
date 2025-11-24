# Capacity Enhancement Proposal: Dynamic Count References

## Problem

Currently, capacity `count` values are static in templates. There's no way to make the count dynamic based on another field's value (e.g., "guest" field determining if count is 1 or 2).

## Proposed Solution

Add support for dynamic count references that allow a field to reference another field's value to determine its capacity count.

### Option 1: Field-level `count_ref` attribute

Add a `count_ref` attribute to select fields that references another field to determine the count:

```json
{
  "id": "day1_time",
  "type": "select",
  "label": "Pick a time slot for Day 1:",
  "count_ref": {
    "field": "guest",
    "mapping": {
      "Yes": 2,
      "No": 1
    }
  },
  "range": [
    {
      "value": "10:00 AM",
      "limit": 50
    }
  ]
}
```

**Implementation:**
- Client-side: When rendering options, check `count_ref.field` value and use `count_ref.mapping[value]` as the count
- Server-side: When calculating capacity, look up the referenced field value from form data and use the mapping

### Option 2: Option-level `count_ref` attribute

Allow each option to reference a field:

```json
{
  "id": "day1_time",
  "type": "select",
  "range": [
    {
      "value": "10:00 AM",
      "limit": 50,
      "count_ref": {
        "field": "guest",
        "mapping": {
          "Yes": 2,
          "No": 1
        }
      }
    }
  ]
}
```

### Option 3: Global field reference (User's suggestion)

Mark a field as `global: true` and allow other fields to reference it:

```json
{
  "id": "guest",
  "type": "select",
  "range": ["Yes", "No"],
  "global": true,
  "capacity_map": {
    "Yes": 2,
    "No": 1
  }
}
```

Then reference it in time slot fields:

```json
{
  "id": "day1_time",
  "type": "select",
  "count_from": "guest",
  "range": [
    {
      "value": "10:00 AM",
      "limit": 50
    }
  ]
}
```

## Recommended Approach

**Option 3 (Global field reference)** is cleanest because:
1. The mapping is defined once on the source field
2. Multiple fields can reference the same global field
3. Clear separation of concerns (source field defines the mapping, consuming fields reference it)

## Implementation Details

### Client-side (`formElements.js`)

When rendering select options with capacity limits:
1. Check if field has `count_from` attribute
2. If yes, find the referenced field by ID
3. Get its current value
4. Look up the count in the referenced field's `capacity_map`
5. Use that count instead of static `count` when checking capacity

```javascript
// In formElements.js, when processing select options:
let count = optionItem.count || 1;

if (field.count_from) {
  const refField = fieldElements[field.count_from];
  if (refField && refField.value) {
    const refFieldDef = findFieldDefinition(field.count_from);
    if (refFieldDef?.capacity_map) {
      count = refFieldDef.capacity_map[refField.value] || 1;
    }
  }
}

// Then use this dynamic count for capacity check
if (typeof limit === 'number') {
  if ((claimed + count) > limit) {
    option.disabled = true;
  }
}
```

### Server-side (`counts.py`)

When calculating capacity from submitted form data:
1. Check if field has `count_from` attribute
2. If yes, look up the referenced field's value in the submitted form data
3. Find the referenced field definition and get its `capacity_map`
4. Use the mapped count value

```python
# In counts.py, when processing a selected option:
count = item.get("count", 1)

# Check if this field references another field for count
if "count_from" in field:
    ref_field_id = field["count_from"]
    ref_field_def = find_field(config, ref_field_id)
    if ref_field_def and "capacity_map" in ref_field_def:
        ref_value = row.get(ref_field_id)  # Get value from submitted form
        if ref_value in ref_field_def["capacity_map"]:
            count = ref_field_def["capacity_map"][ref_value]

# Use this count for capacity calculation
item["claimed"] = item.get("claimed", 0) + count
```

## Backward Compatibility

This enhancement is fully backward compatible:
- Existing templates without `count_from` continue to work as before
- Static `count` values still work
- Only new templates using `count_from` get the dynamic behavior

## Example Template

```json
{
  "id": "guest",
  "label": "Are you bringing a guest?",
  "type": "select",
  "range": ["Yes", "No"],
  "global": true,
  "capacity_map": {
    "Yes": 2,
    "No": 1
  }
},
{
  "id": "day1_time",
  "label": "Pick a time slot for Day 1:",
  "type": "select",
  "count_from": "guest",
  "range": [
    {
      "value": "10:00 AM",
      "limit": 50
    },
    {
      "value": "12:00 PM",
      "limit": 50
    }
  ],
  "conditional": {
    "field": "coming",
    "value": "Yes"
  }
}
```

