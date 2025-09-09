#!/usr/bin/env python3
"""
Content Variations for Seeds Content Rewriter
Provides diverse content blocks, phrases, and templates to eliminate repetitive patterns
"""

import random
from typing import Dict, List

class ContentVariations:
    def __init__(self):
        self.scripture_phrases = [
            "hide God's Word in their hearts",
            "memorize biblical truth naturally", 
            "internalize Scripture through music",
            "store biblical wisdom in their minds",
            "embed God's promises in their memory",
            "treasure Scripture in their hearts",
            "plant biblical seeds through song",
            "weave God's truth into their lives"
        ]
        
        self.foundation_phrases = [
            "building a foundation of faith",
            "creating a biblical framework", 
            "establishing spiritual roots",
            "developing Christian character",
            "forming faith-based values",
            "cultivating spiritual growth",
            "strengthening biblical understanding",
            "deepening scriptural knowledge"
        ]
        
        self.engagement_phrases = [
            "biblically grounded and engaging for young hearts",
            "spiritually rich yet age-appropriate",
            "theologically sound and child-friendly", 
            "doctrinally solid and genuinely enjoyable",
            "biblical truth wrapped in joyful melodies",
            "Scripture-centered and developmentally appropriate",
            "faith-building content kids actually love",
            "biblical wisdom presented through engaging music"
        ]
        
        self.transformation_phrases = [
            "transform your family worship time",
            "revolutionize your home's spiritual atmosphere",
            "enhance your family's faith journey", 
            "elevate your household worship experience",
            "enrich your family's spiritual life",
            "strengthen your home's Christian foundation",
            "deepen your family's worship connection",
            "improve your household's spiritual rhythm"
        ]
        
    def get_scripture_phrase(self) -> str:
        return random.choice(self.scripture_phrases)
        
    def get_foundation_phrase(self) -> str:
        return random.choice(self.foundation_phrases)
        
    def get_engagement_phrase(self) -> str:
        return random.choice(self.engagement_phrases)
        
    def get_transformation_phrase(self) -> str:
        return random.choice(self.transformation_phrases)

class SectionVariations:
    def __init__(self):
        self.biblical_headers = [
            "The Biblical Foundation",
            "Scripture-Based Learning", 
            "Biblical Truth Through Music",
            "God's Word in Song",
            "The Spiritual Foundation",
            "Faith Formation Through Music",
            "Biblical Roots of Worship",
            "Scripture and Song Together"
        ]
        
        self.usage_headers = [
            "How to Use These Songs in Family Worship",
            "Practical Applications for Your Family",
            "Bringing These Songs Into Your Home",
            "Real-World Implementation Ideas", 
            "Making These Songs Part of Family Life",
            "Integration Strategies for Families",
            "Practical Ways to Use This Music",
            "Family-Centered Application Ideas"
        ]
        
        self.power_headers = [
            "The Power of Scripture Songs",
            "Why Music-Based Scripture Works",
            "The Impact of Biblical Music",
            "Scripture Learning Through Song",
            "Music's Role in Faith Formation", 
            "The Science of Musical Scripture",
            "Biblical Music's Unique Benefits",
            "How Songs Strengthen Faith"
        ]
        
        self.cta_headers = [
            "Transform Your Family's Worship Time",
            "Start Your Musical Scripture Journey",
            "Begin Building Musical Memories Today",
            "Create Meaningful Family Worship",
            "Establish Your Family's Musical Foundation",
            "Launch Your Home's Worship Revolution",
            "Build Lasting Faith Through Song",
            "Start Your Scripture Song Adventure"
        ]
    
    def get_biblical_header(self) -> str:
        return random.choice(self.biblical_headers)
        
    def get_usage_header(self) -> str:
        return random.choice(self.usage_headers)
        
    def get_power_header(self) -> str:
        return random.choice(self.power_headers)
        
    def get_cta_header(self) -> str:
        return random.choice(self.cta_headers)

