# SerpAPI Keyword Expander Setup Guide

## 🚀 Quick Start

### 1. Get SerpAPI Key
1. Visit https://serpapi.com/
2. Sign up for a free account (100 searches/month)
3. Get your API key from the dashboard

### 2. Set Environment Variable
**Windows Command Prompt:**
```cmd
set SERPAPI_API_KEY=your_actual_api_key_here
```

**Windows PowerShell:**
```powershell
$env:SERPAPI_API_KEY="your_actual_api_key_here"
```

**Permanent (Windows):**
1. Open System Properties → Advanced → Environment Variables
2. Add new variable: `SERPAPI_API_KEY` = `your_key`

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Run the Expander
```cmd
python serpapi_expander_simple.py
```

## 📁 What Gets Generated

### Input Files Required:
- ✅ `seed_keywords.txt` - 30 base keywords (already created)

### Output Files Created:
- 📄 `all_keywords_raw.json` - Complete raw data with all metadata
- 📊 `keyword_clusters.csv` - Organized keywords with clusters and URLs
- 🌐 `url_metadata.json` - Ready for content generation

## 🔍 What the Script Does

### SerpAPI Data Sources:
1. **Google Autocomplete** - Instant search suggestions
2. **People Also Ask** - Related questions with snippets
3. **Related Searches** - Bottom-of-page related queries
4. **Manual Variations** - Proven SEO expansion patterns

### Keyword Expansion Types:
- **By Age Group:** for toddlers, for preschoolers, for kids
- **By Format:** youtube, videos, cd, app, playlist
- **By Context:** for church, for sunday school, for home
- **By Action:** with motions, with actions, interactive
- **By Theme:** christmas, easter, praise, worship
- **By Quality:** easy, simple, fun, peaceful

### Semantic Clustering:
- `christmas` - Christmas/nativity content
- `easter` - Easter/resurrection content  
- `scripture_memory` - Bible memorization
- `worship` - Worship and praise music
- `sunday_school` - Sunday school activities
- `vbs` - Vacation Bible School
- `preschool` - Preschool-specific content
- `toddler` - Toddler-specific content
- `choir` - Children's choir music
- `lullabies` - Bedtime/quiet music
- `apps` - Mobile applications
- `general` - Other keywords

## 📊 Expected Output
- **300+ unique keywords** from 30 seeds
- **Complete SEO metadata** for each keyword
- **Organized clusters** for content planning
- **Ready-to-use URLs** for page generation

## 🔧 Troubleshooting

### API Key Issues:
```
Configuration error: SERPAPI_API_KEY environment variable not found
```
**Solution:** Set the environment variable correctly

### Rate Limiting:
```
Error: Too many requests
```
**Solution:** Script includes automatic 1-3 second delays

### Network Issues:
```
Error: Connection timeout
```
**Solution:** Check internet connection, script has 10s timeout

## 💡 Pro Tips

1. **Free Tier Limits:** 100 searches/month on free plan
2. **Rate Limiting:** Script includes delays to avoid limits
3. **Keyword Quality:** Filters out very short/long keywords
4. **Deduplication:** Removes duplicate keywords automatically
5. **SEO Ready:** All URLs are slug-safe and SEO-optimized

## 🎯 Next Steps After Generation

1. **Review Keywords:** Check `keyword_clusters.csv`
2. **Generate Content:** Use `url_metadata.json` with Claude
3. **Create Pages:** Run `python generate_pages.py`
4. **Build Site:** Use Hugo or your preferred generator

## 📞 Support

If you encounter issues:
1. Check the API key is set correctly
2. Ensure `seed_keywords.txt` exists
3. Verify internet connection
4. Check SerpAPI dashboard for quota

---

**Ready to generate 300+ keywords with real search data? Run the script now!**