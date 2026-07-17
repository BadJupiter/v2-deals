# Venue-Sponsored Games - Code Reconciliation

## Requirements vs Current Implementation

### ✅ 1. Root URL → List of Participating Venues (as links)

**Requirement**: Root URL shows user a list of participating venues, as links to their pages

**Current Status**: ✅ **IMPLEMENTED**
- `v2-client/squares/script.js`: `showVenueSelection()` function (line 286)
- `v2-server/app/apiserver.py`: `/squares/venues` endpoint (line 826)
- `v2-server/app/services/venues.py`: `get_all_venues()` function (line 131)
- Client shows venue list when no venue token in URL (line 79-80 in script.js)

**Status**: Working as expected. No changes needed.

---

### ✅ 2. Venue Pages → Available Games + User's Active Games (as links)

**Requirement**: Venue pages list available games and also games currently being played by the user (if any) all as links

**Current Status**: ⚠️ **PARTIALLY IMPLEMENTED**

**What Works**:
- Venue landing page loads (`loadVenueLanding()` line 84)
- Available games list displays (`displayAvailableGames()` line 254)
- Active games section exists in HTML (line 72-77 in index.html)

**What's Missing**:
- `/squares/venuegames` returns empty `active_games: []` (line 786 in apiserver.py)
- TODO comment: "Get user's active games from database if usermobile provided" (line 761)
- Games use ESPN ID as temporary token instead of actual game tokens
- Games aren't actually created in database yet

**Needs**:
1. Query database for user's active venue games
2. Create actual game tokens when games are created
3. Return proper game state (SELLING, PLAYING, etc.)

---

### ❌ 3. Join Game Logic

**Requirement**: Users can join a game at a venue if:
- They're not already playing it
- The actual event hasn't started yet
- They get some pre-defined number of squares to pick

**Current Status**: ❌ **NOT IMPLEMENTED**

**What Exists**:
- `/squares/claimsquare` endpoint exists but returns `None` (line 814-824 in apiserver.py)
- `claimSquare()` function placeholder in client (line 347 in script.js)
- `loadGame()` function placeholder (line 341 in script.js)

**What's Missing**:
1. **Game Creation**: No function to create venue games in Neo4j
   - Need: `create_venue_game(venue_slug, espn_id, game_data)`
   - Should create `SqGame` node with:
     - `price=0` (free)
     - `venue_slug` property or relationship
     - ESPN feed info from bargames.json
     - State = "SELLING"
     - Empty 10x10 grid

2. **Join Game Endpoint**: Need `/squares/joingame` or enhance `/squares/venuegameinfo`
   - Check if user already playing
   - Check if game hasn't started (state != "PLAYING")
   - Create `PLAYING` relationship with initial square count
   - Return game info with user's square allocation

3. **Game Info Endpoint**: `/squares/venuegameinfo` returns `None`
   - Should look up or create game for venue+ESPN combo
   - Return game state, user's square count, remaining squares
   - Enforce `max_squares_per_player` from venue config

4. **Client Join Flow**: `loadGame()` needs implementation
   - Call `/squares/venuegameinfo` or join endpoint
   - If not joined, show "Join Game" button
   - If joined, show game board

---

### ❌ 4. Game "Full" Threshold → Auto-Allocate → New Game

**Requirement**: Games are "full" when down to some pre-defined number of empty squares. Those are randomly allocated to players and a new game is started.

**Current Status**: ❌ **NOT IMPLEMENTED**

**What Exists**:
- `__all_full()` function in `squares.py` (line 348) - checks if grid is completely full
- `ready_to_start()` function (line 342) - checks games ready to start
- `start_game()` function (line 262) - starts a game

**What's Missing**:
1. **Threshold Configuration**: Need to define "full" threshold
   - Could be venue-specific: `full_threshold` in venue config
   - Or game-specific: `full_threshold` in game data
   - Default: maybe 10-20 squares remaining?

2. **Auto-Allocation Logic**: When threshold reached:
   - Find all empty squares
   - Randomly assign to existing players (weighted by squares already claimed?)
   - Or assign evenly?
   - Update game state

3. **New Game Creation**: After auto-allocation:
   - Create new `SqGame` node for same venue+ESPN combo
   - Link as "next game" or version number?
   - Notify players?

4. **Trigger Mechanism**: When to check?
   - On each square claim?
   - Periodic background job?
   - Both?

**Suggested Approach**:
- Add `full_threshold` to venue config (default: 10)
- Check threshold in `claim_venue_square()` after each claim
- If threshold reached, call `auto_allocate_remaining_squares()`
- Then call `start_game()` to transition to PLAYING
- Create new game instance for same venue+ESPN combo

---

### ❌ 5. Play Like Original: Flashing Squares, Quarter Winners

**Requirement**: Play works like the original version: players watch flashing squares during the game, winners at each quarter, etc.

**Current Status**: ❌ **NOT IMPLEMENTED**

**What Exists in Original** (`v2-client/s1/`):
- Game board HTML structure (10x10 grid with row/col headers)
- `updateGrid()` function (line 1034) - renders grid state
- `updateGridWithWinners()` function (line 1166) - highlights winners
- `refreshGame()` function (line 1088) - polls for updates
- Polling mechanism (line 1110)
- Score display and winner announcements

