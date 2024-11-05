import os
import json
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for
from PIL import Image
from collections import Counter
import re
import logging

app = Flask(__name__)

# Increase the maximum image size limit to allow large images
Image.MAX_IMAGE_PIXELS = None  # Remove the limit entirely for large images

# Path to the images directory
IMAGES_DIR = os.path.join('Static', 'images')

# Load ratings from the JSON file
def load_ratings():
    if os.path.exists('ratings.json'):
        with open('ratings.json', 'r') as f:
            return json.load(f)
    return {}

# Save ratings to the JSON file
def save_ratings(ratings):
    with open('ratings.json', 'w') as f:
        json.dump(ratings, f, indent=4)

# Load ratings when the app starts
ratings = load_ratings()

# Function to create thumbnails
def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    try:
        with Image.open(image_path) as img:
            # Check for orientation
            try:
                for orientation in img._getexif() or {}:
                    if orientation == 274:
                        if img._getexif()[orientation] == 3:
                            img = img.rotate(180, expand=True)
                        elif img._getexif()[orientation] == 6:
                            img = img.rotate(270, expand=True)
                        elif img._getexif()[orientation] == 8:
                            img = img.rotate(90, expand=True)
            except (AttributeError, TypeError, KeyError, IndexError):
                pass

            img.thumbnail(size, Image.LANCZOS)
            img.save(thumbnail_path)
            print(f"Thumbnail created for {image_path}")
    except Image.DecompressionBombError as e:
        print(f"DecompressionBombError for file {image_path}: {e}. Skipping this file.")
    except OSError as e:
        print(f"Error processing file {image_path}: {e}. Skipping this file.")

# Function to generate thumbnails for all images in a gallery
def generate_thumbnails(year, gallery_name):
    gallery_path = os.path.join(IMAGES_DIR, year, gallery_name)
    thumbnail_dir = os.path.join(gallery_path, 'thumbnails')
    
    os.makedirs(thumbnail_dir, exist_ok=True)

    for root, _, files in os.walk(gallery_path):
        for img in files:
            if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_path = os.path.join(root, img)
                thumbnail_path = os.path.join(thumbnail_dir, img)
                if not os.path.exists(thumbnail_path):
                    create_thumbnail(image_path, thumbnail_path)

# Check if an image is landscape or portrait
def is_landscape(image_path):
    img = Image.open(image_path)
    return img.width > img.height
    
# Function to extract the three most common words from descriptions
def get_most_common_words(image_data):
    words = []
    
    for data in image_data.values():
        description = data.get('description', '')
        # Normalize and tokenize the description
        words.extend(re.findall(r'\b\w+\b', description.lower()))  # Extract words
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Get the three most common words
    most_common_words = word_counts.most_common(10)
    
    return most_common_words
    
@app.context_processor
def utility_processor():
    return dict(is_landscape=is_landscape)

