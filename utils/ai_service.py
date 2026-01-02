
from django.conf import settings
from core.models import QualificationScore, DraftMessage
from integrations.huggingface_client import HuggingFaceClient
import logging

logger = logging.getLogger(__name__)


def detect_job_signal(job_post):
    # Detect if a job post is a legitimate job signal using AI
    logger.info(f"Detecting job signal for: {job_post.title}")

    try:
        client = HuggingFaceClient()
        prompt = f"""You are a job signal detector. Analyze this post and determine if it's a legitimate hiring opportunity.

Job Title: {job_post.title}
Job Description: {job_post.body[:1000]}
Author: {job_post.author}

Respond in this exact format:
IS_JOB_SIGNAL: [YES/NO]
CONFIDENCE: [0-100]
REASONING: [Brief explanation of why this is or isn't a job posting]

Look for:
- Clear hiring intent or job requirements (even if budget not mentioned)
- Job descriptions, skill requirements, or project details
- Newsletter summaries of job opportunities
- Red flags: obvious spam, scams, or completely unrelated content

Be lenient - if it mentions jobs, opportunities, or hiring, it's likely a job signal."""

        response = client.query(prompt, max_tokens=250, temperature=0.5)

        is_signal = 'YES' in response.upper().split('IS_JOB_SIGNAL:')[1].split('\n')[0] if 'IS_JOB_SIGNAL:' in response else False
        confidence = 0.5
        if 'CONFIDENCE:' in response:
            try:
                conf_str = response.split('CONFIDENCE:')[1].split('\n')[0].strip()
                confidence = float(conf_str) / 100.0
            except:
                pass

        reasoning = response
        if 'REASONING:' in response:
            reasoning = response.split('REASONING:')[1].strip()

        logger.info(f"Job signal detection complete: is_signal={is_signal}, confidence={confidence:.2f}")
        return is_signal, confidence, reasoning

    except Exception as e:
        logger.error(f"Error in job signal detection: {str(e)}")
        text = f"{job_post.title} {job_post.body}".lower()
        keywords = [
            'hiring', 'looking for', 'developer', 'freelance', 'contract', 'remote',
            'python', 'django', 'job', 'opportunity', 'position', 'engineer',
            'full-time', 'part-time', 'apply', 'career', 'vacancy', 'needed',
            'software', 'programmer', 'backend', 'frontend', 'full stack'
        ]
        matches = sum(1 for kw in keywords if kw in text)

        is_signal = matches >= 1  # More lenient: just 1 keyword needed
        confidence = min(matches / 3.0, 1.0) if is_signal else 0.0
        reasoning = f"AI analysis failed. Fallback keyword detection found {matches} matches."

        return is_signal, confidence, reasoning


def qualify_job(job_post):
    # Qualify a job post using keyword-based logic
    logger.info(f"Qualifying job: {job_post.title}")

    text = f"{job_post.title} {job_post.body}".lower()

    if 'senior' in text:
        qualification = QualificationScore.objects.create(
            job_post=job_post,
            is_job_signal=True,
            confidence=0.9,
            classification='ignore',
            reasoning="Requires senior-level experience."
        )
        logger.info(f"Job qualification: IGNORE (senior-level required)")
        return qualification

    spam_indicators = [
        'mlm', 'multi-level marketing', 'pyramid scheme', 'get rich quick',
        'work from home mom', 'no experience needed earn $', 'click here now',
        'limited time offer', 'act now', 'free money'
    ]
    spam_count = sum(1 for ind in spam_indicators if ind in text)
    if spam_count >= 2:
        qualification = QualificationScore.objects.create(
            job_post=job_post,
            is_job_signal=True,
            confidence=0.85,
            classification='ignore',
            reasoning=f"Spam/scam indicators detected: {spam_count} matches."
        )
        logger.info(f"Job qualification: IGNORE (spam detected)")
        return qualification

    high_indicators = [
        'django', 'fastapi', 'postgresql', 'full-time', 'long-term',
        '$', 'budget', 'hourly', 'monthly', 'competitive salary',
        'experienced', 'professional', 'rest api', 'docker'
    ]

    medium_indicators = [
        'python', 'api', 'backend', 'automation', 'developer', 'software',
        'web', 'database', 'rest', 'contract', 'freelance', 'remote',
        'scraping', 'flask', 'mysql', 'mongodb'
    ]

    high_count = sum(1 for ind in high_indicators if ind in text)
    medium_count = sum(1 for ind in medium_indicators if ind in text)

    if high_count >= 3:
        classification = 'high'
        confidence = min(0.7 + (high_count * 0.05), 0.95)
        reasoning = f"Strong match: {high_count} high indicators, {medium_count} medium indicators. Keywords: Django/FastAPI, budget mentioned, professional opportunity."
    elif high_count >= 1 and medium_count >= 2:  # Good mix
        classification = 'high'
        confidence = 0.75
        reasoning = f"Good match: {high_count} high indicators, {medium_count} medium indicators. Python/Django opportunity with reasonable details."
    elif medium_count >= 3:  # Decent Python opportunity
        classification = 'medium'
        confidence = 0.65
        reasoning = f"Moderate match: {medium_count} medium indicators. Python-related opportunity worth reviewing."
    elif medium_count >= 1:  # Some relevance
        classification = 'medium'
        confidence = 0.55
        reasoning = f"Partial match: {medium_count} medium indicators. May be relevant."
    else:  # Low relevance but not spam
        classification = 'medium'  # Still alert, let user decide
        confidence = 0.5
        reasoning = "Limited keyword matches. Minimal details but not spam."

    qualification = QualificationScore.objects.create(
        job_post=job_post,
        is_job_signal=True,
        confidence=confidence,
        classification=classification,
        reasoning=reasoning
    )

    logger.info(f"Job qualification: {classification.upper()} (confidence: {confidence:.0%})")
    return qualification


