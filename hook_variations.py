#!/usr/bin/env python3
"""
Hook Variations for Seeds Content Rewriter
Provides diverse, engaging article openings instead of repetitive "Picture this"
"""

import random

class HookGenerator:
    def __init__(self):
        self.opening_phrases = [
            "Imagine", "Consider", "Think about", "Have you ever wondered", 
            "What if", "Envision", "Picture", "Visualize", "Just imagine",
            "Close your eyes and imagine", "Have you noticed", "Did you know",
            "It's Sunday morning and", "You walk into", "The moment when",
            "There's something magical about", "Every parent dreams of",
            "When children", "As families gather", "In homes across the world"
        ]
        
        self.question_starters = [
            "What happens when", "How do you", "Why do", "When should",
            "Where can you find", "How can families", "What makes",
            "Have you ever struggled with", "Do your children", "Are you looking for",
            "Can you imagine", "What if your family", "How would it feel if",
            "What's the secret to", "Why do children", "How do you transform"
        ]
        
        self.story_starters = [
            "Last Sunday,", "In families everywhere,", "Every evening at bedtime,",
            "During car rides to church,", "At breakfast tables around the world,",
            "In Sunday school classrooms,", "When children wake up singing,",
            "After a long day,", "During family devotions,", "In quiet moments,",
            "As parents tuck their children into bed,", "When families gather for worship,"
        ]
        
        self.statistical_hooks = [
            "Research shows that", "Studies reveal that", "Child development experts confirm that",
            "According to recent findings,", "Educational research demonstrates that",
            "Brain science tells us that", "Child psychologists agree that",
            "Music educators know that", "Faith formation research shows that"
        ]
        
    def generate_hook(self, title, context="general"):
        """Generate a varied hook based on context"""
        hook_types = ["opening", "question", "story", "statistical", "direct"]
        hook_type = random.choice(hook_types)
        
        title_lower = title.lower()
        
        if hook_type == "opening":
            phrase = random.choice(self.opening_phrases)
            if "christmas" in title_lower:
                return f"{phrase} your family gathered around the tree, singing Christmas songs that teach children about Jesus' birth while creating precious memories that will last a lifetime."
            elif "worship" in title_lower:
                return f"{phrase} your children's faces lighting up during worship time, their young voices joining together in songs that hide God's Word deep in their hearts."
            elif "action" in title_lower:
                return f"{phrase} your living room transformed into a place of joyful worship as children move, dance, and sing their way into deeper faith."
            else:
                return f"{phrase} the profound impact that Scripture-based music can have on your children's spiritual development and family worship time."
                
        elif hook_type == "question":
            starter = random.choice(self.question_starters)
            if "toddler" in title_lower:
                return f"{starter} keep energetic toddlers engaged during worship while teaching them foundational biblical truths?"
            elif "preschool" in title_lower:
                return f"{starter} help preschoolers develop a genuine love for worship that grows with them into adulthood?"
            else:
                return f"{starter} create meaningful family worship experiences that children actually look forward to?"
                
        elif hook_type == "story":
            starter = random.choice(self.story_starters)
            return f"{starter} something beautiful happens. Children who might struggle to sit still during regular Bible reading suddenly become engaged participants when Scripture comes alive through music."
            
        elif hook_type == "statistical":
            starter = random.choice(self.statistical_hooks)
            if "memory" in title_lower:
                return f"{starter} children retain biblical information 60% better when it's learned through music rather than traditional memorization methods."
            elif "development" in title_lower:
                return f"{starter} musical engagement during early childhood significantly impacts both cognitive development and spiritual formation."
            else:
                return f"{starter} families who incorporate music into their worship routine report stronger spiritual connections and more meaningful devotional time."
                
        else:  # direct
            if "bible" in title_lower:
                return f"Scripture memory doesn't have to be a struggle. When biblical truth is set to music, children naturally absorb God's Word while developing a lifelong love for His truth."
            elif "praise" in title_lower:
                return f"Praise becomes authentic when it flows from hearts that truly understand God's character. The right songs can help children develop genuine worship that goes far beyond singing along."
            else:
                return f"Family worship time can become the highlight of your children's spiritual development when you choose music that engages their hearts while teaching biblical truth."

def get_varied_hooks_for_script():
    """Return code snippets to replace repetitive hooks in the main script"""
    
    generator_code = '''
# Add this to the imports section:
from hook_variations import HookGenerator

# Replace the hooks list in generate_song_page method (around line 810):
hook_generator = HookGenerator()
hook = hook_generator.generate_hook(title, "song")

# Replace collection page hooks (around lines 891-903):
hook_generator = HookGenerator()
if "christmas" in keyword.lower():
    hook = hook_generator.generate_hook(title, "christmas")
elif "easter" in keyword.lower():
    hook = hook_generator.generate_hook(title, "easter") 
elif "action" in keyword.lower():
    hook = hook_generator.generate_hook(title, "action")
else:
    hook = hook_generator.generate_hook(title, "general")
'''
    
    return generator_code

if __name__ == "__main__":
    # Test the hook generator
    generator = HookGenerator()
    
    test_titles = [
        "Christmas Songs for Kids",
        "Action Songs for Toddlers", 
        "Worship Music for Families",
        "Bible Memory Songs",
        "Preschool Praise Songs"
    ]
    
    print("Sample Hook Variations:")
    for title in test_titles:
        for i in range(3):
            hook = generator.generate_hook(title)
            print(f"{title} - Hook {i+1}: {hook}")
        print()