@app.route('/gallery/<year>/<gallery_name>', defaults={'subdirectory': None})
@app.route('/gallery/<year>/<gallery_name>/<path:subdirectory>')
def gallery(year, gallery_name, subdirectory):
    # Construct the gallery path based on whether a subdirectory is provided
    if subdirectory:
        gallery_path = os.path.join(IMAGES_DIR, year, gallery_name, subdirectory)
    else:
        gallery_path = os.path.join(IMAGES_DIR, year, gallery_name)

    # Check if the gallery path exists
    if not os.path.exists(gallery_path):
        return f"Gallery path does not exist: {gallery_path}", 404

    # Generate thumbnails for the images if necessary
    generate_thumbnails(year, gallery_name)

    images = []
    subdirectories = []  # Initialize subdirectories list
    # Walk through the gallery directory to find image files
    for root, dirs, files in os.walk(gallery_path):
        # Collect subdirectory names
        for d in dirs:
            if d.lower() != 'thumbnails':
                subdirectories.append(os.path.relpath(os.path.join(root, d), IMAGES_DIR).replace("\\", "/"))
        for img in files:
            # Check for image file types and exclude thumbnails
            if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and 'thumbnails' not in root:
                relative_path = os.path.relpath(os.path.join(root, img), IMAGES_DIR)
                images.append(relative_path.replace("\\", "/"))

    images.sort()  # Sort images alphabetically

    # Load ratings for the images
    image_data = {img: ratings.get(f'{year}/{gallery_name}/{img}', {"rating": "Unrated", "description": ""}) for img in images}

    # Get the most common words from the descriptions
    most_common_words = get_most_common_words(image_data)

    # Sort images by rating in a specified order
    sort_order = {'Best': 1, 'Good': 2, 'Average': 3, 'Unrated': 4, 'Worst': 5, 'To Delete': 6}
    sorted_images = sorted(images, key=lambda img: sort_order.get(image_data[img]['rating'], 7))  # Default to 7 for unrated

    # Count images by rating
    count_best = sum(1 for img in images if image_data[img]['rating'] == 'Best')
    count_good = sum(1 for img in images if image_data[img]['rating'] == 'Good')
    count_average = sum(1 for img in images if image_data[img]['rating'] == 'Average')
    count_unrated = sum(1 for img in images if image_data[img]['rating'] == 'Unrated')
    count_worst = sum(1 for img in images if image_data[img]['rating'] == 'Worst')
    count_to_delete = sum(1 for img in images if image_data[img]['rating'] == 'To Delete')
    total_images = len(images)

    # Count images without descriptions
    count_no_description = sum(1 for img in images if not image_data[img].get('description'))

    return render_template(
        'gallery.html',
        images=sorted_images,
        gallery_name=gallery_name,
        year=year,
        subdirectories=subdirectories,  # Pass subdirectories to template
        image_data=image_data,
        count_best=count_best,
        count_good=count_good,
        count_average=count_average,
        count_unrated=count_unrated,
        count_worst=count_worst,
        count_to_delete=count_to_delete,
        total_images=total_images,
        count_no_description=count_no_description,
        most_common_words=most_common_words  # Pass most common words to template
    )

import os

@app.route('/')
def index():
    years = sorted(os.listdir(IMAGES_DIR), reverse=True)
    galleries_by_year = {}

    def count_images_in_directory(directory):
        """Recursively count images in a directory and its subdirectories, excluding the 'thumbnails' folder."""
        total_images = 0
        for root, dirs, files in os.walk(directory):
            # Skip the 'thumbnails' directory
            if 'thumbnails' in dirs:
                dirs.remove('thumbnails')  # This will prevent os.walk from going into the 'thumbnails' directory
            
            # Count files with the specified image extensions
            total_images += len([img for img in files if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))])
        return total_images

    for year in years:
        year_path = os.path.join(IMAGES_DIR, year)
        if os.path.isdir(year_path):
            galleries = sorted(os.listdir(year_path))
            galleries_with_count = {}

            for gallery_name in galleries:
                gallery_path = os.path.join(year_path, gallery_name)
                if os.path.isdir(gallery_path):  # Ensure it's a directory
                    # Count images in the gallery including subdirectories, excluding 'thumbnails'
                    image_count = count_images_in_directory(gallery_path)
                    galleries_with_count[gallery_name] = image_count

            galleries_by_year[year] = galleries_with_count

    return render_template('index.html', galleries_by_year=galleries_by_year, years=years)
    
@app.route('/galleries')
def galleries():
    return index()

@app.route('/rate', methods=['POST'])
def rate_image():
    # Get form data
    year = request.form.get('year')
    gallery_name = request.form.get('gallery_name')
    image_name = request.form.get('image_name')
    new_description = request.form.get('description')
    new_rating = request.form.get('rating')

    # Validate the required data
    if not year or not gallery_name or not image_name:
        return jsonify({"error": "Image not found.", "success": False}), 400

    # Update ratings data
    key = f"{year}/{gallery_name}/{image_name}"
    ratings[key] = {"rating": new_rating, "description": new_description}

    # Save the ratings back to the JSON file
    try:
        save_ratings(ratings)  # Assume this function handles saving and can raise exceptions
    except Exception as e:
        return jsonify({"error": f"Failed to save ratings: {str(e)}", "success": False}), 500

    # Return a success response instead of redirecting
    return jsonify({"success": True, "new_rating": new_rating, "new_description": new_description})