def generate_draft_message(job_post, qualification):
    # Generate a draft response message and create a DraftMessage record
    logger.info(f"Generating draft message for: {job_post.title}")

    # Determine platform based on source type
    from core.models import Source

    if job_post.source.type == Source.GITHUB_ISSUE:
        platform = DraftMessage.GITHUB_COMMENT  # GitHub issues use comment-style messages
    elif job_post.source.type == Source.RSS_FEED:
        platform = DraftMessage.COVER_LETTER  # RSS feeds (newsletters/job boards) need formal cover letters
    else:
        platform = DraftMessage.COVER_LETTER

    try:
        client = HuggingFaceClient()
        user_profile = {
            'skills': getattr(settings, 'USER_SKILLS', 'Python, Django, web scraping, automation, REST APIs'),
            'pricing': getattr(settings, 'USER_PRICING', '$50-80/hour'),
            'availability': getattr(settings, 'USER_AVAILABILITY', 'Available for new projects'),
            'tone': getattr(settings, 'USER_TONE', 'Professional and friendly')
        }

        prompt = f"""Write a professional job application message for this opportunity.

Job Title: {job_post.title}
Job Description: {job_post.body[:800]}

Applicant Profile:
- Skills: {user_profile['skills']}
- Pricing: {user_profile['pricing']}
- Availability: {user_profile['availability']}
- Communication Style: {user_profile['tone']}

Platform: {platform.replace('_', ' ').title()}

Write a concise, engaging message (150-250 words) that:
1. Opens with genuine interest in the specific project
2. Highlights 2-3 most relevant skills for this job
3. Briefly mentions relevant experience (if skills match)
4. States availability and pricing
5. Includes a clear call to action
6. Maintains {user_profile['tone'].lower()} tone

Important:
- Don't be generic - reference specific aspects of the job
- Don't oversell or make unrealistic promises
- Keep it conversational and human
- End with an invitation to discuss further

Draft message:"""

        response = client.query(prompt, max_tokens=400, temperature=0.7)
        content = response.strip()
        cover_letter_content = ""
        if platform in [DraftMessage.COVER_LETTER, DraftMessage.DIRECT_MESSAGE]:
            cover_letter_prompt = f"""Write a formal cover letter for this job application.

Job Title: {job_post.title}
Job Description: {job_post.body[:800]}

Applicant Profile:
- Skills: {user_profile['skills']}
- Pricing: {user_profile['pricing']}
- Availability: {user_profile['availability']}

Format as a professional cover letter with:
1. Formal greeting (Dear Hiring Manager,)
2. Opening paragraph expressing interest in the specific role
3. Body paragraphs highlighting relevant qualifications and experience
4. Closing paragraph with availability and invitation to discuss
5. Professional sign-off

Length: 300-400 words
Tone: Formal and professional

Cover letter:"""

            cover_letter_response = client.query(cover_letter_prompt, max_tokens=600, temperature=0.7)
            cover_letter_content = cover_letter_response.strip()
            logger.info(f"Cover letter generated successfully (length: {len(cover_letter_content)} chars)")

        draft = DraftMessage.objects.create(
            job_post=job_post,
            content=content,
            platform=platform,
            cover_letter=cover_letter_content
        )

        logger.info(f"Draft message generated successfully (length: {len(content)} chars)")
        return draft

    except Exception as e:
        logger.error(f"Error generating draft message: {str(e)}")

        if platform == DraftMessage.GITHUB_COMMENT:
            content = f"""Hi! I'm interested in your {job_post.title[:50]} project.

I'm a Python/Django developer with experience in web scraping, automation, and REST API development. I've worked on similar projects and can deliver quality results.

I'm currently available and my rate is $50-80/hour depending on project scope.

Would love to discuss this further. Feel free to DM me or let me know a good time to chat about the details.

Thanks!"""
            cover_letter_fallback = ""
        else:
            content = f"""Subject: Re: {job_post.title[:80]}

Hello,

I came across your job posting and I'm very interested in working on this project.

I'm a Python/Django developer with strong experience in:
- Web application development
- API development and integration
- Web scraping and automation
- Database design and optimization

I'm available to start immediately and my rate is $50-80/hour. I'd be happy to discuss your project requirements in more detail and provide references from previous clients.

Looking forward to hearing from you.

Best regards"""

            cover_letter_fallback = f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_post.title} position. With extensive experience in Python and Django development, I am confident I can deliver exceptional results for your project.

My technical expertise includes:
- Full-stack web application development using Django and modern frontend frameworks
- RESTful API design, development, and integration
- Web scraping and automation solutions
- Database design, optimization, and management
- Clean, maintainable code following industry best practices

I have successfully completed numerous projects similar to yours, consistently delivering high-quality solutions that meet client requirements and exceed expectations. My approach emphasizes clear communication, attention to detail, and timely delivery.

I am available to start immediately and my rate is $50-80/hour, depending on project scope and requirements. I would welcome the opportunity to discuss your project in detail and provide references from previous clients.

Thank you for considering my application. I look forward to the possibility of working together.

Best regards"""

        draft = DraftMessage.objects.create(
            job_post=job_post,
            content=content,
            platform=platform,
            cover_letter=cover_letter_fallback
        )

        return draft
