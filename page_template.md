---
title: "{{ title }}"
description: "{{ meta_description }}"
slug: "{{ url }}"
---

# {{ h1 }}

_Keyword: {{ keyword }}_

{{ intro_paragraph }}

## 📺 Watch the Song

{% if video_embed_code %}
<div class="video-container">
  {{ video_embed_code | safe }}
</div>
{% else %}
<p>Video coming soon.</p>
{% endif %}

## 📖 Scripture

> {{ scripture_ref }}

## 🎵 Lyrics

{{ lyrics_text }}

## 💬 Devotional Thought

{{ devotional_paragraph }}

## ❓ FAQs

{% for faq in faqs %}
**{{ faq.question }}**  
{{ faq.answer }}

{% endfor %}

---

**Explore more:** [Visit our song shop](https://seedskidsworship.com/shop)

<!-- Schema Markup -->

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "MusicRecording",
  "name": "{{ h1 }}",
  "byArtist": {
    "@type": "MusicGroup",
    "name": "Seeds Kids Worship"
  },
  "isFamilyFriendly": true,
  "url": "https://seedskidsworship.com{{ url }}"
}
</script>

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {% for faq in faqs %}
    {
      "@type": "Question",
      "name": "{{ faq.question }}",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "{{ faq.answer }}"
      }
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
</script>