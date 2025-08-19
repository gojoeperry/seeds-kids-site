# Seeds Kids Worship Style Guide Application

This guide explains how to use the `style_guide_rewriter.py` script to apply the Seeds Kids Worship style guide to your markdown content files.

## Quick Start

### Apply style guide to all content files:
```bash
python style_guide_rewriter.py content
```

### Preview changes without modifying files (dry-run):
```bash
python style_guide_rewriter.py content --dry-run
```

### Apply to specific sections:
```bash
# Activities only
python style_guide_rewriter.py content --pattern "activities/**/*.md"

# Songs only  
python style_guide_rewriter.py content --pattern "songs/**/*.md"

# Single file
python style_guide_rewriter.py content --pattern "activities/40-popular-sunday-school-songs/*.md"
```

### Generate a detailed report:
```bash
python style_guide_rewriter.py content --report style_guide_report.txt
```

## What the Script Does

The style guide rewriter automatically applies Seeds Kids Worship editorial standards:

### 1. **Warm, Engaging Hooks**
- Adds faith-centered opening lines like:
  - "Let's explore how your family can sing God's Word together."
  - "Picture this: your children singing Scripture with joy and understanding."

### 2. **Scripture Integration**
- Adds relevant Bible verses when missing
- Uses verses like Psalm 96:1, Psalm 150:6, Colossians 3:16

### 3. **Biblical Language Enhancement**
- Replaces generic terms with faith-centered language:
  - "music for kids" → "Scripture music for children"
  - "educational music" → "faith-building music"
  - "fun songs" → "joy-filled songs"

### 4. **Call-to-Action Addition**
- Adds compelling CTAs focused on Scripture and worship:
  - "Ready to hide God's Word in your children's hearts? Listen now!"
  - "Transform your family worship time with Scripture songs that stick!"

### 5. **Tone Improvement**
- Replaces cold, marketing language with warm, encouraging words
- Changes "provides" to "offers families", "just" to "joyfully", etc.

## Style Guide Standards

### Voice & Tone
- **Tone**: Warm, encouraging, faith-filled, parent-friendly
- **Voice**: Conversational but biblically grounded

### Required Elements
- **Hook**: Engaging opening that draws families in
- **Scripture**: Biblical foundation for the content
- **Application**: Practical ways to use the content
- **Call-to-action**: Clear next steps for families

### Key Phrases to Use
- "Sing God's Word"
- "Hide His Word in their hearts"
- "Rooted in Scripture"
- "Faith-filled worship"
- "Gospel-centered"

### Content Length
- Target: 300-800 words
- Focuses on quality over quantity

## Command Line Options

| Option | Description |
|--------|-------------|
| `content_dir` | Directory containing markdown files (default: "content") |
| `--dry-run` | Preview changes without modifying files |
| `--pattern` | File pattern to match (default: "\*\*/\*.md") |
| `--report` | Save detailed report to file |

## Examples

### Before Style Guide Application:
```markdown
# Sunday School Songs

These songs are fun and educational for kids. They provide entertainment and learning opportunities.
```

### After Style Guide Application:
```markdown
# Sunday School Songs

Let's explore how your family can sing God's Word together.

These Scripture songs are joy-filled and faith-building for children. They offer families worship and biblical learning opportunities rooted in Scripture.

### Scripture
"Sing to the Lord a new song; sing to the Lord, all the earth." - Psalm 96:1

Ready to hide God's Word in your children's hearts? Listen now and let these Scripture songs transform your family worship time!
```

## Requirements

Install required dependencies:
```bash
pip install python-frontmatter
```

## Troubleshooting

### YAML Frontmatter Issues
If you encounter YAML parsing errors, check that your frontmatter is properly formatted:

```yaml
---
title: "Your Title"
description: "Your description"
categories:
- "activities"
tags:
- "kids"
- "songs"
---
```

### Encoding Issues
The script uses UTF-8 encoding. If you encounter encoding issues on Windows, ensure your files are saved with UTF-8 encoding.

### File Backup
The script modifies files in place. Use `--dry-run` first to preview changes, or ensure your files are backed up with git.