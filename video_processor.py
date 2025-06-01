import os
import time
import json
import logging
import whisper
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import openai

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, config):
        """Initialize video processor with configuration"""
        self.config = config
        self.whisper_model = whisper.load_model("base")
    
    def extract_audio_and_transcribe(self, video_path):
        """Extract audio from video and generate transcription with timestamps"""
        try:
            # Load video and extract audio
            video = VideoFileClip(video_path)
            audio_path = video_path.replace('.mp4', '.wav')
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            video.close()
            
            # Transcribe audio with timestamps
            result = self.whisper_model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False,
                fp16=False  # Force FP32 to avoid warnings
            )
            
            # Clean up audio file
            os.remove(audio_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing {video_path}: {str(e)}")
            return None
    
    def find_interesting_segments(self, transcription, video_duration):
        """Use AI to find interesting segments for short-form content"""
        try:
            # Prepare text for analysis
            full_text = transcription['text']
            segments = transcription['segments']
            
            # Use OpenAI to identify interesting moments
            openai.api_key = self.config['openai_api_key']
            
            prompt = f"""
            Analyze this video transcript and identify the most engaging segments for TikTok short-form content (60 seconds each).
            Look for:
            - Controversial or surprising statements
            - Valuable tips or insights
            - Emotional moments
            - Clear explanations of complex topics
            - Hooks that grab attention
            
            Transcript: {full_text[:4000]}...
            
            Return a JSON list of segments with start_time, end_time, reason, and suggested_title.
            Limit to maximum 5 segments.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            ai_segments = json.loads(response.choices[0].message.content)
            
            # Validate and adjust segments based on actual timestamps
            validated_segments = []
            for segment in ai_segments:
                start_time = max(0, segment['start_time'])
                end_time = min(video_duration, segment['end_time'])
                
                if end_time - start_time >= 30:  # Minimum 30 seconds
                    validated_segments.append({
                        'start_time': start_time,
                        'end_time': min(start_time + self.config['clip_duration'], end_time),
                        'reason': segment['reason'],
                        'title': segment['suggested_title']
                    })
            
            return validated_segments[:self.config['max_clips_per_video']]
            
        except Exception as e:
            logger.error(f"Error finding segments: {str(e)}")
            # Fallback: create segments every 2 minutes
            segments = []
            duration = self.config['clip_duration']
            for i in range(0, int(video_duration), 120):  # Every 2 minutes
                if len(segments) >= self.config['max_clips_per_video']:
                    break
                segments.append({
                    'start_time': i,
                    'end_time': min(i + duration, video_duration),
                    'reason': 'Auto-generated segment',
                    'title': f'Clip {len(segments) + 1}'
                })
            return segments
    
    def create_vertical_video_with_captions(self, video_path, segment, transcription, output_path):
        """Create vertical 9:16 video with captions"""
        try:
            # Load video
            video = VideoFileClip(video_path).subclip(segment['start_time'], segment['end_time'])
            
            # Resize to vertical format (9:16)
            target_width = 1080
            target_height = 1920
            
            # Calculate crop/resize parameters
            video_aspect = video.w / video.h
            target_aspect = target_width / target_height
            
            if video_aspect > target_aspect:
                # Video is wider, crop width
                new_width = int(video.h * target_aspect)
                video = video.crop(x_center=video.w/2, width=new_width)
            else:
                # Video is taller, crop height
                new_height = int(video.w / target_aspect)
                video = video.crop(y_center=video.h/2, height=new_height)
            
            # Resize to target resolution
            video = video.resize((target_width, target_height))
            
            # Extract relevant transcription segments
            caption_clips = []
            for trans_segment in transcription['segments']:
                seg_start = trans_segment['start']
                seg_end = trans_segment['end']
                
                # Check if this transcription segment overlaps with our video segment
                if seg_start < segment['end_time'] and seg_end > segment['start_time']:
                    # Adjust timing relative to the clip
                    clip_start = max(0, seg_start - segment['start_time'])
                    clip_end = min(segment['end_time'] - segment['start_time'], seg_end - segment['start_time'])
                    
                    if clip_end > clip_start:
                        # Create caption
                        caption_text = trans_segment['text'].strip()
                        
                        caption = TextClip(
                            caption_text,
                            fontsize=60,
                            color='white',
                            stroke_color='black',
                            stroke_width=3,
                            font='Arial-Bold',
                            method='caption',
                            size=(target_width - 100, None)
                        ).set_position(('center', 'bottom')).set_start(clip_start).set_end(clip_end)
                        
                        caption_clips.append(caption)
            
            # Composite video with captions
            if caption_clips:
                final_video = CompositeVideoClip([video] + caption_clips)
            else:
                final_video = video
            
            # Write final video
            output_filename = f"{segment['title'].replace(' ', '_')[:50]}_{int(time.time())}.mp4"
            final_output_path = os.path.join(output_path, output_filename)
            
            final_video.write_videofile(
                final_output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                fps=30
            )
            
            # Clean up
            video.close()
            final_video.close()
            for clip in caption_clips:
                clip.close()
            
            return final_output_path
            
        except Exception as e:
            logger.error(f"Error creating vertical video: {str(e)}")
            return None
    
    def generate_tiktok_metadata(self, video_info, segment):
        """Generate title, description and hashtags for TikTok"""
        try:
            openai.api_key = self.config['openai_api_key']
            
            prompt = f"""
            Create engaging TikTok metadata for this video clip:
            
            Original Video Title: {video_info['title']}
            Channel: {video_info['channel']}
            Segment: {segment['title']}
            Reason: {segment['reason']}
            
            Generate:
            1. Catchy TikTok title (max 100 characters)
            2. Engaging description (max 300 characters)
            3. Relevant hashtags (include #timothyronald #akademicrypto and others related to crypto/finance)
            
            Return as JSON with keys: title, description, hashtags
            Make it engaging for Indonesian crypto/finance audience.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            
            metadata = json.loads(response.choices[0].message.content)
            
            # Ensure required hashtags are included
            required_hashtags = ['#timothyronald', '#akademicrypto']
            hashtags = metadata.get('hashtags', [])
            
            for req_tag in required_hashtags:
                if req_tag not in hashtags:
                    hashtags.append(req_tag)
            
            metadata['hashtags'] = hashtags
            return metadata
            
        except Exception as e:
            logger.error(f"Error generating metadata: {str(e)}")
            return {
                'title': segment['title'],
                'description': f"Clip dari {video_info['channel']} - {segment['reason']}",
                'hashtags': ['#timothyronald', '#akademicrypto', '#crypto', '#finance', '#indonesia']
            } 