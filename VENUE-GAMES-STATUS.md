# Venue-Sponsored Squares Games - Implementation Status

## Overview
You're building a second version of the squares game where venues sponsor games and customers can join to play. This differs from the original version where end users create their own games and share links.

## What's Been Implemented ✅

### 1. Venue Infrastructure (`v2-server/app/services/venues.py`)
- ✅ `load_bargames()` - Loads venue and game data from `v2-squares/bargames.json`
- ✅ `get_venue_info()` - Returns venue branding, payouts, and customization
- ✅ `get_games_for_venue()` - Lists games available at a venue
- ✅ `get_all_venues()` - Returns list of all venues for selection screen
- ✅ `get_venue_payouts()` - Returns payout structure for a venue

### 2. API Endpoints (`v2-server/app/apiserver.py`)
- ✅ `/squares/venueinfo` - Returns venue branding and info (fully implemented)
- ✅ `/squares/venuegames` - Lists available games for a venue (partially implemented)
- ✅ `/squares/venues` - Lists all venues (fully implemented)
- ⚠️ `/squares/venuegameinfo` - **TODO: Returns None** - Needs implementation
- ⚠️ `/squares/claimsquare` - **TODO: Returns None** - Needs implementation

### 3. Client-Side UI (`v2-client/squares/`)
- ✅ Venue selection screen when no venue specified
- ✅ Venue landing page with branding (logo, colors, welcome message)
- ✅ Active games list (empty - needs game data)
- ✅ Available games list (shows games from bargames.json)
- ⚠️ `loadGame()` function - **TODO: Just a placeholder**
- ⚠️ `claimSquare()` function - **TODO: Just a placeholder**
- ⚠️ Game board rendering - **TODO: Not implemented**

### 4. Data Structure (`v2-squares/bargames.json`)
- ✅ Venue definitions with meta info and payouts
- ✅ Game definitions with ESPN IDs, teams, dates
- ✅ Games linked to venues via `venues` array

## What's Missing / Incomplete ❌

### 1. **Game Creation in Database**
**Problem**: Games from `bargames.json` are listed but never created as `SqGame` nodes in Neo4j.

**What's needed**:
- Function to create a venue-sponsored game in Neo4j
- Should link game to venue (new relationship type?)
- Should set `price=0` (free squares)
- Should include ESPN feed info from bargames.json
- Should initialize with empty 10x10 grid
- Should set state to "SELLING" initially

**Location**: `v2-server/app/services/graph/squares.py` - needs new function like `create_venue_game()`

### 2. **Game Info Endpoint** (`/squares/venuegameinfo`)
**Current state**: Returns `None` (line 804 in `apiserver.py`)

**What's needed**:
- Look up or create game for venue + ESPN ID combination
- Return game state (similar to `game_info()` but for venue games)
- Include user's square count and remaining squares they can claim
- Enforce `max_squares_per_player` limit from venue config
- Return game board state, scores, etc.

**Key differences from original**:
- No price/fee (free squares)
- Per-player limit instead of credits
- Venue context required

### 3. **Claim Square Endpoint** (`/squares/claimsquare`)
**Current state**: Returns `None` (line 824 in `apiserver.py`)

**What's needed**:
- Check if user has remaining squares (max_squares_per_player limit)
- Verify square is available
- Claim square (free, no payment)
- Update game state in Neo4j
- Return updated game info

**Key differences from original**:
- No credits/payment - just count squares claimed
- Enforce per-player limit
- Free squares

### 4. **Client-Side Game Loading** (`loadGame()` in `script.js`)
**Current state**: Just logs and has TODO comment (line 341-344)

**What's needed**:
- Call `/squares/venuegameinfo` to get game data
- Render game board (10x10 grid)
- Show user's remaining squares
- Handle square clicking/claiming
- Poll for game updates (scores, state changes)
- Display scores and game status

### 5. **Database Schema Considerations**
**Questions to resolve**:
- How to link games to venues? New relationship type `VENUE_SPONSORS`?
- How to track user's square count? Use existing `PLAYING` relationship with `credits` field?
- Should venue games have a different state flow? (SELLING → PLAYING → OVER)

### 6. **Game Token Strategy**
**Current issue**: `/squares/venuegames` uses ESPN ID as temporary token (line 771)

**What's needed**:
- Create actual game tokens when games are created
- Map ESPN ID + venue to game token
- Or use composite key (venue_slug + espn_id)

## Key Differences: Original vs Venue Games

| Feature | Original Games | Venue Games |
|---------|---------------|-------------|
| **Creation** | User creates via `/squares/newgame` | Venue sponsors (auto-created?) |
| **Price** | User sets price | Free (price=0) |
| **Limits** | Credits purchased | Max squares per player |
| **Payment** | PayPal integration | None (free) |
| **Link** | Share game token | Venue-specific URL |
| **State** | SELLING → PLAYING → OVER | Same? |

## Recommended Next Steps

1. **Create venue game creation function**
   - `create_venue_game(venue_slug, espn_id, game_data)` in `squares.py`
   - Creates SqGame node with venue relationship
   - Sets price=0, state=SELLING
   - Includes ESPN feed info

2. **Implement `/squares/venuegameinfo`**
   - Look up or create game for venue+ESPN combo
   - Return game state with user's square count
   - Enforce max_squares_per_player limit

3. **Implement `/squares/claimsquare`**
   - Check user's square count vs limit
   - Claim square (free)
   - Update game state
   - Return updated info

4. **Complete client-side `loadGame()`**
   - Fetch game info
   - Render 10x10 grid
   - Handle square claiming
   - Poll for updates

5. **Update `/squares/venuegames`**
   - Return actual game tokens (not ESPN IDs)
   - Include game state (SELLING, PLAYING, etc.)
   - Show available squares count

## Files to Modify

1. `v2-server/app/services/graph/squares.py` - Add venue game functions
2. `v2-server/app/apiserver.py` - Complete TODO endpoints
3. `v2-client/squares/script.js` - Implement game loading and claiming
4. `v2-client/squares/index.html` - May need game board HTML structure

## Notes

- The original `grab_game_square()` function uses credits system - venue games need different logic
- Consider creating `claim_venue_square()` function similar to `grab_game_square()` but without payment
- Venue games might need auto-creation when first accessed, or manual creation via admin script
- Need to decide: one game per venue+ESPN combo, or multiple games per venue?
- The `register_credits()` function shows how `PLAYING` relationship is created - venue games can use similar pattern but track square count instead of credits
- Original games use `OWNS` relationship for creator, `PLAYING` for participants - venue games might only need `PLAYING`

## Code Patterns to Follow

### Original Game Creation Pattern (`create_game()`)
- Creates `SqGame` node with random 6-char token
- Creates `OWNS` relationship from user to game
- Sets initial state to "SELLING"
- Initializes 10x10 grid (rc) as JSON array
- Stores event info in `eventinfo` property

### Original Square Claiming Pattern (`grab_game_square()`)
- Requires `PLAYING` relationship with credits > 0
- Updates `rc` array in game node
- Decrements credits in `PLAYING` relationship
- Returns updated game info

### Venue Game Adaptation Needed
- Create game with venue context (maybe `venue_slug` property on game node?)
- No `OWNS` relationship (venue-sponsored, not user-owned)
- Track squares claimed per user (could use `PLAYING.credits` as square count, or new field)
- Enforce `max_squares_per_player` from venue config
- Auto-create game on first access, or create via script before game day