**What's Missing in Venue Version** (`v2-client/squares/`):
1. **Game Board HTML**: `index.html` has placeholder (line 97)
   - Need full 10x10 grid structure like `s1/index.html` (lines 120-267)
   - Need row/column headers
   - Need winner display table

2. **Game Board Rendering**: `loadGame()` is placeholder (line 341)
   - Need to render grid from game data
   - Need to handle SELLING vs PLAYING states
   - Need to show row/col assignments when PLAYING

3. **Square Claiming UI**: `claimSquare()` is placeholder (line 347)
   - Need click handlers for empty squares
   - Need to update UI optimistically
   - Need to handle errors

4. **Live Updates**: `refreshGame()` is placeholder (line 352)
   - Need to poll `/squares/venuegameinfo`
   - Need to update grid with current scores
   - Need to highlight flashing squares
   - Need to show quarter winners

5. **Score Display**: Missing
   - Need to show current score
   - Need to show quarter scores
   - Need winner announcements

**Needs**:
- Copy/adapt game board HTML from `s1/index.html`
- Implement `loadGame()` to render board
- Implement `claimSquare()` with API call
- Implement `refreshGame()` with polling
- Add score display and winner logic

---

## Database Schema Considerations

### Current Schema (Original Games)
- `SqGame` node with properties: `token`, `name`, `state`, `price`, `rc`, `eventinfo`, etc.
- `User` -[:OWNS]-> `SqGame` (game creator)
- `User` -[:PLAYING]-> `SqGame` (participants, with `credits` and `usertag`)

### Needed for Venue Games
1. **Venue Linkage**: How to link games to venues?
   - Option A: Add `venue_slug` property to `SqGame` node
   - Option B: Create `Venue` node and `SqGame` -[:SPONSORED_BY]-> `Venue`
   - **Recommendation**: Option A (simpler, venue_slug property)

2. **Game Identification**: How to identify venue games?
   - Option A: Composite key: `venue_slug` + `espn_id` → unique game
   - Option B: Generate unique token, store `venue_slug` and `espn_id` as properties
   - **Recommendation**: Option B (consistent with original, easier queries)

3. **Multiple Game Instances**: When game fills and new one starts:
   - Option A: Create new `SqGame` node with version number
   - Option B: Reuse same game, reset state
   - **Recommendation**: Option A (preserves history, allows multiple concurrent games)

4. **User Participation**: Track user's squares
   - Use existing `PLAYING` relationship
   - Use `credits` field as "squares remaining" (or add `squares_remaining` property)
   - **Recommendation**: Use `credits` as squares remaining (consistent with original)

---

## Recommended Implementation Plan

### Phase 1: Game Creation & Joining
1. Create `create_venue_game()` function in `squares.py`
2. Implement `/squares/venuegameinfo` to look up/create games
3. Add "Join Game" flow in client
4. Implement `/squares/claimsquare` for claiming squares

### Phase 2: Game Board & Play
5. Add game board HTML structure to `squares/index.html`
6. Implement `loadGame()` to render board
7. Implement `claimSquare()` with API integration
8. Implement `refreshGame()` with polling

### Phase 3: Full Threshold & Auto-Allocation
9. Add `full_threshold` to venue config
10. Implement threshold check in claim logic
11. Implement auto-allocation of remaining squares
12. Implement new game creation when threshold reached

### Phase 4: Polish & Testing
13. Add score display and winner announcements
14. Handle edge cases (game already started, user already joined, etc.)
15. Testing with multiple users and venues

---

## Key Code Locations

### Server-Side
- `v2-server/app/apiserver.py`: API endpoints (lines 728-836)
- `v2-server/app/services/graph/squares.py`: Game logic (needs new functions)
- `v2-server/app/services/venues.py`: Venue data (complete)

### Client-Side
- `v2-client/squares/index.html`: HTML structure (needs game board)
- `v2-client/squares/script.js`: Client logic (needs game functions)
- `v2-client/squares/style.css`: Styling (may need updates)

### Reference Implementation
- `v2-client/s1/`: Original game implementation (use as reference)

---

## Questions to Resolve

1. **Game Token Strategy**: Use ESPN ID temporarily or create real tokens immediately?
   - **Recommendation**: Create real tokens when game is first accessed

2. **Join Flow**: Separate "join" endpoint or auto-join on first square claim?
   - **Recommendation**: Auto-join on first square claim (simpler UX)

3. **Full Threshold**: Venue-specific or game-specific?
   - **Recommendation**: Venue-specific with default (e.g., 10 squares)

4. **Auto-Allocation**: How to distribute remaining squares?
   - **Recommendation**: Evenly among all players who have claimed squares

5. **Multiple Games**: Can same venue+ESPN have multiple concurrent games?
   - **Recommendation**: Yes, when one fills, create new one

6. **Game State Flow**: Same as original (SELLING → PLAYING → OVER)?
   - **Recommendation**: Yes, but auto-transition when threshold reached

