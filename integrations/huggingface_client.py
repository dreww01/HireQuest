from huggingface_hub import InferenceClient
from django.conf import settings
import logging
from utils.validators import validate_huggingface_credentials
from utils.exceptions import MissingAPIKeyError, InvalidAPIKeyError, APIConnectionError

logger = logging.getLogger(__name__)


class HuggingFaceClient:
    # Hugging Face API client for AI-powered job analysis

    def __init__(self):
        logger.info("Initializing Hugging Face client")

        try:
            validate_huggingface_credentials(
                api_key=settings.HUGGINGFACE_API_KEY
            )
        except MissingAPIKeyError:
            logger.error("Hugging Face client initialization failed: missing API key")
            raise

        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model = settings.HUGGINGFACE_MODEL

        try:
            self.client = InferenceClient(token=self.api_key)
            logger.info(f"Hugging Face client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"Error initializing Hugging Face client: {str(e)}")
            raise APIConnectionError('Hugging Face', e)

    def query(self, prompt, max_tokens=500, temperature=0.7):
        # Query the Hugging Face model
        logger.info(f"Querying Hugging Face model with prompt length: {len(prompt)}")

        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature
            )

            generated_text = response.choices[0].message.content

            logger.info(f"Successfully received response from Hugging Face (length: {len(generated_text)})")
            return generated_text

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error querying Hugging Face: {error_msg}")

            if '401' in error_msg or 'unauthorized' in error_msg.lower():
                raise InvalidAPIKeyError(
                    'Hugging Face',
                    'API key is invalid or expired. Please verify HUGGINGFACE_API_KEY in your .env file.'
                )

            if '404' in error_msg or 'not found' in error_msg.lower():
                raise APIConnectionError(
                    'Hugging Face',
                    f'Model {self.model} not found. Please verify HUGGINGFACE_MODEL in settings.'
                )

            raise APIConnectionError('Hugging Face', e)

    def test_connection(self):
        # Test the API connection
        logger.info("Testing Hugging Face API connection")
        test_prompt = "Hello, respond with: Connection successful"

        try:
            response = self.query(test_prompt, max_tokens=50)
            logger.info("Hugging Face API connection test successful")
            return True
        except Exception as e:
            logger.error(f"Hugging Face API connection test failed: {str(e)}")
            raise

    def analyze_job_relevance(self, job_post):
        # Analyze if a job post is relevant for the user
        logger.info(f"Analyzing job relevance for: {job_post.title}")

        prompt = f"""Analyze this job posting and determine if it's relevant for a Python/Django developer with skills in web scraping and automation.

Job Title: {job_post.title}
Job Description: {job_post.body[:1000]}

Respond in this exact format:
RELEVANT: [YES/NO]
CONFIDENCE: [0-100]
REASON: [Brief explanation]"""

        try:
            response = self.query(prompt, max_tokens=200, temperature=0.3)

            is_relevant = 'YES' in response.upper()
            confidence = 0.5

            if 'CONFIDENCE:' in response:
                try:
                    conf_str = response.split('CONFIDENCE:')[1].split('\n')[0].strip()
                    confidence = float(conf_str) / 100.0
                except:
                    pass

            return {
                'is_relevant': is_relevant,
                'confidence': confidence,
                'reasoning': response
            }

        except Exception as e:
            logger.error(f"Error analyzing job relevance: {str(e)}")
            return {
                'is_relevant': False,
                'confidence': 0.0,
                'reasoning': f'AI analysis failed: {str(e)}'
            }

    def generate_draft_message(self, job_post, user_profile):
        # Generate a draft message to respond to a job posting
        logger.info(f"Generating draft message for: {job_post.title}")

        prompt = f"""Write a professional job application message for this job posting.

Job Title: {job_post.title}
Job Description: {job_post.body[:800]}

Applicant Profile:
- Skills: {user_profile.get('skills', 'Python, Django, web scraping')}
- Pricing: {user_profile.get('pricing', '$50-100/hour')}
- Availability: {user_profile.get('availability', 'Available immediately')}
- Tone: {user_profile.get('tone', 'Professional but friendly')}

Write a concise, engaging message (150-200 words) that:
1. Shows genuine interest in the project
2. Highlights relevant skills
3. Mentions availability and pricing
4. Includes a call to action

Draft message:"""

        try:
            response = self.query(prompt, max_tokens=300, temperature=0.7)
            logger.info("Successfully generated draft message")
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating draft message: {str(e)}")
            # Return a simple template as fallback
            return f"""Hi,

I'm interested in your {job_post.title} project. I have experience in {user_profile.get('skills', 'Python, Django, and web scraping')}.

I'm {user_profile.get('availability', 'available immediately')} and my rate is {user_profile.get('pricing', '$50-100/hour')}.

Would love to discuss this further!

Best regards"""