@app.route('/search', methods=['GET'])
def search():
    search_term = request.args.get('q', '').lower()
    year = request.args.get('year', '')
    rating = request.args.get('rating', '')
    results = []
    ratings_count = {
        "count_best": 0,
        "count_average": 0,
        "count_unrated": 0,
        "count_worst": 0,
        "count_to_delete": 0,
    }
    count_no_description = 0

    if not search_term and not year and not rating:
        return render_template('search_results.html', results=results, total_images=0, count_no_description=0, **ratings_count)

    try:
        for year_dir in os.listdir(IMAGES_DIR):
            year_path = os.path.join(IMAGES_DIR, year_dir)
            if os.path.isdir(year_path) and (not year or year == year_dir):  # Filter by year if specified
                for gallery_name in os.listdir(year_path):
                    gallery_path = os.path.join(year_path, gallery_name)
                    if os.path.isdir(gallery_path) and "thumbnails" not in gallery_name.lower():  # Skip the "thumbnails" directory
                        for root, _, files in os.walk(gallery_path):
                            # Skip subdirectories like "thumbnails"
                            if "thumbnails" in root.lower():
                                continue

                            for img in files:
                                if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                                    image_path = os.path.relpath(os.path.join(root, img), IMAGES_DIR).replace('\\', '/')
                                    key = f"{year_dir}/{gallery_name}/{year_dir}/{gallery_name}/{img}".replace('\\', '/')
                                    description = ratings.get(key, {}).get('description', '').lower()

                                    if (not search_term or search_term in img.lower() or search_term in description) and (not rating or ratings.get(key, {}).get('rating') == rating):
                                        results.append({
                                            'path': image_path,
                                            'rating': ratings.get(key, {}).get('rating', 'Unrated'),
                                            'description': description,
                                        })

                                        # Count ratings
                                        rating_value = ratings.get(key, {}).get('rating', 'Unrated')
                                        if rating_value == 'Best':
                                            ratings_count["count_best"] += 1
                                        elif rating_value == 'Good':
                                            ratings_count["count_good"] += 1
                                        elif rating_value == 'Average':
                                            ratings_count["count_average"] += 1
                                        elif rating_value == 'Worst':
                                            ratings_count["count_worst"] += 1
                                        elif rating_value == 'To Delete':
                                            ratings_count["count_to_delete"] += 1
                                        else:
                                            ratings_count["count_unrated"] += 1

                                        if not description:
                                            count_no_description += 1

        # Sort the results by the custom order: Best, Average, Unrated, Worst, To Delete
        sort_order = {'Best': 1, 'Average': 2, 'Unrated': 3, 'Worst': 4, 'To Delete': 5}
        results.sort(key=lambda x: sort_order.get(x['rating'], 6))  # Default to 6 for 'Unrated'

    except Exception as e:
        print(f"Error during search: {e}")

    total_images = len(results)
    return render_template('search_results.html', results=results, total_images=total_images, count_no_description=count_no_description, query=search_term, year=year, rating=rating, **ratings_count)

@app.route('/delete', methods=['POST'])
def delete_photo():
    year = request.form.get('year')
    gallery_name = request.form.get('gallery_name')
    image_name = request.form.get('image_name')
    
    image_path = os.path.join(IMAGES_DIR, year, gallery_name, image_name)
    
    if os.path.exists(image_path):
        os.remove(image_path)

    key = f"{year}/{gallery_name}/{image_name}"
    if key in ratings:
        del ratings[key]

    save_ratings(ratings)

    return redirect(url_for('gallery', year=year, gallery_name=gallery_name))

