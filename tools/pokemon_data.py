#!/usr/bin/env python3
"""
Pokemon Quiz Data Pipeline
Downloads FireRed/LeafGreen sprites, extracts dominant colors,
fetches types/stats/evolutions from PokeAPI, outputs JSON for the quiz.
"""

import json
import os
import time
from collections import Counter
from io import BytesIO

import numpy as np
import requests
from PIL import Image

SPRITE_DIR = os.path.join(os.path.dirname(__file__), "sprites")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "pokemon_quiz_data.json")

SPRITE_URL = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/versions/generation-iii/firered-leafgreen/{id}.png"
POKEAPI_URL = "https://pokeapi.co/api/v2"

GEN1_TYPES = [
    "normal", "fighting", "flying", "poison", "ground",
    "rock", "bug", "ghost", "fire", "water",
    "grass", "electric", "psychic", "ice", "dragon"
]

TYPE_COLORS = {
    "normal": "#A8A878",
    "fighting": "#C03028",
    "flying": "#A890F0",
    "poison": "#A040A0",
    "ground": "#E0C068",
    "rock": "#B8A038",
    "bug": "#A8B820",
    "ghost": "#705898",
    "fire": "#F08030",
    "water": "#6890F0",
    "grass": "#78C850",
    "electric": "#F8D030",
    "psychic": "#F85888",
    "ice": "#98D8D8",
    "dragon": "#7038F8",
}


def download_sprites():
    """Download all 151 FireRed/LeafGreen sprites."""
    os.makedirs(SPRITE_DIR, exist_ok=True)
    for i in range(1, 152):
        path = os.path.join(SPRITE_DIR, f"{i}.png")
        if os.path.exists(path):
            continue
        url = SPRITE_URL.format(id=i)
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            print(f"  Downloaded sprite {i}")
        else:
            print(f"  FAILED sprite {i}: {resp.status_code}")
        time.sleep(0.1)


