This is my first project, it works perfectly at home so hopefully it will for you, via my instructions.
I have a lot of photos / videos so I wanted some way to review them, and organise them. 
Using Flask and Pillow I (with lots of ChatGPT help), have created a photo / video gallery.
It can be used to rate photos, give photos a description, and order by rating in each gallery.
I have mine in C:\Photogallery - but with minor editing you can put it anywhere.
First install Flask and Pillow (follow their instructions, to do this).
Now put all files into you base directory.
Create folders "Templates" and "Static" from your base directory
Move all HTML files into Templates
In Static, create another sub directory "images"
Then in "images" make sub directories for each year (2024, 2023, 2022 etc etc - as many as you need. Mine goes back to 2004)
Add to each year, named photo galleries. I.e Static/images/2024/Summer Holiday 2024/"all your images".JPG or PNG
(Optional but looks loads better) In each gallery, make 1 image "thumbnail.jpg" as this will be the thumbnail used in the index.html gallery list.
Best to make a copy, and rename it to "thumbnail.jpg". Repeat (if you want) for each gallery.
Create a blank "ratings.JSON" file in your base directory.
For videos, I put onto youtube and edit the code in app.py to each video and playlist (I have my examples so you will work out what to change).
But to help a bit, it looks like this:

def videos():
    videos = [
        {'youtube_id': 'ZMrkiWmcUxQ', 'description': 'GO APE Sherwood forest 140 meter zip line', 'year': '2024'},
        {'youtube_id': '4WcL7oh6r_k', 'description': '17 Minutes of Storm Winds at Tenesar', 'year': '2022'},
    ]
    
    playlists = [
        {'playlist_id': 'PLSfc-h9OXZn3vU9Pu8IYeQWntY5hE0goF', 'description': 'Black Forest 2024', 'year': '2024'},
        {'playlist_id': 'PLSfc-h9OXZn0YlUA2JWquYpaNHZ6j0uze', 'description': 'Travelling Lanzarote', 'year': '2022'},

You just need to edit the youtube ID or playlist ID, the description and year - simple really
Run run_gallery.bat (I suggest making this run automatically when starting windows)
Go to your browser and type in 127.0.0.1:5000 and all should be good
