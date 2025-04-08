# Deal Templates (and others)

This repo (root directlory here) might be a little mis-named. 
It contains all templates for Jupiter 2.0 **deals**, **rewards**, **punchcards**, and **reports** along with corresponding images and styling.
This document provides a basic overview of how all these templates are structured for consumption by the 
Jupiter mobile serverless HTML app at [https://badjupiter.cloud](https://badjupiter.cloud "Jupiter 2.0") 
to create and manage interactions with users.

---

## Deals

A **deal** is an end-to-end interaction with a *user*. Each **deal** is identified by a unique token and is defined by up to 4 files, below.
A **deal** is access by a URL structured like **badjupiter.cloud?*dealtoken*** (possibly followed by optional params).

|File                  |Description                                 |
|----------------------|--------------------------------------------|
|*dealtoken*.json      |template for the deal (required)            |
|*dealtoken*.png       |hero image (other formats are supported)    |
|*dealtoken*.css       |deal-specific styling                       |
|*dealtoken*-temp.json |placeholder page (overrides deal)           |

### Flow(s)

For our purposes every **deal** follows the same simple flow: 

1. A QR scan (ot other link) kicks it off;
2. (optionally) it collects some info with a form;
3. if the user is not known and auth is required, it authenticates him;
4. it shows a main "confirm" page and the "grab" is complete.

By default, a **deal** presents the *user* with either an info page or a form; the *user* may opt to "grab" the deal if he's interested.

### Check-In

A *check-in* is a special kind of **deal** automatically grabs without any user confirmation. Typical use-case is an  
in-person QR scan at a business where a followup confirm would be an unnecessary step. 

###  Deal Template Structure

Each **deal** template is a JSON text document with a name corresponding to a unique **deal** *token*. 

```json
{
	"biz_id": "colusa",
	"check_in": true,
	"auth_required": true,
	"error_auth": {
		"title": "Woops!",
		"content": "Can't play if you ain't authenticated!"
	},
	"FORM": {
		"title": "Player Feedback",
		"fields": [ ... ],	
		"limits": { ... },	# OPTIONAL limits criteria
		"submit": { 		# OPTIONAL submit button
			"label": "Submit Feedback",
			"color": "#20363d"
		}
	},
	"MAIN": {
		"title": "Thanks for playing!",
		"body_md": "See you next time..."
	}
}
```

|Attribute     |Description                                                         |
|--------------|--------------------------------------------------------------------|
|biz_id        |Business - must exist in graph                                      |
|check_in      |if present and *true* grab flow kicks off immediately               |
|auth_required |if present and *true* user will be authenticated prior to grab      |
|error_auth    |if present and *auth_required*, overrides defaults for error dialog |
|FORM          |if present defines user interactions prior to grab                  |
|MAIN          |defined the main confirmation page                                  |

### FORM Fields

The following types of fields are supported in **deal** templates:

|Field Type        |Description                                                           |
|------------------|----------------------------------------------------------------------|
|*info*            |special non-input "field" for descriptive text - can contain markdown |
|*email*           |text field accepting only valid-formatted email                       |
|*text*            |simple text field                                                     |
|*textarea*        |bigger text field, can specify number of lines                        |
|*checkbox*        |check it or don't                                                     |
|*select*          |pick one from several options                                         |
|*multi-select*    |pick one or more from several options                                 |
|*characters*      |individual character inputs with back-forth nav                       |
|*image*           |take a photo or upload an image                                       |

The following attributes are supported, and some are required, based on field type:

|Attribute  |Required |Field                                             |Description         |
|-----------|---------|--------------------------------------------------|--------------------|
|type       |YES      |ALL                                               |                    |
|id         |YES      |*email*, *text*, *textarea*, *select*, *checkbox* |unique identifier   |
|label      |NO       |*email*, *text*, *textarea*, *select*, *checkbox* |displayed           |
|disabled   |NO       |*email*, *text*, *textarea*, *select*, *checkbox* |view-only           |
|sticky     |NO       |*email*, *text*, *textarea*, *select*, *checkbox* |persists / defaults |

**NOTE:** Sticky fields attach to a Business-level user context and as a result are available across **deals**
for a Business. So if one **deal* asks for *email* and makes it sticky, all other **deals** from that Business
with sticky *email* fields will pick up (and possibly modify) the value.

```json
{
	"id": "PlayerID",
	"label": "Rewards #:",
	"type": "text",
	"sticky": true,		# (otherwise just omit)
	"disabled": true
}
```

## Context Data
## Conditional Fields
## Capacity Limits

Optionally, fields which ask for a quantity (e.g. RSVP with or without a guest) can specify a limit.
This is done inline when the field is declared, like below. If a selected option counts for more than one,
then a count can be specified also.

```json
{
	"id": "gift",
	"label": "Which gift would you prefer?",
	"type": "select",
	"range": [
		{
			"value": "Daybook",
			"limit": 100
		},
		{
			"value": "Padfolio (set of 2)",
			"count": 2,
			"limit": 100
		}
	],
	"required": true,
}
```

If a FORM contains any field with limits specified, the form is pre-processed and updated with current counts for those fields
so that the rendering engine can determine which options might still be available. (The template file itself is not modified; 
this is an internal processing step.) By default, counts are based on ALL grabs of the deal, even if multiple grabs for a single
user-mobile. In some cases, like RSVPs, that needs to be overridden in an optional limits section following fields:

```json
"limits": {
	"most_recent_only": true,
	"most_recent_key": "PlayerID"
}
```

## Supported FORM field types

### info

This is an information-only field that can contain markdown for the purposes of rendering headers and formatting text.
***info*** fields do not require an *id* parameter.

```json
{
	"type": "info",
	"justify": "center",	# OPTIONAL
	"markdown": "\n\nAs a valued customer, we are *thrilled* to offer you this deal."
}
```


### Rewards

At grab time, a **deal** confirm will present the user with a list of any **rewards**
available for redemption in the form of buttons he can click to redeem. The flow for this continues from the
flow outlined above:

5. The "confirm" page shows a button for each **reward** that can be redeemed;
6. when a button is clicked, a modal confirmation "receipt" is shown and the corresponding **reward** is done.





## Punch Cards
## Reports







## EXAMPLE: Colusa Casino Player Feedback

Casino clientele can interact with a digital comment card by scanning a QR and providing some feedback for
casino staff. This is a check-in deal with an info form that has a couple required fields.

[colusa.json](https://badjupiter.github.io/v2-deals/colusa.json) (deal template)
[colusa.png](https://badjupiter.github.io/v2-deals/colusa.png) (header image)

## Markdown Syntax

[Markdown Guide](https://www.markdownguide.org/basic-syntax/ "Markdown Cheat Sheet")