@app.route('/videos')
def videos():
    videos = [
        {'youtube_id': 'ZMrkiWmcUxQ', 'description': 'GO APE Sherwood forest 140 meter zip line', 'year': '2024'},
        {'youtube_id': '4WcL7oh6r_k', 'description': '17 Minutes of Storm Winds at Tenesar', 'year': '2022'},
    ]
    
    playlists = [
        {'playlist_id': 'PLSfc-h9OXZn3vU9Pu8IYeQWntY5hE0goF&si=XiAP4P3I_WFj7Yzt', 'description': 'Black Forest 2024', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn0YlUA2JWquYpaNHZ6j0uze', 'description': 'Travelling Lanzarote', 'year': '2022'},
        {'playlist_id': 'PLSfc-h9OXZn1kSjD-oPLtwvZmddVXJj4t&si=e8ZM3B3VEMf9TxLg', 'description': 'Summer Party 2024', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn1YXyDGyr70Y9Y_VP012owB', 'description': 'Wells next the Sea on RNLI Lucy Laver - June 2024', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn1ST8VgeTvSgD5Q3U9c5L1T', 'description': 'Purrr Cafe, Kings Lynn - February 2024', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn0npgKUJdzvTPCVv_WpRslI&si=BxtVL34pF0rLXa9c', 'description': 'Iceland 2012 - Highlights', 'year': '2012'},
        {'playlist_id': 'PLSfc-h9OXZn2_OTMz716wWNBdn-LUl5RX&pp=gAQBiAQB', 'description': 'Sun, Moon and Stars Timelapse Photography.', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn1_2p7popD1P_G5-3fNDGrB&si=-GAp81p5as2b2FQa', 'description': 'The Adventures of Ian in Lanzarote - May 2024', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn0YlUA2JWquYpaNHZ6j0uze', 'description': 'Travelling Lanzarote', 'year': '2022'},
        {'playlist_id': 'PLSfc-h9OXZn1kSjD-oPLtwvZmddVXJj4t', 'description': 'Summer Party 2024', 'year': '2024'},
       
    ]
        
    # Grouping videos by year
    videos_by_year = {}
    for video in videos:
        year = video['year']
        if year not in videos_by_year:
            videos_by_year[year] = {'videos': [], 'playlists': []}
        videos_by_year[year]['videos'].append(video)

    for playlist in playlists:
        year = playlist['year']
        if year not in videos_by_year:
            videos_by_year[year] = {'videos': [], 'playlists': []}
        videos_by_year[year]['playlists'].append(playlist)

    return render_template('videos.html', video_gallery_name='My Video Gallery', videos_by_year=videos_by_year)

@app.route('/random')
def random_gallery():
    years = sorted(os.listdir(IMAGES_DIR))

    if not years:
        return "No galleries available."

    random_year = random.choice(years)
    galleries = os.listdir(os.path.join(IMAGES_DIR, random_year))
    random_gallery_name = random.choice(galleries) if galleries else "No galleries available."

    return redirect(url_for('gallery', year=random_year, gallery_name=random_gallery_name))
# Route for sorting images based on ratings
@app.route('/sort', methods=['POST'])
def sort_images():
    # Assuming you pass gallery data and order via form data
    year = request.form.get('year')
    gallery_name = request.form.get('gallery_name')
    order = request.form.get('order')  # Order could be "Best", "Average", "Unrated", etc.
    
    # Load the images and ratings for sorting
    gallery_path = os.path.join(IMAGES_DIR, year, gallery_name)
    if not os.path.exists(gallery_path):
        return jsonify({"error": "Gallery not found"}), 404
    
    images = []
    for root, _, files in os.walk(gallery_path):
        for img in files:
            if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                relative_path = os.path.relpath(os.path.join(root, img), IMAGES_DIR)
                images.append(relative_path.replace("\\", "/"))

    image_data = {img: ratings.get(f'{year}/{gallery_name}/{img}', {"rating": "Unrated", "description": ""}) for img in images}

    # Sort based on the specified order
    sort_order = {'Best': 1, 'Average': 2, 'Unrated': 3, 'Worst': 4, 'To Delete': 5}
    sorted_images = sorted(images, key=lambda img: sort_order.get(image_data[img]['rating'], 6))

    return jsonify({"images": sorted_images})

if __name__ == '__main__':
    app.run(debug=True)
