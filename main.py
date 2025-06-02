import os
import time
import logging
import schedule
from moviepy.editor import VideoFileClip
from moviepy.config import change_settings

from config import Config
from video_downloader import VideoDownloader
from video_processor import VideoProcessor
from tiktok_uploader import TikTokUploader

change_settings({"IMAGEMAGICK_BINARY": r"D:\\program files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YouTubeToTikTokAutomation:
    def __init__(self, config_file='config.json'):
        """Initialize the automation system"""
        self.config = Config(config_file)
        self.downloader = VideoDownloader(self.config)
        self.processor = VideoProcessor(self.config)
        self.uploader = TikTokUploader(self.config)
        
    def process_video(self, video_info):
        """Process a single video through the entire pipeline"""
        try:
            logger.info(f"Processing video: {video_info['title']}")
            
            # Create directories
            os.makedirs(self.config['download_path'], exist_ok=True)
            os.makedirs(self.config['output_path'], exist_ok=True)
            
            # Step 1: Download video
            video_path = self.downloader.download_video(video_info['url'], self.config['download_path'])
            if not video_path:
                logger.error(f"Failed to download video: {video_info['title']}")
                # Mark as processed to avoid retrying failed downloads
                self.downloader.mark_as_processed(video_info['video_id'])
                return False
            
            # Step 2: Transcribe video
            transcription = self.processor.extract_audio_and_transcribe(video_path)
            if not transcription:
                logger.error(f"Failed to transcribe video: {video_info['title']}")
                # Clean up downloaded file
                if os.path.exists(video_path):
                    os.remove(video_path)
                return False
            
            # Step 3: Find interesting segments
            video_clip = VideoFileClip(video_path)
            video_duration = video_clip.duration
            video_clip.close()
            
            segments = self.processor.find_interesting_segments(transcription, video_duration)
            
            if not segments:
                logger.warning(f"No interesting segments found for video: {video_info['title']}")
                # Clean up downloaded file
                if os.path.exists(video_path):
                    os.remove(video_path)
                # Mark as processed
                self.downloader.mark_as_processed(video_info['video_id'])
                return False
            
            # Step 4: Create short-form videos
            successful_uploads = 0
            for i, segment in enumerate(segments):
                try:
                    logger.info(f"Creating clip {i+1}/{len(segments)}: {segment['title']}")
                    
                    # Create vertical video with captions
                    clip_path = self.processor.create_vertical_video_with_captions(
                        video_path, segment, transcription, self.config['output_path']
                    )
                    
                    if clip_path:
                        # Generate metadata
                        metadata = self.processor.generate_tiktok_metadata(video_info, segment)
                        
                        # Upload to TikTok
                        if self.uploader.upload_to_tiktok(clip_path, metadata):
                            successful_uploads += 1
                            logger.info(f"Successfully processed clip: {segment['title']}")
                        else:
                            logger.warning(f"Failed to upload clip: {segment['title']}")
                        
                        # Clean up clip file
                        if os.path.exists(clip_path):
                            os.remove(clip_path)
                        
                        time.sleep(2)  # Brief pause between uploads
                    else:
                        logger.warning(f"Failed to create clip: {segment['title']}")
                        
                except Exception as clip_error:
                    logger.error(f"Error processing clip {i+1}: {str(clip_error)}")
                    continue
            
            # Clean up original video file
            if os.path.exists(video_path):
                os.remove(video_path)
            
            # Mark video as processed
            self.downloader.mark_as_processed(video_info['video_id'])
            
            logger.info(f"Completed processing {video_info['title']} - {successful_uploads}/{len(segments)} clips uploaded")
            return successful_uploads > 0
            
        except Exception as e:
            logger.error(f"Error processing video {video_info['title']}: {str(e)}")
            # Clean up any remaining files
            try:
                if 'video_path' in locals() and os.path.exists(video_path):
                    os.remove(video_path)
            except:
                pass
            return False
    
    def run_automation_cycle(self):
        """Run one cycle of the automation"""
        logger.info("Starting automation cycle...")
        
        try:
            # Check for new videos
            new_videos = self.downloader.check_new_videos()
            
            if not new_videos:
                logger.info("No new videos found")
                return
            
            logger.info(f"Found {len(new_videos)} new videos")
            
            # Process each new video
            for video in new_videos:
                try:
                    self.process_video(video)
                    # Add delay between videos to avoid rate limiting
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"Error processing video {video.get('title', 'unknown')}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in automation cycle: {str(e)}")
    
    def start_monitoring(self):
        """Start the monitoring system"""
        logger.info("Starting YouTube to TikTok automation system...")
        
        # Schedule the automation to run every hour
        schedule.every().hour.do(self.run_automation_cycle)
        
        # Run once immediately
        self.run_automation_cycle()
        
        # Keep the system running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Automation stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)

def main():
    """Main function to start the automation"""
    try:
        # Create automation instance
        automation = YouTubeToTikTokAutomation()
        
        # Start monitoring
        automation.start_monitoring()
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")

if __name__ == "__main__":
    main() 