class ContentBlocks:
    def __init__(self):
        self.content_variations = ContentVariations()
        
    def get_foundation_intro(self, title: str, scripture: str, description: str) -> str:
        """Generate varied foundation introduction"""
        intros = [
            f"{description} This Scripture-focused song brings {scripture} to life through music, helping families sing God's Word together in a way that's both joyful and deeply rooted in biblical truth.",
            f"{description} Through the power of music, this biblical song transforms {scripture} into an unforgettable family worship experience that combines joy with solid scriptural teaching.",
            f"{description} By setting {scripture} to music, this song creates opportunities for families to engage with God's Word in fresh, meaningful ways that resonate across all age groups.",
            f"{description} This musical adaptation of {scripture} provides families with a powerful tool for worship that combines the memorability of music with the authority of Scripture.",
            f"{description} Drawing from {scripture}, this song offers families a unique way to experience biblical truth through the universal language of music and worship."
        ]
        return random.choice(intros)
    
    def get_learning_block(self, title: str) -> str:
        """Generate varied learning explanation blocks"""
        scripture_phrase = self.content_variations.get_scripture_phrase()
        foundation_phrase = self.content_variations.get_foundation_phrase()
        
        blocks = [
            f"When children sing Scripture-based songs like \"{title},\" they're not just learning melodies—they're {foundation_phrase} that will serve them throughout their lives. Each repetition helps {scripture_phrase} through worship.",
            f"Songs like \"{title}\" do more than entertain children—they actively contribute to {foundation_phrase} through repeated exposure to biblical truth. This natural learning process helps {scripture_phrase} effortlessly.",
            f"The beauty of \"{title}\" lies in its dual purpose: entertainment and education. While children enjoy the melody, they're simultaneously {foundation_phrase} and learning to {scripture_phrase} through joyful repetition.",
            f"\"{title}\" serves as both worship and instruction, creating opportunities for {foundation_phrase} while helping children {scripture_phrase} in a natural, pressure-free environment.",
            f"Through songs like \"{title},\" children experience {foundation_phrase} without feeling like they're in a formal learning situation. The music naturally helps them {scripture_phrase} through repeated, joyful engagement."
        ]
        return random.choice(blocks)
    
    def get_cta_block(self, title: str, context: str = "song") -> str:
        """Generate varied call-to-action blocks"""
        scripture_phrase = self.content_variations.get_scripture_phrase()
        transformation_phrase = self.content_variations.get_transformation_phrase()
        engagement_phrase = self.content_variations.get_engagement_phrase()
        
        if context == "song":
            ctas = [
                f"Ready to {scripture_phrase} through \"{title}\"? This Scripture-based song provides the perfect foundation for family worship that's {engagement_phrase}.",
                f"Experience how \"{title}\" can {transformation_phrase} while helping children {scripture_phrase} through meaningful musical worship.",
                f"Let \"{title}\" become part of your family's spiritual journey—a tool that helps children {scripture_phrase} while creating {engagement_phrase} worship experiences.",
                f"Discover the impact \"{title}\" can have on your family's faith formation as it helps children {scripture_phrase} through {engagement_phrase} musical worship.",
                f"Transform family devotions with \"{title}\"—a powerful resource that helps children {scripture_phrase} while providing {engagement_phrase} worship opportunities."
            ]
        else:
            ctas = [
                f"Ready to {scripture_phrase} through joy-filled worship? These Scripture-based songs provide the perfect foundation for family worship that's {engagement_phrase}.",
                f"Experience how these songs can {transformation_phrase} while helping children {scripture_phrase} through meaningful musical experiences.",
                f"Let these biblical songs become part of your family's spiritual rhythm—tools that help children {scripture_phrase} while creating {engagement_phrase} worship moments.",
                f"Discover the lasting impact these songs can have as they help children {scripture_phrase} through {engagement_phrase} family worship experiences.",
                f"Transform your approach to family faith formation with songs that help children {scripture_phrase} while providing {engagement_phrase} learning opportunities."
            ]
        return random.choice(ctas)
    
    def get_meta_description(self, title: str, context: str) -> str:
        """Generate varied meta descriptions"""
        templates = [
            f"Transform your family's faith journey with {title.lower()} that combine biblical truth with engaging melodies. Expert insights on child development, Scripture memorization, and meaningful worship experiences that build lasting spiritual foundations.",
            f"Discover proven strategies for using {title.lower()} to strengthen children's faith formation. Research-backed insights on music-based learning, family worship, and creating spiritual memories that last a lifetime.",
            f"Unlock the power of {title.lower()} for authentic family discipleship. Professional guidance on age-appropriate Scripture learning, worship integration, and building biblical foundations through music your children will love.",
            f"Master the art of faith formation with {title.lower()} designed for real families. Expert advice on Scripture memorization, worship planning, and creating meaningful spiritual experiences that engage children naturally.",
            f"Elevate your family's spiritual life with {title.lower()} that actually work. Proven techniques for biblical education, worship enhancement, and faith-building activities that turn learning into joyful discovery."
        ]
        return random.choice(templates)

def get_replacement_patterns():
    """Return patterns to find and replace repetitive content"""
    return {
        "hide God's Word in their hearts": "content_variations.get_scripture_phrase()",
        "building a foundation of faith": "content_variations.get_foundation_phrase()",
        "biblically grounded and engaging for young hearts": "content_variations.get_engagement_phrase()",
        "transform your family worship time": "content_variations.get_transformation_phrase()"
    }

if __name__ == "__main__":
    # Test content variations
    content = ContentBlocks()
    
    print("Sample Foundation Intros:")
    for i in range(3):
        intro = content.get_foundation_intro("Amazing Grace for Kids", "Ephesians 2:8", "This beloved hymn teaches children about God's amazing grace.")
        print(f"{i+1}. {intro}\n")
    
    print("Sample Learning Blocks:")
    for i in range(3):
        block = content.get_learning_block("Jesus Loves Me")
        print(f"{i+1}. {block}\n")
    
    print("Sample CTAs:")
    for i in range(3):
        cta = content.get_cta_block("Scripture Songs for Kids", "collection")
        print(f"{i+1}. {cta}\n")