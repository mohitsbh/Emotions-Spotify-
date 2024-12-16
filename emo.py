import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import random
import cv2
import webbrowser
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# Emotion-to-genre mapping
EMOTION_TO_GENRE = {
    'Happy': ['pop', 'dance', 'hip-hop'],
    'Sad': ['blues', 'classical', 'acoustic'],
    'Angry': ['rock', 'metal', 'punk'],
    'Surprise': ['electronic', 'dance', 'trap'],
    'Neutral': ['ambient', 'chillout', 'lo-fi']
}

# Language-to-genre mapping for different languages
LANGUAGE_TO_GENRE = {
    'English': ['pop', 'dance', 'hip-hop', 'blues', 'classical', 'rock'],
    'Spanish': ['reggaeton', 'bailando', 'salsa', 'flamenco'],
    'French': ['chanson', 'pop', 'electronic'],
    'Marathi': ['Marathi pop', 'Marathi film songs', 'Bhavageet'],
    'Hindi': ['Bollywood', 'Indie', 'Pop'],
    'Bengali': ['Bengali folk', 'Rabindra Sangeet'],
    'Tamil': ['Kollywood', 'Tamil folk'],
    'Punjabi': ['Bhangra', 'Punjabi pop'],
    'Telugu': ['Tollywood', 'Telugu songs']
}

MUSIC_RECOMMENDATIONS = {
    'pop': ['Blinding Lights', 'Levitating', 'Shape of You', 'Happier'],
    'dance': ['Titanium', 'Turn Down for What', 'Dancing On My Own'],
    'hip-hop': ['Sicko Mode', 'HUMBLE.', 'God\'s Plan'],
    'blues': ['The Thrill Is Gone', 'Ain\'t No Sunshine'],
    'classical': ['Für Elise', 'Clair de Lune', 'Canon in D'],
    'rock': ['Bohemian Rhapsody', 'Hotel California'],
    'Marathi pop': ['Zingaat', 'Kiti Sangaychay', 'Gani Tujhi'],
    'Marathi film songs': ['Swaasthay Mhanje', 'Apsara Aali', 'Jeev Mhane'],
    'Bhavageet': ['Mann He Gajali', 'Jagve Nagati Chandanye'],
    'Hindi': {
        'Happy': ['Phoolon Ka Taron Ka', 'Nashe Si Chadh Gayi', 'Dil Dhadakne Do'],
        'Sad': ['Channa Mereya', 'Tum Hi Ho', 'Tujhe Kitna Chahne Lage Hum'],
        'Angry': ['Jashn-e-Ishqa', 'Akkad Bakkad', 'Malang'],
        'Surprise': ['Kala Chashma', 'Swag Se Swagat', 'Urvashi'],
        'Neutral': ['Tum Jo Aaye', 'Tum Tak', 'Raabta']
    },
    'Marathi': {
        'Happy': ['Zingaat', 'Kiti Sangaychay', 'Gani Tujhi'],
        'Sad': ['Tujhya Rojicha', 'Jeev Mi Tontya Kela', 'Mann He Gajali', 'Madhurani', 'Jeev Mhane'],
        'Angry': ['Swaasthay Mhanje', 'Apsara Aali', 'Jeev Mhane'],
        'Surprise': ['Jeev Dhotyahi', 'Taryanche Bhatke', 'Kahich Nathe Thodasa'],
        'Neutral': ['Sundara Manamali', 'Kahi Kahi Samajh Kuni', 'Phool Deta Mazhe']
    },
    'English': {
        'Happy': ['Happy', 'Can\'t Stop the Feeling!', 'Uptown Funk'],
        'Sad': ['Someone Like You', 'Stay', 'The Scientist'],
        'Angry': ['Breaking the Habit', 'Bohemian Rhapsody', 'Smells Like Teen Spirit'],
        'Surprise': ['Rolling in the Deep', 'Firework', 'Shake It Off'],
        'Neutral': ['Perfect', 'Shape of You', 'All of Me']
    }
}

# Spotify credentials (replace with your credentials or leave blank for no Spotify)
SPOTIFY_CLIENT_ID = "979cb63990c94208b902ef2932e2de92"
SPOTIFY_CLIENT_SECRET = "25dc451e6f374a1a8f35d658fd41ec75"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"


class EmotionMusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Emotion-Based Music Player")
        self.root.geometry("1000x800")
        self.root.configure(bg="#F5F5F5")

        # Canvas for scrolling
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar setup
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        # Create a frame inside the canvas
        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind frame resize to canvas scrolling region
        self.scrollable_frame.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Emotion and language variables
        self.emotion = tk.StringVar(value="Detecting...")
        self.language = tk.StringVar(value="English")

        # Initialize Spotify (optional)
        try:
            self.spotify = Spotify(auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
            ))
        except Exception as e:
            print("Spotify not set up properly:", e)
            self.spotify = None

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.cap = cv2.VideoCapture(0)

        # Create the GUI
        self.create_widgets()

        if self.cap.isOpened():
            self.update_camera_feed()
        else:
            messagebox.showerror("Error", "Camera is not accessible.")

    def create_widgets(self):
        # Title label
        tk.Label(self.scrollable_frame, text="Emotion-Based Music Player",
                 font=("Helvetica", 24), bg="#F5F5F5").pack(pady=10)

        # Detected emotion label
        tk.Label(self.scrollable_frame, text="Detected Emotion:",
                 font=("Helvetica", 18), bg="#F5F5F5").pack(pady=5)
        tk.Label(self.scrollable_frame, textvariable=self.emotion, font=("Helvetica", 20, "bold"),
                 fg="blue", bg="#F5F5F5").pack(pady=10)

        # Language selection dropdown
        tk.Label(self.scrollable_frame, text="Select Language:",
                 font=("Helvetica", 14), bg="#F5F5F5").pack(pady=5)
        self.language_combo = ttk.Combobox(
            self.scrollable_frame, textvariable=self.language,
            values=["English", "Spanish", "French", "Marathi",
                    "Hindi", "Bengali", "Tamil", "Punjabi", "Telugu"],
            font=("Helvetica", 14), state="readonly"
        )
        self.language_combo.pack(pady=5)

        # Video frame placeholder
        self.video_frame = tk.Label(self.scrollable_frame, bg="#000000", width=500, height=300)
        self.video_frame.pack(pady=20)

        # Buttons
        tk.Button(self.scrollable_frame, text="Capture & Recommend Songs", command=self.capture_and_recommend,
                  font=("Helvetica", 16), bg="green", fg="white").pack(pady=10)

        self.song_listbox = tk.Listbox(self.scrollable_frame, height=10, font=("Helvetica", 14), selectmode=tk.SINGLE)
        self.song_listbox.pack(pady=20, fill=tk.X, padx=20)

        tk.Button(self.scrollable_frame, text="Play on Spotify", command=self.play_song_on_spotify,
                  font=("Helvetica", 16), bg="blue", fg="white").pack(pady=10)

        tk.Button(self.scrollable_frame, text="Select Song Without Spotify", command=self.play_song_without_spotify,
                  font=("Helvetica", 16), bg="orange", fg="white").pack(pady=10)

    def update_camera_feed(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_frame.imgtk = imgtk
            self.video_frame.configure(image=imgtk)
        self.root.after(10, self.update_camera_feed)

    def detect_emotion_from_frame(self, frame):
        emotions = ['Happy', 'Sad', 'Angry', 'Surprise', 'Neutral']
        return random.choice(emotions)  # Simulated emotion detection

    def capture_and_recommend(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            detected_emotion = self.detect_emotion_from_frame(frame)
            self.emotion.set(detected_emotion)
            self.get_music_recommendations()
        else:
            messagebox.showerror("Error", "Failed to capture image.")

    def get_music_recommendations(self):
        selected_language = self.language.get()
        detected_emotion = self.emotion.get()

        language_genres = LANGUAGE_TO_GENRE.get(selected_language, [])
        emotion_genres = EMOTION_TO_GENRE.get(detected_emotion, [])

        all_genres = set(language_genres + emotion_genres)
        recommendations = [
            song for genre in all_genres for song in MUSIC_RECOMMENDATIONS.get(genre, [])]

        self.song_listbox.delete(0, tk.END)
        if recommendations:
            for song in recommendations:
                self.song_listbox.insert(tk.END, song)
        else:
            self.song_listbox.insert(tk.END, "No songs available for the combination.")

    def play_song_on_spotify(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song and self.spotify:
            result = self.spotify.search(q=selected_song, type="track", limit=1)
            if result['tracks']['items']:
                track_url = result['tracks']['items'][0]['external_urls']['spotify']
                webbrowser.open(track_url)
            else:
                messagebox.showerror("Spotify Error", "Song not found on Spotify.")

    def play_song_without_spotify(self):
        selected_song = self.song_listbox.get(tk.ACTIVE)
        if selected_song:
            song_url = f"https://www.youtube.com/results?search_query={selected_song.replace(' ', '+')}"
            webbrowser.open(song_url)  # Open the YouTube search result
        else:
            messagebox.showwarning("No Selection", "Please select a song from the list.")


# Running the application
if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionMusicPlayer(root)
    root.mainloop()
