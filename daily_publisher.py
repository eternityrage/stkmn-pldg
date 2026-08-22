import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "gemini-fast")

    fallback_titles = [
        "When the Stickman Realizes Monday Is a Social Construct 😂",
        "The Stickman's Cooking Experiment Went Exactly as Expected 🔥",
        "POV: You and the Stickman Try to Assemble IKEA Furniture 💀",
        "The Stickman's Workout Plan vs Reality 😭",
        "When the Stickman Tries to Be Productive but Falls Asleep 💤",
        "The Stickman's Attempt at a Selfie Will Ruin Your Day 🤣",
        "Why the Stickman Never Wins an Argument With the Wall 🧱",
        "The Stickman's Morning Routine Is a Total Disaster ☕",
        "When the Stickman Forgets His Own Birthday 🎂",
        "The Stickman vs the Automatic Door: Round 47 🚪",
        "The Stickman's Dance Moves Should Be Illegal 🕺",
        "When the Stickman Tries to Parallel Park for the First Time 🅿️",
        "The Stickman's DIY Haircut Was a Bold Choice ✂️",
        "POV: The Stickman Is Your Personal IT Support 💻",
        "The Stickman's Attempt to Be Early for Once ⏰",
    ]

    fallback_descriptions = [
        "We've all been the stickman at some point — confidently doing the wrong thing and hoping nobody notices. Tag the friend who is 100% this energy. 😂 #stickman #funny #relatable #comedy #animation #stickfigure #lol #fyp #shorts #humor #memes #cartoon #funnyvideos #drawing",
        "POV: you trusted the stickman with one simple task. Somehow the building is now on fire and he's still smiling. Send this to someone who would absolutely do this. 🔥 #stickman #funny #animation #comedy #stickfigure #relatable #shorts #lol #humor #memes #cartoon #funnyvideos #fyp",
        "The stickman's plan was flawless. The execution was a catastrophe. But he learned nothing and will absolutely do it again tomorrow. Comment your favorite fail below! 💀 #stickman #funny #relatable #comedy #animation #stickfigure #lol #shorts #humor #memes #cartoon #funnyvideos #drawing",
        "This is your sign to stop letting the stickman near anything important. He means well. He really does. But the results speak for themselves. Share this with a friend who needs a laugh! ☕ #stickman #funny #morning #comedy #animation #stickfigure #relatable #shorts #lol #humor #memes #cartoon #funnyvideos",
        "The stickman tried his best and that's what matters. The wall, however, remains undefeated. Follow Stickman for daily laughs! 🧱 #stickman #funny #comedy #animation #stickfigure #relatable #shorts #lol #humor #memes #cartoon #funnyvideos #fyp",
        "Nobody told the stickman it was impossible, so he went for it anyway. Respect the confidence, fear the results. Tag someone who would 100% try this. 🚪 #stickman #funny #relatable #comedy #animation #stickfigure #lol #shorts #humor #memes #cartoon #funnyvideos #drawing",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "absurd and ridiculous — lean into the silly, over-the-top comedy",
        "relatable everyday fails — things everyone laughs at but won't admit",
        "deadpan and ironic — sound serious while being completely absurd",
        "wholesome but goofy — cute chaos that makes people smile",
        "observational and witty — point out the funny little truths of life",
        "chaotic and unpredictable — anything can happen to the stickman",
        "self-deprecating and humble — the stickman is us, failing gently",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, hilarious, and captivating title and description for a short funny STICKMAN animation video "
        f"for the social media page 'Stickman'. "
        f"The page posts funny stickman (stick-figure) animation videos — relatable fails, absurd everyday situations, "
        f"goofy chaos, and wholesome but silly moments. It's lighthearted, laugh-out-loud, and highly shareable. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be FUNNY (4-6 sentences minimum), playful, and make people laugh or smile. "
        f"Include engagement calls-to-action such as: "
        f"- Tag someone who is totally this stickman! 😂 "
        f"- Comment your favorite fail below! "
        f"- Share this with a friend who needs a laugh! "
        f"- Follow Stickman for daily laughs! "
        f"Include relevant hashtags in ALL LOWERCASE such as #stickman #funny #relatable #comedy #animation #stickfigure #lol #fyp #shorts #humor #memes #cartoon #funnyvideos #drawing. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["stickman", "funny", "animation", "comedy", "stickfigure", "relatable", "shorts", "humor", "cartoon", "lol", "memes", "funnyvideos", "drawing", "fyp"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
