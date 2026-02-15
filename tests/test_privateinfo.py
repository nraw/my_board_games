"""Test script to check if we can get private info from BGG collection API."""

import os

from my_board_games.bgg_api import BGGClient
from my_board_games.settings import conf

def test_privateinfo():
    bgg = BGGClient()
    username = conf["user_name"]

    print(f"Testing collection for user: {username}")
    print(f"API Key present: {bool(os.environ.get('BGG_API_KEY'))}\n")

    # Test the collection method which now includes showprivate=1
    collection_items = bgg.collection(
        user_name=username,
        own=True,
        exclude_subtype="boardgameexpansion"
    )

    print(f"Found {len(collection_items)} items via collection() method")

    # Check the raw data
    for item in collection_items[:3]:
        print(f"\nSample item: {item._data.get('name')}")
        print(f"  Has invlocation key: {'invlocation' in item._data}")
        print(f"  invlocation value: {item._data.get('invlocation')}")

    # Now also make a direct API call to see the raw XML
    params = {
        "username": username,
        "own": 1,
        "stats": 1,
        "excludesubtype": "boardgameexpansion",
        "showprivate": 1
    }

    root = bgg._make_request("collection", params)

    # Check all items for inventory location
    items = root.findall("item")
    print(f"Found {len(items)} items in collection")

    items_with_location = []
    items_with_privateinfo = []
    items_without_privateinfo = []

    for item in items:
        name_elem = item.find("name")
        name = name_elem.text if name_elem is not None else "Unknown"
        item_id = item.get("objectid")

        # Check for privateinfo
        privateinfo = item.find("privateinfo")
        if privateinfo is not None:
            invlocation = privateinfo.get("inventorylocation")
            items_with_privateinfo.append({
                "id": item_id,
                "name": name,
                "location": invlocation or "(empty)",
                "all_attrs": dict(privateinfo.attrib)
            })
            if invlocation:
                items_with_location.append({
                    "id": item_id,
                    "name": name,
                    "location": invlocation
                })
        else:
            items_without_privateinfo.append(name)

    print(f"\n{'='*60}")
    print(f"Items WITH privateinfo element: {len(items_with_privateinfo)}")
    print(f"{'='*60}")
    for item in items_with_privateinfo:
        print(f"  - {item['name']} (ID: {item['id']})")
        print(f"      invlocation: '{item['location']}'")
        print(f"      all attributes: {item['all_attrs']}")

    print(f"\n{'='*60}")
    print(f"Items WITH inventory location set: {len(items_with_location)}")
    print(f"{'='*60}")
    for item in items_with_location:
        print(f"  - {item['name']} (ID: {item['id']}) -> Location: '{item['location']}'")

    print(f"\n{'='*60}")
    print(f"Items WITHOUT privateinfo element: {len(items_without_privateinfo)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    test_privateinfo()