def color_distance(c1, c2):
    """Simple Euclidean distance in RGB space."""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def extract_colors(sprite_path, num_colors=6, merge_threshold=30):
    """Extract dominant colors from a sprite, ignoring transparency."""
    img = Image.open(sprite_path).convert("RGBA")
    pixels = np.array(img)

    # Filter out transparent/near-transparent pixels
    mask = pixels[:, :, 3] > 128
    visible = pixels[mask][:, :3]

    if len(visible) == 0:
        return [{"hex": "#808080", "f": 1.0}]

    # Quantize using PIL for speed
    rgb_img = Image.fromarray(visible.reshape(-1, 1, 3).astype(np.uint8))
    quantized = rgb_img.quantize(colors=20, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[:60]  # 20 colors * 3 channels

    # Count pixels per palette index
    quant_pixels = np.array(quantized)
    counts = Counter(quant_pixels.flatten())

    # Build color list
    colors = []
    for idx, count in counts.most_common(20):
        if idx * 3 + 2 < len(palette):
            r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
            colors.append({"rgb": (r, g, b), "count": count})

    # Merge similar colors
    merged = []
    for c in colors:
        found = False
        for m in merged:
            if color_distance(c["rgb"], m["rgb"]) < merge_threshold:
                # Weighted average
                total = m["count"] + c["count"]
                m["rgb"] = tuple(
                    int((m["rgb"][i] * m["count"] + c["rgb"][i] * c["count"]) / total)
                    for i in range(3)
                )
                m["count"] = total
                found = True
                break
        if not found:
            merged.append(dict(c))

    # Sort by count, take top N
    merged.sort(key=lambda x: x["count"], reverse=True)
    top = merged[:num_colors]

    # Calculate fractions
    total_pixels = sum(c["count"] for c in top)
    result = []
    for c in top:
        r, g, b = c["rgb"]
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        fraction = round(c["count"] / total_pixels, 3)
        if fraction > 0.01:
            result.append({"hex": hex_color, "f": fraction})

    # Normalize fractions to sum to 1
    total_f = sum(c["f"] for c in result)
    for c in result:
        c["f"] = round(c["f"] / total_f, 3)

    # Fix rounding: ensure sum is exactly 1
    diff = 1.0 - sum(c["f"] for c in result)
    if result:
        result[0]["f"] = round(result[0]["f"] + diff, 3)

    return result


def fetch_pokemon_data():
    """Fetch types, stats, and evolution data from PokeAPI."""
    pokemon_list = []

    for i in range(1, 152):
        resp = requests.get(f"{POKEAPI_URL}/pokemon/{i}", timeout=10)
        data = resp.json()

        types = [t["type"]["name"] for t in data["types"]]
        # Filter to Gen 1 types only (Steel/Dark/Fairy didn't exist)
        types = [t for t in types if t in GEN1_TYPES]

        stats = sum(s["base_stat"] for s in data["stats"])

        pokemon_list.append({
            "id": i,
            "name": data["name"].capitalize(),
            "types": types,
            "bst": stats,
        })

        if i % 10 == 0:
            print(f"  Fetched data for {i}/151")
        time.sleep(0.3)

    return pokemon_list


def fetch_evolution_chains():
    """Fetch evolution chain data for Gen 1 Pokemon."""
    evolutions = []  # [{from_id, to_id}]
    seen_chains = set()

    for i in range(1, 152):
        resp = requests.get(f"{POKEAPI_URL}/pokemon-species/{i}", timeout=10)
        data = resp.json()
        chain_url = data["evolution_chain"]["url"]
        chain_id = chain_url.rstrip("/").split("/")[-1]

        if chain_id in seen_chains:
            continue
        seen_chains.add(chain_id)

        chain_resp = requests.get(chain_url, timeout=10)
        chain_data = chain_resp.json()["chain"]

        def walk_chain(node):
            species_id = int(node["species"]["url"].rstrip("/").split("/")[-1])
            for evo in node["evolves_to"]:
                evo_id = int(evo["species"]["url"].rstrip("/").split("/")[-1])
                # Only include Gen 1 Pokemon
                if species_id <= 151 and evo_id <= 151:
                    evolutions.append({"from": species_id, "to": evo_id})
                walk_chain(evo)

        walk_chain(chain_data)

        if len(seen_chains) % 10 == 0:
            print(f"  Fetched {len(seen_chains)} evolution chains...")
        time.sleep(0.3)

    return evolutions


def analyze_difficulty(pokemon_list):
    """Find Pokemon with very similar color profiles."""
    print("\n=== DIFFICULTY ANALYSIS ===\n")

    # Compare all pairs
    similar_pairs = []
    for i, p1 in enumerate(pokemon_list):
        for j, p2 in enumerate(pokemon_list):
            if j <= i:
                continue
            # Compare color profiles
            colors1 = {c["hex"]: c["f"] for c in p1["colors"]}
            colors2 = {c["hex"]: c["f"] for c in p2["colors"]}

            # Calculate similarity based on dominant color overlap
            all_colors = set(list(colors1.keys()) + list(colors2.keys()))
            similarity = 0
            for c in all_colors:
                f1 = colors1.get(c, 0)
                f2 = colors2.get(c, 0)
                similarity += min(f1, f2)

            # Also check if dominant colors are close in RGB space
            dom1 = p1["colors"][0]["hex"]
            dom2 = p2["colors"][0]["hex"]
            rgb1 = tuple(int(dom1[i:i+2], 16) for i in (1, 3, 5))
            rgb2 = tuple(int(dom2[i:i+2], 16) for i in (1, 3, 5))
            dom_distance = color_distance(rgb1, rgb2)

            # High similarity + close dominant colors = potentially confusing
            if similarity > 0.5 and dom_distance < 50:
                similar_pairs.append({
                    "p1": p1["name"],
                    "p2": p2["name"],
                    "similarity": round(similarity, 3),
                    "dom_distance": round(dom_distance, 1),
                    "same_type": bool(set(p1["types"]) & set(p2["types"])),
                    "bst_diff": abs(p1["bst"] - p2["bst"]),
                })

    similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)

    print(f"Found {len(similar_pairs)} potentially confusing pairs:\n")
    for pair in similar_pairs[:30]:
        distinguisher = ""
        if pair["bst_diff"] > 50:
            distinguisher = f" [SIZE HELPS: BST diff={pair['bst_diff']}]"
        elif not pair["same_type"]:
            distinguisher = " [TYPES DIFFER]"
        else:
            distinguisher = " *** VERY HARD ***"

        print(f"  {pair['p1']:15s} vs {pair['p2']:15s} "
              f"(similarity={pair['similarity']}, dom_dist={pair['dom_distance']})"
              f"{distinguisher}")

    return similar_pairs


def main():
    print("=== Pokemon Quiz Data Pipeline ===\n")

    # Step 1: Download sprites
    print("1. Downloading sprites...")
    download_sprites()

    # Step 2: Extract colors
    print("\n2. Extracting colors from sprites...")
    all_colors = {}
    for i in range(1, 152):
        path = os.path.join(SPRITE_DIR, f"{i}.png")
        if os.path.exists(path):
            all_colors[i] = extract_colors(path)
        else:
            all_colors[i] = [{"hex": "#808080", "f": 1.0}]
        if i % 20 == 0:
            print(f"  Processed {i}/151 sprites")

    # Step 3: Fetch Pokemon data
    print("\n3. Fetching Pokemon data from PokeAPI...")
    pokemon_list = fetch_pokemon_data()

    # Step 4: Fetch evolution chains
    print("\n4. Fetching evolution chains...")
    evolutions = fetch_evolution_chains()

    # Combine colors with pokemon data
    for p in pokemon_list:
        p["colors"] = all_colors[p["id"]]

    # Step 5: Difficulty analysis
    similar_pairs = analyze_difficulty(pokemon_list)

    # Step 6: Output JSON
    output = {
        "pokemon": pokemon_list,
        "evolutions": evolutions,
        "types": GEN1_TYPES,
        "type_colors": TYPE_COLORS,
        "similar_pairs": similar_pairs[:20],
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Done! Output written to {OUTPUT_FILE} ===")
    print(f"  {len(pokemon_list)} Pokemon")
    print(f"  {len(evolutions)} evolution links")
    print(f"  {len(similar_pairs)} similar pairs flagged")


if __name__ == "__main__":
    main()
