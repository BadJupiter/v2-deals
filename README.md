# Deal Templates

This repo (root directlory here) contains all templates for Jupiter 2.0 deals, along with corresponding images.
This page serves as a basic overview of how deals templates are structured for consumption by the 
Jupiter mobile serverless HTML app at [https://badjupiter.cloud](https://badjupiter.cloud "Jupiter 2.0") 
to create and manage interactions with users.

---

## Deal Flows and Types

For our purposes every **Deal** follows the same simple flow: 

1. a QR scan a link kicks it off
2. (optionally) it collects some info with a form
3. if the user is not known, it authenticates him
4. it shows a main deal page, the deal is "grabbed"

Any complications around grabbing a deal: punch card handling, reward notifications via SMS, etc. are handled
by the server at grab time. 

There is a special kind of deal, a **check-in deal** which closes the loop for previously-grabbed deals 
that require in-person redemption. At grab time, a check-in deal will present the user with a list of deals
available for redemption in the form of buttons he can select to redeem. The flow for this continues from above:

5. the main deal page shows a button for each deal that can be redeemed
6. when a button is clicked, a modal confirmation "receipt" is shown and the corresponding deal is done

##  Deal Templates and Structure

Each deal template is a JSON text document with a name corresponding to a unique deal token. 
Optionally there may be a corresponding image file with the same token identifier.

	{
		"biz_id": "colusa",
		"check_in": true,
		"auth_required": true,
		"FORM": { 
     		},
    		"MAIN": { 
			"title": "Thanks for playing!",
   			"body_md": "See you next time..."
		}
	}

## EXAMPLE: Colusa Casino Player Feedback

Casino clientele can interact with a digital comment card by scanning a QR and providing some feedback for
casino staff. This is a check-in deal with an info form that has a couple required fields.

[colusa.json](https://badjupiter.github.io/v2-deals/colusa.json) (deal template)
[colusa.png](https://badjupiter.github.io/v2-deals/colusa.png) (header image)

## Markdown Syntax

[Markdown Guide](https://www.markdownguide.org/basic-syntax/ "Markdown Cheat Sheet")
