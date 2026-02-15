"""Direct BoardGameGeek XML API client without external dependencies."""

import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from loguru import logger


class BGGApiError(Exception):
    """Exception raised for BGG API errors."""

    pass


class BGGItemNotFoundError(Exception):
    """Exception raised when a BGG item is not found."""

    pass


@dataclass
class GameExpansion:
    """Represents a game expansion."""

    id: int
    name: str

    def data(self):
        """Return expansion data as dict."""
        return {"id": self.id, "name": self.name}


@dataclass
class GameData:
    """Represents game data from BGG."""

    id: int
    name: str
    thumbnail: Optional[str]
    min_players: int
    max_players: int
    rating_average: float
    expansions: List[GameExpansion]
    data_dict: dict  # Store the full data dictionary

    def data(self):
        """Return the full data dictionary."""
        return self.data_dict


@dataclass
class CollectionItem:
    """Represents an item in a user's collection."""

    id: int
    _data: dict


class BGGClient:
    """Client for BoardGameGeek XML API v2."""

    BASE_URL = "https://boardgamegeek.com/xmlapi2"

    def __init__(self, timeout=15, retries=3, retry_delay=5):
        """Initialize the BGG client.

        Args:
            timeout: Request timeout in seconds
            retries: Number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.session = requests.Session()

        # Load environment variables from .env file
        load_dotenv()

        # Set up authentication if BGG_API_KEY is available (for rate limiting identification)
        bgg_api_key = os.environ.get("BGG_API_KEY")
        if bgg_api_key:
            self.session.headers.update({"Authorization": f"Bearer {bgg_api_key}"})
        else:
            logger.warning(
                "No BGG_API_KEY found in environment; proceeding without authentication."
            )

        # Try to login with username/password to get session cookies for private info access
        self._login_for_private_info()

    def _login_for_private_info(self):
        """Login to BGG to get session cookies for accessing private info."""
        username = os.environ.get("BGG_USERNAME")
        password = os.environ.get("BGG_PASSWORD")

        if not username or not password:
            logger.info(
                "BGG_USERNAME or BGG_PASSWORD not set. "
                "Private info (inventory location) will not be available."
            )
            return False

        try:
            # Use the login API endpoint
            login_url = "https://boardgamegeek.com/login/api/v1"
            # Credentials must be wrapped in a "credentials" object
            payload = {"credentials": {"username": username, "password": password}}

            response = self.session.post(
                login_url, json=payload, timeout=self.timeout
            )

            # Status 200 or 204 indicates successful login
            if response.status_code in (200, 204):
                # Check if we got session cookies
                cookie_names = list(self.session.cookies.keys())
                if "bggusername" in self.session.cookies or "SessionID" in self.session.cookies:
                    logger.info(
                        f"Successfully logged in as {username} - "
                        f"cookies: {cookie_names} - private info access enabled"
                    )
                    return True
                else:
                    logger.warning(
                        f"Login succeeded (status {response.status_code}) "
                        f"but no session cookies received. Cookies: {cookie_names}"
                    )
                    return False
            else:
                logger.warning(
                    f"BGG login failed with status {response.status_code}. "
                    "Private info will not be available."
                )
                return False

        except Exception as e:
            logger.warning(f"Failed to login to BGG: {e}. Private info will not be available.")
            return False

    def _make_request(self, endpoint, params=None):
        """Make a request to the BGG API with retries.

        Args:
            endpoint: API endpoint (e.g., 'thing', 'search')
            params: Query parameters

        Returns:
            XML ElementTree root

        Raises:
            BGGApiError: If the request fails after all retries
        """
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(self.retries):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                # Parse XML
                root = ET.fromstring(response.content)

                # Check for BGG API errors (202 status means data is being generated)
                if response.status_code == 202:
                    logger.warning("BGG API returned 202, retrying...")
                    time.sleep(self.retry_delay)
                    continue

                # Check for error in XML
                if root.tag == "error":
                    error_msg = root.find("message")
                    if error_msg is not None:
                        raise BGGItemNotFoundError(error_msg.text)
                    raise BGGItemNotFoundError("Item not found")

                return root

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"BGG API request failed (attempt {attempt + 1}/{self.retries}): {e}"
                )
                if attempt < self.retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise BGGApiError(
                        f"Failed to connect to BGG API after {self.retries} attempts"
                    ) from e

        raise BGGApiError("Failed to get valid response from BGG API")

    def game(self, game_id=None, name=None, versions=False):
        """Get game information by ID or name.

        Args:
            game_id: BGG game ID
            name: Game name (used if game_id is not provided)
            versions: Whether to include version information

        Returns:
            GameData object

        Raises:
            BGGItemNotFoundError: If game is not found
            BGGApiError: If API request fails
        """
        if game_id is None and name is None:
            raise ValueError("Either game_id or name must be provided")

        # If name is provided, search for the game first
        if game_id is None:
            game_id = self._search_game_by_name(name)

        # Get game details
        params = {"id": game_id, "stats": 1, "type": "boardgame"}

        if versions:
            params["versions"] = 1

        root = self._make_request("thing", params)

        # Parse game data
        item = root.find("item")
        if item is None:
            raise BGGItemNotFoundError(f"Game with ID {game_id} not found")

        return self._parse_game_data(item, include_versions=versions)

    def _search_game_by_name(self, name):
        """Search for a game by name and return the best match ID.

        Args:
            name: Game name to search for

        Returns:
            Game ID of the best match

        Raises:
            BGGItemNotFoundError: If no games are found
        """
        params = {
            "query": name,
            "type": "boardgame",
            "exact": 1,  # Try exact match first
        }

        root = self._make_request("search", params)
        items = root.findall("item")

        if not items:
            # Try non-exact match
            params["exact"] = 0
            root = self._make_request("search", params)
            items = root.findall("item")

        if not items:
            raise BGGItemNotFoundError(f"No games found matching '{name}'")

        # Return the first result (best match)
        return int(items[0].get("id"))

    def _parse_game_data(self, item, include_versions=False):
        """Parse game data from XML item element.

        Args:
            item: XML element for the game
            include_versions: Whether version info was requested

        Returns:
            GameData object
        """
        game_id = int(item.get("id"))

        # Get primary name
        primary_name = item.find("name[@type='primary']")
        if primary_name is None:
            primary_name = item.find("name")
        name = primary_name.get("value") if primary_name is not None else "Unknown"

        # Get thumbnail
        thumbnail_elem = item.find("thumbnail")
        thumbnail = thumbnail_elem.text if thumbnail_elem is not None else None

        # Get player count
        min_players_elem = item.find("minplayers")
        max_players_elem = item.find("maxplayers")
        min_players = (
            int(min_players_elem.get("value", 1)) if min_players_elem is not None else 1
        )
        max_players = (
            int(max_players_elem.get("value", 1)) if max_players_elem is not None else 1
        )

        # Suggested players
        suggested_players_elem = item.find(".//poll[@name='suggested_numplayers']")
        suggested_players = {"results": {}, "totalvotes": 0}
        if suggested_players_elem is not None:
            total_votes = suggested_players_elem.get("totalvotes", "0")
            try:
                suggested_players["totalvotes"] = int(total_votes)
            except (ValueError, TypeError):
                suggested_players["totalvotes"] = 0

            for numplayers in suggested_players_elem.findall("results"):
                player_count = numplayers.get("numplayers")
                if player_count:
                    ratings = {
                        "best_rating": 0,
                        "recommended_rating": 0,
                        "not_recommended_rating": 0,
                    }
                    for result in numplayers.findall("result"):
                        rating_type = result.get("value")
                        votes = result.get("numvotes", "0")
                        try:
                            votes_int = int(votes)
                        except (ValueError, TypeError):
                            votes_int = 0
                        if rating_type == "Best":
                            ratings["best_rating"] = votes_int
                        elif rating_type == "Recommended":
                            ratings["recommended_rating"] = votes_int
                        elif rating_type == "Not Recommended":
                            ratings["not_recommended_rating"] = votes_int
                    suggested_players["results"][player_count] = ratings

        # Get rating
        rating_elem = item.find(".//average")
        rating_average = (
            float(rating_elem.get("value", 0)) if rating_elem is not None else 0.0
        )

        # Playingtime
        playingtime_elem = item.find("playingtime")
        playingtime = (
            int(playingtime_elem.get("value", 0)) if playingtime_elem is not None else 0
        )

        # Get expansions
        expansions = []
        for link in item.findall("link[@type='boardgameexpansion']"):
            if (
                link.get("inbound") != "true"
            ):  # Only outbound links (this game's expansions)
                expansion = GameExpansion(
                    id=int(link.get("id")), name=link.get("value")
                )
                expansions.append(expansion)

        # Build full data dictionary
        data_dict = {
            "id": game_id,
            "name": name,
            "thumbnail": thumbnail,
            "minplayers": min_players,
            "maxplayers": max_players,
            "stats": self._parse_stats(item),
            "expansions": [exp.data() for exp in expansions],
            "suggested_players": suggested_players,
            "playingtime": playingtime,
        }

        # Add versions if requested
        if include_versions:
            data_dict["versions"] = self._parse_versions(item)

        return GameData(
            id=game_id,
            name=name,
            thumbnail=thumbnail,
            min_players=min_players,
            max_players=max_players,
            rating_average=rating_average,
            expansions=expansions,
            data_dict=data_dict,
        )

    def _parse_stats(self, item):
        """Parse statistics from game item."""
        stats_elem = item.find(".//statistics/ratings")
        if stats_elem is None:
            return {}

        def get_value(elem, tag, default=0):
            el = elem.find(tag)
            if el is not None:
                val = el.get("value")
                if val and val != "Not Ranked":
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        pass
            return default

        stats = {
            "usersrated": int(get_value(stats_elem, "usersrated")),
            "average": get_value(stats_elem, "average"),
            "bayesaverage": get_value(stats_elem, "bayesaverage"),
            "stddev": get_value(stats_elem, "stddev"),
            "median": get_value(stats_elem, "median"),
            "averageweight": get_value(stats_elem, "averageweight"),
            "ranks": [],
        }

        # Parse ranks
        ranks_elem = stats_elem.find("ranks")
        if ranks_elem is not None:
            for rank in ranks_elem.findall("rank"):
                rank_data = {
                    "id": rank.get("id"),
                    "name": rank.get("name"),
                    "friendlyname": rank.get("friendlyname"),
                    "value": None,
                }
                rank_value = rank.get("value")
                if rank_value and rank_value != "Not Ranked":
                    try:
                        rank_data["value"] = int(rank_value)
                    except (ValueError, TypeError):
                        pass
                stats["ranks"].append(rank_data)

        return stats

    def _parse_versions(self, item):
        """Parse version information from game item."""
        versions = []
        for version in item.findall(".//version"):
            version_data = {
                "item_id": version.get("id"),
                "language": (
                    version.find("link[@type='language']").get("value")
                    if version.find("link[@type='language']") is not None
                    else "Unknown"
                ),
                "width": 0,
                "length": 0,
                "depth": 0,
            }

            # Parse dimensions
            width_elem = version.find(".//width")
            length_elem = version.find(".//length")
            depth_elem = version.find(".//depth")

            if width_elem is not None:
                try:
                    version_data["width"] = float(width_elem.get("value", 0))
                except (ValueError, TypeError):
                    pass

            if length_elem is not None:
                try:
                    version_data["length"] = float(length_elem.get("value", 0))
                except (ValueError, TypeError):
                    pass

            if depth_elem is not None:
                try:
                    version_data["depth"] = float(depth_elem.get("value", 0))
                except (ValueError, TypeError):
                    pass

            versions.append(version_data)

        return versions

    def collection(self, user_name, **kwargs):
        """Get a user's collection.

        Args:
            user_name: BGG username
            **kwargs: Collection filters (own, wishlist, exclude_subtype, etc.)

        Returns:
            List of CollectionItem objects

        Raises:
            BGGApiError: If API request fails
        """
        params = {"username": user_name}

        # Map common parameters
        if kwargs.get("own"):
            params["own"] = 1
        if kwargs.get("wishlist"):
            params["wishlist"] = 1
        if kwargs.get("preordered"):
            params["preordered"] = 1
        if kwargs.get("exclude_subtype"):
            params["excludesubtype"] = kwargs["exclude_subtype"]

        # Add stats to get more information
        params["stats"] = 1

        # Add showprivate=1 to retrieve private info (inventory location, etc.)
        params["showprivate"] = 1

        root = self._make_request("collection", params)

        # Parse collection items
        items = []
        for item_elem in root.findall("item"):
            item_id = int(item_elem.get("objectid"))

            # Parse item data
            name_elem = item_elem.find("name")
            name = name_elem.text if name_elem is not None else "Unknown"

            thumbnail_elem = item_elem.find("thumbnail")
            thumbnail = thumbnail_elem.text if thumbnail_elem is not None else None

            # Parse stats if available
            stats_elem = item_elem.find(".//stats")
            min_players = 1
            max_players = 1
            rating = None

            if stats_elem is not None:
                minplayers_elem = stats_elem.get("minplayers")
                maxplayers_elem = stats_elem.get("maxplayers")
                rating_elem = stats_elem.find(".//average")

                if minplayers_elem is not None:
                    try:
                        min_players = int(minplayers_elem)
                    except (ValueError, TypeError):
                        pass

                if maxplayers_elem is not None:
                    try:
                        max_players = int(maxplayers_elem)
                    except (ValueError, TypeError):
                        pass

                if rating_elem is not None:
                    try:
                        rating = float(rating_elem.get("value", 0))
                    except (ValueError, TypeError):
                        pass

            # Parse wishlist priority
            status = item_elem.find("status")
            wishlist_priority = None
            if status is not None and kwargs.get("wishlist"):
                priority = status.get("wishlistpriority")
                if priority:
                    try:
                        wishlist_priority = int(priority)
                    except (ValueError, TypeError):
                        pass
            numplays_elem = item_elem.find("numplays")
            numplays = 0
            if numplays_elem is not None:
                numplays = int(numplays_elem.text or "0")

            # Parse private info (inventory location, etc.)
            privateinfo_elem = item_elem.find("privateinfo")
            invlocation = None
            if privateinfo_elem is not None:
                # The attribute is called "inventorylocation", not "invlocation"
                invlocation = privateinfo_elem.get("inventorylocation")

            item_data = {
                "id": item_id,
                "name": name,
                "thumbnail": thumbnail,
                "minplayers": min_players,
                "maxplayers": max_players,
                "rating": rating,
                "wishlistpriority": wishlist_priority,
                "numplays": numplays,
                "invlocation": invlocation,
            }

            items.append(CollectionItem(id=item_id, _data=item_data))

        return items

    def game_list(self, game_ids):
        """Get information for multiple games.

        Args:
            game_ids: List of game IDs

        Returns:
            List of GameData objects
        """
        # BGG API accepts comma-separated IDs
        ids_str = ",".join(str(gid) for gid in game_ids)

        params = {"id": ids_str, "stats": 1, "type": "boardgame"}

        root = self._make_request("thing", params)

        # Parse all items
        games = []
        for item in root.findall("item"):
            games.append(self._parse_game_data(item))

        return games

    def get_user_id(self, user_name):
        """Get BGG user ID from username.

        Args:
            user_name: BGG username

        Returns:
            User ID as integer

        Raises:
            BGGApiError: If user not found
        """
        params = {"name": user_name, "type": "user"}
        root = self._make_request("user", params)

        user_id = root.get("id")
        if not user_id:
            raise BGGApiError(f"Could not get user ID for {user_name}")

        return int(user_id)

    def marketplace_listings(self, user_name):
        """Get a user's marketplace inventory listings.

        Args:
            user_name: BGG username

        Returns:
            List of marketplace listings with game info and prices

        Raises:
            BGGApiError: If API request fails
        """
        # First get the user ID
        user_id = self.get_user_id(user_name)
        logger.info(f"Found user ID: {user_id} for username: {user_name}")

        # Use the GeekDo marketplace API
        marketplace_url = "https://api.geekdo.com/api/market/products"
        params = {
            "ajax": 1,
            "browsetype": "inventory",
            "userid": user_id,
            "productstate": "active",
            "stock": "instock",
            "sort": "title",
            "pageid": 1,
        }

        try:
            response = self.session.get(
                marketplace_url, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            listings = []

            # Parse marketplace products
            if "products" in data:
                for product in data["products"]:
                    listing_data = {
                        "id": product.get("objectid"),
                        "price": product.get("price"),
                        "currency": product.get("currency"),
                        "condition": product.get("condition"),
                        "product_id": product.get("productid"),
                        "link": f"https://boardgamegeek.com/market/product/{product.get('productid')}",
                    }

                    # Only include if we have valid data
                    if listing_data["id"] and listing_data["price"]:
                        listings.append(listing_data)

            logger.info(f"Found {len(listings)} marketplace listings")
            return listings

        except requests.exceptions.RequestException as e:
            raise BGGApiError(f"Failed to fetch marketplace listings: {e}") from e
        except (KeyError, ValueError) as e:
            raise BGGApiError(f"Failed to parse marketplace data: {e}") from e
