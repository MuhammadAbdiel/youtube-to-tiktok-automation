import os
import time
import logging
from datetime import datetime
import feedparser
from pytube import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.config import change_settings
import yt_dlp
import subprocess

change_settings({"IMAGEMAGICK_BINARY": r"D:\\program files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self, config):
        """Initialize video downloader with configuration"""
        self.config = config
        self.processed_videos = self.load_processed_videos()
    
    def load_processed_videos(self):
        """Load list of already processed videos"""
        import json
        processed_file = 'processed_videos.json'
        if os.path.exists(processed_file):
            with open(processed_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_processed_videos(self):
        """Save list of processed videos"""
        import json
        with open('processed_videos.json', 'w') as f:
            json.dump(list(self.processed_videos), f)
    
    def check_new_videos(self):
        """Check for new videos from monitored channels"""
        new_videos = []
        
        for channel_name, channel_info in self.config['channels'].items():
            try:
                feed = feedparser.parse(channel_info['rss_url'])
                
                for entry in feed.entries:
                    video_id = entry.yt_videoid
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Check if video is new (within last 24 hours) and not processed
                    published_time = datetime(*entry.published_parsed[:6])
                    if (datetime.now() - published_time).days == 0 and video_id not in self.processed_videos:
                        new_videos.append({
                            'channel': channel_name,
                            'video_id': video_id,
                            'url': video_url,
                            'title': entry.title,
                            'published': published_time
                        })
                        
            except Exception as e:
                logger.error(f"Error checking {channel_name}: {str(e)}")
        
        return new_videos
    
    def download_with_ytdlp(self, video_url, output_path):
        """Download video using yt-dlp as backup method"""
        try:
            # Extract video ID from URL
            video_id = video_url.split('v=')[1].split('&')[0]
            
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(output_path, f'{video_id}.%(ext)s'),
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                
            # Find the downloaded file
            for file in os.listdir(output_path):
                if file.startswith(video_id):
                    return os.path.join(output_path, file)
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading with yt-dlp {video_url}: {str(e)}")
            return None
    
    def download_video(self, video_url, output_path):
        """Download video from YouTube with fallback methods"""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to download {video_url} (attempt {attempt + 1}/{max_retries})")
                
                # Try pytube first
                try:
                    yt = YouTube(video_url)
                    
                    # Get highest quality video with audio
                    video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    
                    if not video_stream:
                        # Fallback to adaptive streams
                        video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()
                        audio_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_audio=True).order_by('abr').desc().first()
                        
                        if video_stream and audio_stream:
                            video_path = video_stream.download(output_path, filename_prefix='video_')
                            audio_path = audio_stream.download(output_path, filename_prefix='audio_')
                            
                            # Merge video and audio using moviepy
                            video_clip = VideoFileClip(video_path)
                            audio_clip = AudioFileClip(audio_path)
                            final_clip = video_clip.set_audio(audio_clip)
                            
                            merged_path = os.path.join(output_path, f"merged_{yt.video_id}.mp4")
                            final_clip.write_videofile(merged_path, codec='libx264', audio_codec='aac')
                            
                            # Clean up temporary files
                            os.remove(video_path)
                            os.remove(audio_path)
                            video_clip.close()
                            audio_clip.close()
                            final_clip.close()
                            
                            logger.info(f"Successfully downloaded with pytube: {merged_path}")
                            return merged_path
                    else:
                        video_path = video_stream.download(output_path, filename=f"{yt.video_id}.mp4")
                        logger.info(f"Successfully downloaded with pytube: {video_path}")
                        return video_path
                        
                except Exception as pytube_error:
                    logger.warning(f"Pytube failed: {str(pytube_error)}, trying yt-dlp...")
                    
                    # Try yt-dlp as backup
                    result = self.download_with_ytdlp(video_url, output_path)
                    if result:
                        logger.info(f"Successfully downloaded with yt-dlp: {result}")
                        return result
                    
                    # If this is not the last attempt, wait and retry
                    if attempt < max_retries - 1:
                        logger.info(f"Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All download methods failed for {video_url}")
                        return None
                        
            except Exception as e:
                logger.error(f"Unexpected error downloading {video_url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
        return None
    
    def mark_as_processed(self, video_id):
        """Mark video as processed"""
        self.processed_videos.add(video_id)
        self.save_processed_videos() 